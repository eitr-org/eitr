#!/usr/bin/env python3
"""Read a compact CPU, GPU, RAM, and installation-storage snapshot."""
import csv
import io
import json
from pathlib import Path
import shutil
import subprocess
import time


def query(command):
    try:
        return subprocess.check_output(command, text=True, timeout=2, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return ""


def cpu_ticks():
    values = [int(value) for value in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
    return sum(values), values[3] + values[4]


def cpu():
    before, idle_before = cpu_ticks()
    time.sleep(0.2)
    after, idle_after = cpu_ticks()
    usage = round(100 * (1 - (idle_after - idle_before) / max(1, after - before)))
    processors = []
    for block in Path('/proc/cpuinfo').read_text().strip().split('\n\n'):
        processors.append(dict(line.split(':', 1) for line in block.splitlines() if ':' in line))
    processors = [{key.strip(): value.strip() for key, value in item.items()} for item in processors]
    cores = {(item.get('physical id', '0'), item.get('core id', str(index))) for index, item in enumerate(processors)}
    mhz = [float(item['cpu MHz']) for item in processors if 'cpu MHz' in item]
    temperature = 'Unavailable'
    try:
        sensors = json.loads(query(['sensors', '-j']))
        for device in sensors.values():
            for label in ('Package id 0', 'Tctl', 'Tdie', 'PECI 0.0'):
                for key, value in device.get(label, {}).items():
                    if key.endswith('_input'):
                        temperature = f'{value:.0f}°C'
                        break
                if temperature != 'Unavailable':
                    break
            if temperature != 'Unavailable':
                break
    except (ValueError, AttributeError):
        pass
    load = ' / '.join(Path('/proc/loadavg').read_text().split()[:3])
    return {'title': 'CPU', 'name': processors[0].get('model name', 'Processor'), 'usage': usage,
            'rows': [['Cores / threads', f'{len(cores)} / {len(processors)}'],
                     ['Frequency / temperature', f'{sum(mhz) / len(mhz) / 1000:.2f} GHz · {temperature}' if mhz else temperature],
                     ['Load · 1 / 5 / 15 min', load]]}


def gib(kib):
    return f'{kib / 1024 / 1024:.1f} GiB'


def memory():
    values = {key: int(value.split()[0]) for key, value in
              (line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())}
    total = values['MemTotal']
    available = values['MemAvailable']
    used = total - available
    swap = values['SwapTotal']
    return {'title': 'RAM', 'name': 'System memory', 'usage': round(100 * used / total),
            'rows': [['Used / total', f'{gib(used)} / {gib(total)}'],
                     ['Available', gib(available)],
                     ['Swap used / total', f'{gib(swap - values["SwapFree"])} / {gib(swap)}']]}


def gpu():
    raw = query(['nvidia-smi', '--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit',
                 '--format=csv,noheader,nounits'])
    entries = list(csv.reader(io.StringIO(raw)))
    if not entries:
        return {'title': 'GPU', 'name': 'GPU telemetry unavailable', 'usage': None, 'rows': []}
    name, usage, used, total, temperature, power, limit = [value.strip() for value in entries[0]]
    def number(value, unit, divisor=1):
        try:
            return f'{float(value) / divisor:.1f} {unit}'
        except ValueError:
            return 'Unavailable'
    return {'title': 'GPU', 'name': name, 'usage': float(usage) if usage.isdigit() else None,
            'rows': [['VRAM used / total', f'{number(used, "GiB", 1024)} / {number(total, "GiB", 1024)}'],
                     ['Temperature', number(temperature, '°C')],
                     ['Power / limit', f'{number(power, "W")} / {number(limit, "W")}']]}


def storage():
    try:
        devices = json.loads(query(['lsblk', '-J', '-b', '-o', 'NAME,TYPE,SIZE,MODEL,ROTA,MOUNTPOINTS']))['blockdevices']
    except (ValueError, KeyError, TypeError):
        devices = []

    def hosts_root(device):
        return '/' in (device.get('mountpoints') or []) or any(
            hosts_root(child) for child in device.get('children', []))

    device = next((device for device in devices if device.get('type') == 'disk' and hosts_root(device)), None)
    rows = []
    name = 'Arch installation · /'
    if device:
        name = device.get('name', '')
        kind = 'HDD' if device.get('rota') else ('NVMe SSD' if name.startswith('nvme') else 'SSD')
        capacity = f'{int(device.get("size") or 0) / 1024 ** 3:.1f} GiB'
        rows = [['Type / device', f'{kind} · {name}'], ['Capacity', capacity]]
        name = (device.get('model') or name).strip()
    usage = None
    try:
        stats = shutil.disk_usage('/')
        usage = round(100 * stats.used / max(1, stats.total))
        rows.extend([
            ['Used / total', f'{stats.used / 1024 ** 3:.1f} / {stats.total / 1024 ** 3:.1f} GiB'],
            ['Free', f'{stats.free / 1024 ** 3:.1f} GiB'],
        ])
    except OSError:
        rows.append(['Status', 'Usage unavailable'])
    return [{'title': 'Storage', 'name': name, 'usage': usage, 'rows': rows}]


if __name__ == '__main__':
    print(json.dumps({'sections': [cpu(), gpu(), memory(), *storage()]}))
