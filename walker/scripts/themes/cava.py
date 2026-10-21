#!/usr/bin/env python3
"""Preserve user settings while replacing cava's theme-owned color section."""
import os
from pathlib import Path
import re
from palette import load
from eitr_paths import code


def generate(palette, existing):
    colors = [palette.get(key, palette['foreground']) for key in
              ('color4', 'color6', 'accent', 'color2', 'color3', 'color1')]
    section = '[color]\nbackground = default\nforeground = default\ngradient = 1\n'
    section += ''.join(f"gradient_color_{index} = '{color}'\n"
                       for index, color in enumerate(colors, 1))
    pattern = r'(?ms)^\[color\][^\n]*\n.*?(?=^\[|\Z)'
    if re.search(pattern, existing):
        return re.sub(pattern, lambda match: section + '\n', existing)
    return existing.rstrip() + '\n\n' + section


def main():
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    palette = load(os.environ.get('CURRENT_DIR', str(config / 'theme/current')))
    if not palette:
        return
    target = config / 'cava/config'
    default = code('cava/config').read_text()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(generate(palette, target.read_text() if target.exists() else default))


if __name__ == '__main__':
    main()
