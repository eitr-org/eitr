#!/usr/bin/env python3
"""Write the bar's private raw-output config, then replace this process with cava."""
import argparse
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


def write_config(directory, bars=4, framerate=30, monstercat=0, noise_reduction=77):
    if type(bars) is not int or not 4 <= bars <= 128 or type(framerate) is not int or not 1 <= framerate <= 60:
        raise ValueError("Invalid cava bars or framerate")
    if not 0 <= monstercat <= 10 or type(noise_reduction) is not int or not 0 <= noise_reduction <= 100:
        raise ValueError("Invalid cava smoothing")
    text = CONFIG.replace("bars = 4", f"bars = {bars}").replace("framerate = 30", f"framerate = {framerate}")
    if monstercat != 0 or noise_reduction != 77:
        text += f"[smoothing]\nmonstercat = {monstercat}\nnoise_reduction = {noise_reduction}\n"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'cava-bar.conf'
    descriptor, temporary = tempfile.mkstemp(prefix='cava-bar-', dir=directory)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(text)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bars', type=int, default=4)
    parser.add_argument('--framerate', type=int, default=30)
    parser.add_argument('--monstercat', type=float, default=0)
    parser.add_argument('--noise-reduction', type=int, default=77)
    options = parser.parse_args()
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    base = Path(runtime) if runtime else Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))
    config = write_config(base / 'eitr', options.bars, options.framerate, options.monstercat, options.noise_reduction)
    os.execvp('cava', ['cava', '-p', str(config)])
