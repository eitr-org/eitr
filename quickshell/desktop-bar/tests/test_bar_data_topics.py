"""Pure topic contracts, independent of broker and domain initialization."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'bar_data_topics.py'
spec = importlib.util.spec_from_file_location('topic_contracts', SCRIPT)
topics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topics)


class TopicContractTests(unittest.TestCase):
    def test_every_fixture_topic_has_exactly_one_definition(self):
        fixtures = json.loads((SCRIPT.parents[1] / 'tests/fixtures/domain-results.json').read_text())
        self.assertEqual(len(topics._DEFINITIONS), len(topics.TOPICS))
        self.assertEqual(set(fixtures), set(topics.TOPICS))
        for name, definition in topics.TOPICS.items():
            with self.subTest(topic=name):
                self.assertEqual(definition.name, name)
                self.assertEqual(definition.domain, name.split('.')[0])
                self.assertEqual(definition.interval, topics.INTERVALS[name])
                for result in fixtures[name]:
                    topics.validate_result(name, result)

    def test_read_budgets_preserve_default_and_short_test_timeouts(self):
        overrides = {'updates.status': 365, 'weather.default': 17, 'remote.status': 10,
                     'display.topology': 16, 'display.settings': 6, 'display.brightness': 9,
                     'capture.details': 25, 'capture.summary': 10}
        for name, definition in topics.TOPICS.items():
            for timeout in (0.01, 4, 5, 12):
                with self.subTest(topic=name, timeout=timeout):
                    expected = overrides.get(name, timeout)
                    if timeout < 5:
                        expected = min(expected, timeout)
                    self.assertEqual(definition.budget(timeout), expected)

    def test_validation_rejects_nonobjects_nonfinite_and_oversized_results(self):
        for name in topics.TOPICS:
            for result in (None, [], {'extra': float('nan')},
                           {'extra': float('inf')}, {'extra': 'x' * topics.MAX_RESULT}):
                with self.subTest(topic=name, result_type=type(result)), self.assertRaises(ValueError):
                    topics.validate_result(name, result)

    def test_import_has_no_domain_imports_or_io(self):
        code = '''import importlib.util, sys
spec = importlib.util.spec_from_file_location('topic_contracts', sys.argv[1])
module = importlib.util.module_from_spec(spec)
# Read dependencies before observing module execution.
import json, typing, types
spec.loader.get_code(spec.name)
def audit(event, args):
    if event in {'subprocess.Popen', 'socket.__new__', 'os.system'}:
        raise AssertionError(event)
    if event == 'open' and isinstance(args[1], str) and any(flag in args[1] for flag in 'wax+'):
        raise AssertionError(event)
    if event == 'import' and (args[0].startswith('bar_') or args[0].endswith('_domain')):
        raise AssertionError(event)
sys.addaudithook(audit)
spec.loader.exec_module(module)
assert not any(name.startswith('bar_') or name.endswith('_domain') for name in sys.modules)
'''
        result = subprocess.run([sys.executable, '-B', '-c', code, str(SCRIPT)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
