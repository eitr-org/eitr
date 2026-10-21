#!/usr/bin/env python3
"""Write the bar's private raw-output config, then replace this process with cava."""
import os
from pathlib import Path
import tempfile

CONFIG = """[general]
bars = 4
framerate = 30
[input]
method = pipewire
source = auto
[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 100
bar_delimiter = 59
frame_delimiter = 10
"""


def write_config(directory):
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'cava-bar.conf'
    descriptor, temporary = tempfile.mkstemp(prefix='cava-bar-', dir=directory)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(CONFIG)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


if __name__ == '__main__':
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    base = Path(runtime) if runtime else Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))
    config = write_config(base / 'eitr')
    os.execvp('cava', ['cava', '-p', str(config)])
