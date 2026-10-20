#!/usr/bin/env python3
"""Choose palette colors with readable contrast on Walker's row highlight."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette import contrast, is_light, load, rgb  # noqa: E402


def selection_colors(palette, light=False):
    base = palette['background']
    overlay = palette.get('color8', palette.get('color0', base))
    alpha = 0.22 if light else 0.26
    background = '#' + ''.join(f'{round(a * alpha + b * (1 - alpha)):02x}'
                              for a, b in zip(rgb(overlay), rgb(base)))
    candidates = [palette['foreground'], base, *palette.values()]
    candidates = [color for color in candidates
                  if isinstance(color, str) and len(color) == 7 and color.startswith('#')]

    def readable(preferred):
        for color in [preferred, *candidates]:
            if contrast(color, background) >= 4.5:
                return color
        return max(candidates, key=lambda color: contrast(color, background))

    return {'background': background,
            'foreground': readable(palette.get('selection_foreground', base)),
            'current': readable(palette['accent'])}


if __name__ == '__main__':
    directory = Path(sys.argv[1])
    print(json.dumps(selection_colors(load(directory), is_light(directory))))
