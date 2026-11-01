#!/usr/bin/env python3
"""Read-only desktop performance sampling, with optional panel presentation."""
import argparse
import datetime
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

GROUPS = ('bar', 'broker', 'elephant', 'walker', 'Hyprland', 'hyprpaper')
PANELS = [('panels', 'show', kind) for kind in
          ('calendar', 'hardware', 'notifications', 'keyboard', 'media')]
PANELS += [('appearance', 'show', kind) for kind in ('theme', 'wallpaper')]
ROOT = Path(__file__).resolve().parents[1]


def read(path):
    try:
        return path.read_text(errors='replace')
    except OSError:
        return ''


def command(arguments):
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=3,
                                check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def fields(text):
    result = {}
    for line in text.splitlines():
        key, separator, value = line.partition(':')
        if separator:
            result[key.strip()] = value.strip()
    return result


def group_for(name, arguments):
    if any(Path(argument).name == 'bar-data.py' for argument in arguments):
        return 'broker'
    if (name in ('quickshell', 'qs') or (arguments and Path(arguments[0]).name in ('quickshell', 'qs'))) and any('desktop-bar' in argument for argument in arguments):
        return 'bar'
    if name in GROUPS:
        return name
    return None


def process(path, ticks):
    stat = read(path / 'stat')
    # comm may contain spaces and parentheses; fields after its final ')' are fixed.
    suffix = stat[stat.rfind(')') + 2:].split()
    if len(suffix) < 22:
        raise ValueError('incomplete stat')
    name = stat[stat.find('(') + 1:stat.rfind(')')]
    status = fields(read(path / 'status'))
    memory = fields(read(path / 'smaps_rollup'))
    arguments = read(path / 'cmdline').rstrip('\0').split('\0')
    def counter(key):
        return int(status[key]) if key in status else None
    def kib(key):
        return int(memory[key].split()[0]) if key in memory else None
    return {'pid': int(path.name), 'ppid': int(suffix[1]),
            'start_ticks': int(suffix[19]), 'group': group_for(name, arguments),
            'cpu_seconds': (int(suffix[11]) + int(suffix[12])) / ticks,
            'rss_kib': kib('Rss'), 'pss_kib': kib('Pss'),
            'voluntary': counter('voluntary_ctxt_switches'),
            'nonvoluntary': counter('nonvoluntary_ctxt_switches')}


def snapshot(proc=Path('/proc')):
    ticks = os.sysconf('SC_CLK_TCK')
    processes = {}
    for path in proc.iterdir():
        if not path.name.isdigit():
            continue
        try:
            item = process(path, ticks)
            processes[(item['pid'], item['start_ticks'])] = item
        except (OSError, ValueError, IndexError):
            continue
    stat = read(proc / 'stat').splitlines()
    cpu = next((line.split()[1:9] for line in stat if line.startswith('cpu ')), [])
    counters = {line.split()[0]: line.split()[1] for line in stat if len(line.split()) == 2}
    memory = fields(read(proc / 'meminfo'))
    return {'time': time.monotonic(), 'processes': processes,
            'system': {'cpu_seconds': sum(map(int, cpu)) / ticks,
                       'busy_cpu_seconds': sum(int(value) for index, value in enumerate(cpu)
                                               if index not in (3, 4)) / ticks,
                       'context_switches': int(counters.get('ctxt', 0)),
                       'processes_including_threads': int(counters.get('processes', 0)),
                       'ram_used_kib': int(memory.get('MemTotal', '0').split()[0]) -
                       int(memory.get('MemAvailable', '0').split()[0])}}


def number(value):
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    except (ValueError, TypeError):
        return None


def gpu_samples():
    devices = []
    for device in sorted(Path('/sys/class/drm').glob('card[0-9]*/device')):
        busy = read(device / 'gpu_busy_percent').strip()
        power = next(iter(sorted(device.glob('hwmon/hwmon*/power1_average'))), None)
        power_value = number(read(power)) if power else None
        if busy or power:
            devices.append({'source': device.parent.name,
                            'busy_percent': number(busy),
                            'power_watts': power_value / 1e6 if power_value is not None else None})
    if shutil.which('nvidia-smi'):
        output = command(['nvidia-smi', '--query-gpu=index,utilization.gpu,power.draw',
                          '--format=csv,noheader,nounits'])
        for line in (output or '').splitlines():
            columns = line.split(',')
            if len(columns) == 3:
                devices.append({'source': 'nvidia:' + columns[0].strip(),
                                'busy_percent': number(columns[1]), 'power_watts': number(columns[2])})
    return devices


def mean(values):
    available = [value for value in values if value is not None]
    return sum(available) / len(available) if available else None


