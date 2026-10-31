#!/usr/bin/env python3
"""Render Eitr's aspect, palette and password-state review matrix without locking."""
import argparse
import itertools
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
from aurora_reference import AuroraReference

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=REPOSITORY.parent / 'eitr-lockscreen-renders')
    output = parser.parse_args().output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='eitr-render-') as temporary:
        runtime = Path(temporary)
        aurora = AuroraReference(runtime)
        for (width, height), theme, state in itertools.product(
                ((2560, 1080), (1920, 1080), (1080, 1920)),
                ('eitr', 'daylight'), ('empty', 'typed', 'wrong')):
            folder = REPOSITORY / 'themes' / theme
            palette = tomllib.loads((folder / 'colors.toml').read_text())
            settings = {key: palette[key] for key in ('accent', 'foreground', 'muted', 'alert') if key in palette}
            settings.update(backgroundColor=palette['background'],
                            themeMode='light' if (folder / 'light.mode').exists() else 'dark',
                            palette=[palette[key] for key in ('accent', 'color6', 'color4', 'color5', 'color3')],
                            reduceMotion=True, clock='12h', eitrTheme=theme == 'eitr')
            screen = runtime / 'screen.json'
            screen.write_text(json.dumps({'screens': [{'name': 'Preview', 'width': width, 'height': height,
                                                       'x': 0, 'y': 0, 'logicalDpi': 96, 'dpr': 1}]}))
            target = output / f'{width}x{height}-{theme}-{state}.png'
            environment = dict(os.environ, QT_QPA_PLATFORM=f'offscreen:configfile={screen}',
                               QSG_RHI_BACKEND='opengl', LIBGL_ALWAYS_SOFTWARE='1',
                               XDG_RUNTIME_DIR=str(runtime), LC_ALL='C.UTF-8',
                               QML_IMPORT_PATH=os.pathsep.join((str(ROOT.parent), str(ROOT / 'imports'))),
                               EITR_RENDER_AURORA=aurora.render(settings, width, height),
                               EITR_RENDER_CONFIG=json.dumps(settings),
                               EITR_RENDER_DESIGN=(ROOT / 'themes/eitr/Main.qml').as_uri(),
                               EITR_RENDER_OUTPUT=str(target), EITR_RENDER_WIDTH=str(width),
                               EITR_RENDER_HEIGHT=str(height), EITR_RENDER_STATE=state)
            environment.pop('QT_QUICK_BACKEND', None)
            result = subprocess.run(['quickshell', '-n', '-p', str(ROOT / 'references/render-preview.qml')],
                                    env=environment, capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            print(target.name, flush=True)
        aurora.write_report(output / 'render-method.json')


if __name__ == '__main__':
    main()
