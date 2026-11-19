"""Shared battery warning level settings."""
from eitr_paths import config, read_settings, write_settings

DEFAULTS = {'low': 10, 'critical': 5}


def validate_levels(low, critical):
    if type(low) is not int or type(critical) is not int:
        raise ValueError('Battery warning levels must be integers')
    if not (2 <= critical < low <= 50):
        raise ValueError(f'Invalid battery warning levels: critical ({critical}) must be < low ({low}), and both between 2 and 50%')
    return low, critical


def settings():
    try:
        path = config('eitr/power.json')
        if not path.exists():
            return dict(DEFAULTS)
        data = read_settings(path, DEFAULTS)
        low = int(data.get('low', 10))
        critical = int(data.get('critical', 5))
        validate_levels(low, critical)
        return {'low': low, 'critical': critical}
    except (OSError, ValueError, TypeError):
        return dict(DEFAULTS)


def set_levels(low=None, critical=None):
    current = settings()
    new_low = current['low'] if low is None else int(low)
    new_critical = current['critical'] if critical is None else int(critical)
    validate_levels(new_low, new_critical)
    write_settings(config('eitr/power.json'), {'low': new_low, 'critical': new_critical})
    return {'low': new_low, 'critical': new_critical}
