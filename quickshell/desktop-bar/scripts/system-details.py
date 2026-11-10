#!/usr/bin/env python3
"""Read a compact CPU, GPU, RAM, and installation-storage snapshot."""
import csv
import io
import json
from pathlib import Path
import shutil
import subprocess
import time
import sys


def query(command):
    try:
        return subprocess.check_output(command, text=True, timeout=2, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return ""


def cpu_ticks():
    values = [int(value) for value in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
    return sum(values), values[3] + values[4]


def cpu_identity(cpuinfo):
    processors = []
    for block in cpuinfo.strip().split('\n\n'):
        processors.append({key.strip(): value.strip() for key, value in
                           (line.split(':', 1) for line in block.splitlines() if ':' in line)})
    cores = {(item.get('physical id', '0'), item.get('core id', str(index)))
             for index, item in enumerate(processors)}
    return {'name': processors[0].get('model name', 'Processor'),
            'cores': f'{len(cores)} / {len(processors)}'}


def cpu(identity=None):
    before, idle_before = cpu_ticks()
    time.sleep(0.2)
    after, idle_after = cpu_ticks()
    usage = round(100 * (1 - (idle_after - idle_before) / max(1, after - before)))
    cpuinfo = Path('/proc/cpuinfo').read_text()
    if identity is None:
        identity = cpu_identity(cpuinfo)
    mhz = [float(line.split(':', 1)[1]) for line in cpuinfo.splitlines() if line.startswith('cpu MHz')]
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
    return {'title': 'CPU', 'name': identity['name'], 'usage': usage,
            'rows': [['Cores / threads', identity['cores']],
                     ['Frequency / temperature', f'{sum(mhz) / len(mhz) / 1000:.2f} GHz · {temperature}' if mhz else temperature],
                     ['Load · 1 / 5 / 15 min', load]]}


def gib(kib):
    return f'{kib / 1024 / 1024:.1f} GiB'


def memory(identity=None):
    values = {key: int(value.split()[0]) for key, value in
              (line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())}
    total = values['MemTotal']
    available = values['MemAvailable']
    used = total - available
    swap = values['SwapTotal']
    return {'title': 'RAM', 'name': (identity or memory_identity())['name'], 'usage': round(100 * used / total),
            'rows': [['Used / total', f'{gib(used)} / {gib(total)}'],
                     ['Available', gib(available)],
                     ['Swap used / total', f'{gib(swap - values["SwapFree"])} / {gib(swap)}']]}


def gpu(identity=None):
    if identity is not None and not identity["available"]:
        return {"title": "GPU", "name": "GPU telemetry unavailable", "usage": None, "rows": []}
    fields = 'utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit'
    if identity is None:
        fields = 'name,' + fields
    raw = query(['nvidia-smi', '--query-gpu=' + fields,
                 '--format=csv,noheader,nounits'])
    entries = list(csv.reader(io.StringIO(raw)))
    if not entries:
        return {'title': 'GPU', 'name': 'GPU telemetry unavailable', 'usage': None, 'rows': []}
    values = [value.strip() for value in entries[0]]
    if identity is not None:
        values.insert(0, identity['name'])
    name, usage, used, total, temperature, power, limit = values
    def number(value, unit, divisor=1):
        try:
            return f'{float(value) / divisor:.1f} {unit}'
        except ValueError:
            return 'Unavailable'
    return {'title': 'GPU', 'name': identity['name'] if identity else name, 'usage': float(usage) if usage.isdigit() else None,
            'rows': [['VRAM used / total', f'{number(used, "GiB", 1024)} / {number(total, "GiB", 1024)}'],
                     ['Temperature', number(temperature, '°C')],
                     ['Power / limit', f'{number(power, "W")} / {number(limit, "W")}']]}


def storage(identity=None):
    if identity is None:
        identity = storage_identity()
    name, rows = identity["name"], [list(row) for row in identity["rows"]]
    return storage_usage(name, rows)


def storage_identity():
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
    return {"name": name, "rows": rows}


def storage_usage(name, rows):
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


def installed_memory(memory=Path('/sys/devices/system/memory'), meminfo=Path('/proc/meminfo')):
    """Installed RAM in GiB: the kernel's online memory blocks, else usable memory."""
    try:
        block = int((memory / 'block_size_bytes').read_text(), 16)
        online = sum(1 for state in memory.glob('memory*/state') if state.read_text().strip() == 'online')
        if block and online:
            return online * block / 1024 ** 3
    except (OSError, ValueError):
        pass
    total = next(int(line.split()[1]) for line in meminfo.read_text().splitlines() if line.startswith('MemTotal:'))
    return total / 1024 ** 2


def memory_modules(properties):
    """Installed modules from udev's DMI properties (`udevadm info -p /devices/virtual/dmi/id`)."""
    modules = {}
    for line in properties.splitlines():
        key, _, value = line.partition('=')
        parts = key.split('_', 3)
        if len(parts) == 4 and parts[:2] == ['MEMORY', 'DEVICE'] and parts[2].isdigit():
            modules.setdefault(int(parts[2]), {})[parts[3]] = value
    return [module for _, module in sorted(modules.items()) if module.get('PRESENT') != '0' and module.get('SIZE', '0').isdigit()
            and int(module['SIZE']) > 0]


def memory_summary(properties, installed, *, brief=False):
    """Amount, type and speed of the installed RAM; the full form adds rated speed and modules."""
    modules = memory_modules(properties)
    if not modules:
        return f'{installed:.0f} GiB'
    sizes = {int(module['SIZE']) for module in modules}
    kinds = sorted({module.get('TYPE') for module in modules if module.get('TYPE') not in (None, 'Unknown', 'Other')})
    running = sorted({int(module['CONFIGURED_SPEED_MTS']) for module in modules if module.get('CONFIGURED_SPEED_MTS', '').isdigit()})
    rated = sorted({int(module['SPEED_MTS']) for module in modules if module.get('SPEED_MTS', '').isdigit()})
    speed = ''
    if running:
        speed = f'{running[0]} MT/s' + (f' (rated {rated[-1]} MT/s)' if rated and rated[-1] > running[0] and not brief else '')
    elif rated:
        speed = f'{rated[-1]} MT/s'
    layout = '' if brief else f'{len(modules)} × {sizes.pop() / 1024 ** 3:.0f} GiB' if len(sizes) == 1 else f'{len(modules)} modules'
    return ' · '.join(filter(None, [f'{installed:.0f} GiB', '/'.join(kinds), speed, layout]))


def memory_lines(properties, installed):
    """About's RAM line: amount, type, speed and module layout when the firmware describes them."""
    return [{'title': 'RAM', 'name': memory_summary(properties, installed)}]


def memory_identity():
    """The RAM card's caption, kept with the identity: installed memory does not change while running."""
    try:
        return {'name': memory_summary(query(['udevadm', 'info', '-q', 'property', '-p', '/devices/virtual/dmi/id']),
                                       installed_memory(), brief=True)}
    except (OSError, ValueError):
        return {'name': 'System memory'}


def disk_size(size):
    """Capacity in the decimal units printed on drives: 500 GB, 1.0 TB."""
    return f'{size / 1e12:.1f} TB' if size >= 1e12 else f'{round(size / 1e9)} GB'


def graphics_names(listing):
    """Display controllers from `lspci -mm`: vendor and the bracketed product name."""
    names = []
    for row in csv.reader(io.StringIO(listing), delimiter=' '):
        if len(row) > 3 and row[1] in ('VGA compatible controller', '3D controller', 'Display controller'):
            vendor = row[2].replace(' Corporation', '').replace('Advanced Micro Devices, Inc. ', '')
            product = row[3][row[3].find('[') + 1:row[3].rfind(']')] if '[' in row[3] else row[3]
            names.append(f'{vendor} {product}'.strip())
    return names


def disks(devices):
    """Every connected drive from `lsblk -J -d -b`, skipping RAM disks, loops and optical drives."""
    result = []
    for device in devices:
        name = device.get('name', '')
        if device.get('type') != 'disk' or name.startswith(('zram', 'loop', 'ram')):
            continue
        kind = 'HDD' if device.get('rota') else ('NVMe SSD' if name.startswith('nvme') else 'SSD')
        if device.get('tran') == 'usb':
            kind = 'USB ' + ('drive' if device.get('rota') else 'SSD')
        model = (device.get('model') or name).strip()
        result.append({'title': 'Storage', 'name': f'{model} · {kind} · {disk_size(int(device.get("size") or 0))}'})
    return result


# Firmware fills unused DMI fields with placeholders instead of leaving them empty.
DMI_PLACEHOLDERS = {'', 'default string', 'to be filled by o.e.m.', 'not specified', 'not applicable', 'none', 'system product name'}


def motherboard(dmi=Path('/sys/devices/virtual/dmi/id')):
    """The board's model name, or None when the firmware does not give a real one."""
    try:
        name = (dmi / 'board_name').read_text().strip()
    except OSError:
        return None
    return None if name.casefold() in DMI_PLACEHOLDERS else name


def inventory():
    """About's hardware lines: names and amounts that do not change while running."""
    lines = [{'title': 'CPU', 'name': cpu_identity(Path('/proc/cpuinfo').read_text())['name']}]
    lines += [{'title': 'GPU', 'name': name} for name in graphics_names(query(['lspci', '-mm']))]
    board = motherboard()
    if board:
        lines.append({'title': 'Motherboard', 'name': board})
    lines += memory_lines(query(['udevadm', 'info', '-q', 'property', '-p', '/devices/virtual/dmi/id']), installed_memory())
    try:
        devices = json.loads(query(['lsblk', '-J', '-d', '-b', '-o', 'NAME,TYPE,SIZE,MODEL,ROTA,TRAN']))['blockdevices']
    except (ValueError, KeyError, TypeError):
        devices = []
    return lines + disks(devices)


def snapshot(identity=None):
    if identity is None:
        identity = {}
    if 'cpu' not in identity:
        identity['cpu'] = cpu_identity(Path('/proc/cpuinfo').read_text())
    if 'storage' not in identity:
        identity['storage'] = storage_identity()
    if 'memory' not in identity:
        identity['memory'] = memory_identity()
    if 'gpu' not in identity:
        graphics = gpu()
        identity['gpu'] = {'available': graphics['usage'] is not None or bool(graphics['rows']),
                           'name': graphics['name']}
    else:
        graphics = gpu(identity['gpu'])
    return {'identity': identity, 'sections': [cpu(identity['cpu']), graphics, memory(identity['memory']), *storage(identity['storage'])]}


if __name__ == '__main__':
    identity = json.loads(sys.stdin.readline()) if '--identity' in sys.argv else None
    print(json.dumps(snapshot(identity)))
