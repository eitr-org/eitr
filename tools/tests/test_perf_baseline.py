import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

SPEC = importlib.util.spec_from_file_location('perf_baseline', Path(__file__).resolve().parents[1] / 'perf-baseline.py')
perf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(perf)


class PerfBaselineTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.proc = Path(temporary.name)
        (self.proc / 'stat').write_text('cpu  100 0 20 200 10 2 3 0 0 0\nctxt 400\nprocesses 800\n')
        (self.proc / 'meminfo').write_text('MemTotal: 1000 kB\nMemAvailable: 400 kB\n')

    def fixture(self, pid=10, start=100, cpu=30, switches=4):
        directory = self.proc / str(pid)
        directory.mkdir(exist_ok=True)
        values = ['0'] * 22
        values[0], values[1] = 'S', '2'
        values[11], values[12], values[19] = str(cpu), '10', str(start)
        (directory / 'stat').write_text(f'{pid} (odd ) name) ' + ' '.join(values))
        (directory / 'cmdline').write_text('quickshell\0-p\0/usr/share/eitr/quickshell/desktop-bar\0')
        (directory / 'status').write_text(f'voluntary_ctxt_switches: {switches}\nnonvoluntary_ctxt_switches: 2\n')
        (directory / 'smaps_rollup').write_text('Rss: 200 kB\nPss: 120 kB\n')
        return directory

    def sample(self, timestamp):
        sample = perf.snapshot(self.proc)
        sample.update(time=timestamp, uptime=timestamp)
        return sample

    def test_cpuinfo_keys_padded_with_tabs(self):
        self.assertEqual(perf.fields('model name\t: Example CPU\nflags\t\t: fpu\n')['model name'], 'Example CPU')

    def test_stat_comm_parentheses_and_memory(self):
        item = perf.process(self.fixture(), 100)
        self.assertEqual((item['cpu_seconds'], item['ppid'], item['start_ticks']), (.4, 2, 100))
        self.assertEqual((item['pss_kib'], item['rss_kib'], item['group']), (120, 200, 'bar'))

    def test_delta_and_pid_reuse(self):
        self.fixture()
        before = self.sample(10)
        self.fixture(cpu=50, switches=9)
        after = self.sample(11)
        result = perf.summarize([before, after])
        ticks = perf.os.sysconf('SC_CLK_TCK')
        self.assertAlmostEqual(result['groups']['bar']['cpu_seconds'], 20 / ticks)
        self.assertEqual(result['groups']['bar']['voluntary'], 5)
        self.assertEqual(result['observed_process_launch_count'], 0)
        self.fixture(start=1050, cpu=2)
        reused = self.sample(12)
        result = perf.summarize([before, reused])
        self.assertEqual(result['observed_process_launch_count'], 1)
        self.assertEqual(result['observed_process_launches'][0]['ppid'], 2)

    def test_missing_memory_and_disappearing_process(self):
        directory = self.fixture()
        (directory / 'smaps_rollup').unlink()
        item = perf.process(directory, 100)
        self.assertIsNone(item['pss_kib'])
        (self.proc / '11').mkdir()
        self.assertEqual(len(self.sample(10)['processes']), 1)
        result = perf.summarize([self.sample(10), self.sample(11)])
        self.assertIsNone(result['groups']['bar']['pss_kib_mean'])

    def test_groups_exclude_other_quickshell(self):
        self.assertIsNone(perf.group_for('quickshell', ['quickshell', '-p', 'lockscreen']))
        self.assertEqual(perf.group_for('python3', ['python3', '/code/bar-data.py']), 'broker')
        self.assertEqual(perf.group_for('Hyprland', []), 'Hyprland')

    def test_system_cpu_excludes_guest_double_count(self):
        result = self.sample(1)
        ticks = perf.os.sysconf('SC_CLK_TCK')
        self.assertEqual(result['system']['cpu_seconds'], 335 / ticks)
        self.assertEqual(result['system']['busy_cpu_seconds'], 125 / ticks)
        self.assertEqual(result['system']['ram_used_kib'], 600)

    def test_private_output_and_repository_rejection(self):
        with self.assertRaises(ValueError):
            perf.save({}, perf.ROOT / 'results')
        result = perf.save({'schema_version': 1}, self.proc / 'results')
        self.assertEqual(result.stat().st_mode & 0o777, 0o600)

    def test_optional_gpu_numbers(self):
        self.assertIsNone(perf.number('[N/A]'))
        self.assertIsNone(perf.number('nan'))
        self.assertEqual(perf.number(' 25.5 '), 25.5)

    def test_compare(self):
        self.fixture()
        result = {'metrics': perf.summarize([self.sample(1), self.sample(2)]), 'context': {}, 'configuration': {}}
        with contextlib.redirect_stdout(io.StringIO()) as output:
            perf.compare(result, result)
        self.assertIn('bar.pss_kib_mean', output.getvalue())
        self.assertIn('+0.000', output.getvalue())

    def fake_collection(self, scenario, assume_playing=False):
        clock = [0.0]
        original_snapshot = perf.snapshot
        def sleep(seconds):
            clock[0] += seconds
        def sample():
            result = original_snapshot(self.proc)
            result.update(time=clock[0], uptime=clock[0])
            return result
        args = SimpleNamespace(scenario=scenario, settle=0, duration=7,
                               interval=1, panel_seconds=1, assume_playing=assume_playing)
        with patch.object(perf.time, 'sleep', side_effect=sleep), \
                patch.object(perf.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(perf, 'snapshot', side_effect=sample), \
                patch.object(perf, 'gpu_samples', return_value=[]), \
                patch.object(perf, 'ipc') as ipc, patch('builtins.input') as prompt:
            result = perf.collect(args)
        return result, ipc, prompt

    def test_panel_sequence_only_presents_and_closes(self):
        result, ipc, _ = self.fake_collection('panels')
        shown = [invocation.args for invocation in ipc.call_args_list if 'show' in invocation.args]
        self.assertEqual(shown, perf.PANELS)
        self.assertEqual(len(result['panel_actions']), 7)
        self.assertTrue(all(invocation.args[1] in ('show', 'close') for invocation in ipc.call_args_list))
        self.assertEqual(ipc.call_args_list[-1].args, ('appearance', 'close'))

    def test_music_only_prompts(self):
        _, ipc, prompt = self.fake_collection('music')
        prompt.assert_called_once()
        ipc.assert_not_called()
        _, _, prompt = self.fake_collection('music', assume_playing=True)
        prompt.assert_not_called()

    def test_startup_never_restarts_shell(self):
        self.fixture()
        result, ipc, _ = self.fake_collection('startup')
        self.assertEqual(len(result['startup']), 1)
        self.assertIn('Unavailable', result['startup_readiness'])
        ipc.assert_not_called()

    def test_panel_failure_still_closes_both_surfaces(self):
        args = type('Args', (), dict(scenario='panels', settle=0, duration=1, interval=1, panel_seconds=4))()
        self.fixture()
        with patch.object(perf, 'snapshot', return_value=self.sample(1)), patch.object(perf, 'gpu_samples', return_value=[]), patch.object(perf, 'ipc', side_effect=RuntimeError('unavailable')) as ipc, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(RuntimeError):
                perf.collect(args)
        self.assertEqual(ipc.call_args_list[-2:].copy(), [unittest.mock.call('panels', 'close'), unittest.mock.call('appearance', 'close')])


if __name__ == '__main__':
    unittest.main()