def summarize(samples):
    elapsed = samples[-1]['time'] - samples[0]['time']
    groups = {}
    for group in GROUPS:
        totals = {key: 0.0 for key in ('cpu_seconds', 'voluntary', 'nonvoluntary')}
        observations = {key: [] for key in ('rss_kib', 'pss_kib')}
        missing = set()
        for sample in samples:
            members = [item for item in sample['processes'].values() if item['group'] == group]
            for key in observations:
                values = [item[key] for item in members]
                observations[key].append(sum(values) if all(value is not None for value in values) else None)
        for previous, current in zip(samples, samples[1:]):
            for identity, item in current['processes'].items():
                if item['group'] != group:
                    continue
                older = previous['processes'].get(identity)
                # A newly observed process contributes its lifetime counters only if born in this interval.
                if older is None and item['start_ticks'] / os.sysconf('SC_CLK_TCK') < previous['uptime']:
                    continue
                for key in totals:
                    if item[key] is None or (older and older[key] is None):
                        missing.add(key)
                    else:
                        totals[key] += max(0, item[key] - (older[key] if older else 0))
        groups[group] = {**{key: None if key in missing else value for key, value in totals.items()},
                         **{key + '_mean': mean(values) for key, values in observations.items()}}
        groups[group]['process_count_peak'] = max(sum(item['group'] == group for item in sample['processes'].values()) for sample in samples)
        groups[group]['cpu_percent_one_core'] = totals['cpu_seconds'] / elapsed * 100
    launches = []
    seen = set(samples[0]['processes'])
    for sample in samples[1:]:
        for identity, item in sample['processes'].items():
            if identity not in seen:
                launches.append({key: item[key] for key in ('pid', 'ppid', 'start_ticks', 'group')})
                seen.add(identity)
    system = {key: samples[-1]['system'][key] - samples[0]['system'][key]
              for key in samples[0]['system'] if key != 'ram_used_kib'}
    for key in ('rss_kib', 'pss_kib'):
        system[key + '_readable_sum_mean'] = mean([sum(item[key] for item in sample['processes'].values() if item[key] is not None) for sample in samples])
        system[key + '_readable_process_count_mean'] = mean([sum(item[key] is not None for item in sample['processes'].values()) for sample in samples])
    system['ram_used_kib_mean'] = mean([sample['system']['ram_used_kib'] for sample in samples])
    return {'elapsed_seconds': elapsed, 'groups': groups, 'system': system,
            'observed_process_launches': launches, 'observed_process_launch_count': len(launches)}


