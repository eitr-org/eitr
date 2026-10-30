"""Read system batteries without treating peripheral batteries as laptop hardware."""
from pathlib import Path

POWER_SUPPLY = Path('/sys/class/power_supply')


def system_batteries(root=POWER_SUPPLY):
    batteries = []
    for supply in root.glob('*'):
        try:
            if (supply / 'type').read_text().strip() != 'Battery':
                continue
            if (supply / 'scope').exists() and (supply / 'scope').read_text().strip() == 'Device':
                continue
            if (supply / 'present').exists() and (supply / 'present').read_text().strip() == '0':
                continue
            batteries.append(supply)
        except OSError:
            continue
    return batteries