def context():
    cpu = fields(read(Path('/proc/cpuinfo')))
    monitors = command(['hyprctl', '-j', 'monitors'])
    try:
        screens = [{key: monitor.get(key) for key in ('width', 'height', 'refreshRate', 'scale')}
                   for monitor in json.loads(monitors or '[]')]
    except (ValueError, TypeError):
        screens = []
    return {'cpu_model': cpu.get('model name'), 'logical_cores': os.cpu_count(),
            'ram_total': fields(read(Path('/proc/meminfo'))).get('MemTotal'),
            'gpu': command(['lspci', '-mm', '-d', '::03xx']), 'kernel': platform.release(),
            'power_profile': command(['powerprofilesctl', 'get']),
            'eitr_version': read(Path('/usr/share/eitr/version')).strip() or None,
            'checkout_revision': command(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']),
            'screens': screens, 'screen_count': len(screens)}


def ipc(*arguments):
    result = command(['eitr-shell', 'desktop-bar', 'ipc', 'call', '--', *arguments])
    if result is None:
        raise RuntimeError('bar IPC failed: ' + ' '.join(arguments))


def collect(args):
    if args.scenario == 'music' and not args.assume_playing:
        input('Press Enter when playing music (playback remains under your control): ')
    time.sleep(args.settle)
    samples, gpu, actions = [], [], []
    deadline = time.monotonic() + args.duration
    next_panel = 0.0
    sequence = 0
    try:
        while True:
            sample = snapshot()
            sample['uptime'] = float(read(Path('/proc/uptime')).split()[0])
            samples.append(sample)
            gpu.append({'elapsed': sample['time'] - samples[0]['time'], 'devices': gpu_samples()})
            now = time.monotonic()
            if now >= deadline:
                break
            if args.scenario == 'panels' and now >= next_panel:
                ipc('panels', 'close')
                ipc('appearance', 'close')
                action = PANELS[sequence % len(PANELS)]
                ipc(*action)
                actions.append({'elapsed': now - samples[0]['time'], 'action': action})
                sequence += 1
                next_panel = now + args.panel_seconds
            time.sleep(min(args.interval, max(0, deadline - time.monotonic())))
    finally:
        if args.scenario == 'panels':
            failures = []
            for target in ('panels', 'appearance'):
                try:
                    ipc(target, 'close')
                except RuntimeError as error:
                    failures.append(str(error))
            if failures:
                print('; '.join(failures), file=sys.stderr)
    result = summarize(samples)
    result.update({'gpu_samples': gpu, 'panel_actions': actions})
    devices_by_source = {}
    for sample in gpu:
        for device in sample['devices']:
            devices_by_source.setdefault(device['source'], []).append(device)
    result['gpu_means'] = {}
    for source, devices in devices_by_source.items():
        result['gpu_means'][source] = {
            key: mean([device[key] for device in devices])
            for key in ('busy_percent', 'power_watts')
        }
    if args.scenario == 'startup':
        uptime = samples[0]['uptime']
        ticks = os.sysconf('SC_CLK_TCK')
        result['startup'] = [{'pid': item['pid'], 'start_seconds_after_boot': item['start_ticks'] / ticks,
                              'age_seconds': uptime - item['start_ticks'] / ticks}
                             for item in samples[0]['processes'].values() if item['group'] == 'bar']
        result['startup_readiness'] = 'Unavailable: process start time does not establish first frame or UI readiness.'
    return result


def validate_destination(folder):
    folder = folder.expanduser().resolve()
    if folder == ROOT or ROOT in folder.parents:
        raise ValueError('results must be outside a repository')
    return folder


def save(result, folder):
    folder = validate_destination(folder)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    name = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    path = folder / (name + '.json')
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write('\n')
    return path


def compare(before, after):
    print(f'{"Metric":48} {"Before":>12} {"After":>12} {"Difference":>12}')
    for key in ('elapsed_seconds', 'observed_process_launch_count'):
        first, second = before['metrics'][key], after['metrics'][key]
        print(f'{key:48} {first:12.3f} {second:12.3f} {second-first:+12.3f}')
    for group in (*GROUPS, 'system'):
        older = before['metrics']['groups'][group] if group != 'system' else before['metrics']['system']
        newer = after['metrics']['groups'][group] if group != 'system' else after['metrics']['system']
        for key in sorted(older.keys() & newer.keys()):
            first, second = older[key], newer[key]
            if isinstance(first, (int, float)) and isinstance(second, (int, float)):
                print(f'{group + "." + key:48} {first:12.3f} {second:12.3f} {second-first:+12.3f}')
    for source in sorted(before['metrics'].get('gpu_means', {}).keys() & after['metrics'].get('gpu_means', {}).keys()):
        for key in ('busy_percent', 'power_watts'):
            first = before['metrics']['gpu_means'][source][key]
            second = after['metrics']['gpu_means'][source][key]
            if first is not None and second is not None:
                print(f'{"gpu." + source + "." + key:48} {first:12.3f} {second:12.3f} {second-first:+12.3f}')
    if before['configuration'] != after['configuration'] or before['context'] != after['context']:
        print('Context or configuration differs; inspect JSON before attributing differences to code.')


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('must be finite and greater than zero')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    measure = commands.add_parser('measure')
    measure.add_argument('scenario', choices=('idle', 'panels', 'music', 'startup'))
    measure.add_argument('--settle', type=float, default=30)
    measure.add_argument('--duration', type=positive, default=60)
    measure.add_argument('--interval', type=positive, default=1)
    measure.add_argument('--panel-seconds', type=positive, default=4)
    measure.add_argument('--assume-playing', action='store_true')
    measure.add_argument('--instrumented', action='store_true', help='label a separately instrumented test-shell run')
    measure.add_argument('--output-dir', type=Path, default=Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'eitr/perf')
    comparison = commands.add_parser('compare')
    comparison.add_argument('before', type=Path)
    comparison.add_argument('after', type=Path)
    args = parser.parse_args()
    try:
        if args.operation == 'compare':
            compare(json.loads(args.before.read_text()), json.loads(args.after.read_text()))
            return
        if not math.isfinite(args.settle) or args.settle < 0:
            parser.error('--settle must be finite and nonnegative')
        # Reject a repository destination before waiting or presenting panels.
        destination = validate_destination(args.output_dir)
        metadata = context()
        metrics = collect(args)
        configuration = {key: value for key, value in vars(args).items() if key not in ('output_dir', 'operation')}
        print(save({'schema_version': 1, 'context': metadata, 'configuration': configuration,
                    'metrics': metrics, 'limitations': [
                        'Process polling misses short-lived processes and final counters of exited processes.',
                        'System processes counter includes threads; observed launches enumerate process leaders.',
                        'Group context switches cover main threads and are only a wakeup proxy.',
                        'GPU counters are device-wide; unreadable memory is unavailable.',
                        'Startup timestamps do not measure first-frame readiness.'
                    ]}, destination))
    except (OSError, ValueError, RuntimeError, EOFError) as error:
        parser.exit(1, f'perf-baseline: {error}\n')
    except KeyboardInterrupt:
        parser.exit(130, 'perf-baseline: interrupted\n')


if __name__ == '__main__':
    main()
