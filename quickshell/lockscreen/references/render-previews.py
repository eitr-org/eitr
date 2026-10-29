#!/usr/bin/env python3
"""Render privacy-safe 4K previews offscreen with mock authentication only."""
import argparse
import configparser
import json
import os
from pathlib import Path
import subprocess
import tempfile
from aurora_reference import AuroraReference

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    designs = sorted((ROOT / "themes").rglob("Main.qml"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("designs", nargs="*", help="optional design IDs; default: all")
    requested = parser.parse_args().designs
    known = {str(design.parent.relative_to(ROOT / "themes")) for design in designs}
    if set(requested) - known:
        parser.error("Unknown design ID")
    with tempfile.TemporaryDirectory(prefix="eitr-lockscreen-render-") as directory:
        aurora = AuroraReference(directory)
        screen = Path(directory) / "screen.json"
        screen.write_text(json.dumps({"screens": [{"name": "4K", "x": 0, "y": 0,
                                                   "width": 3840, "height": 2160,
                                                   "logicalDpi": 96, "dpr": 1}]}))
        for design in designs:
            if requested and str(design.parent.relative_to(ROOT / "themes")) not in requested:
                continue
            parser = configparser.ConfigParser(interpolation=None)
            parser.optionxform = str
            parser.read(design.parent / "theme.conf")
            settings = dict(parser["General"])
            if design.parent.name == "theme-wallpaper":
                settings['background'] = (ROOT.parents[1] / 'themes/eitr/backgrounds/02-eitr-runestone.png').as_uri()
            environment = dict(os.environ, QT_QPA_PLATFORM=f"offscreen:configfile={screen}",
                               QSG_RHI_BACKEND="opengl", LIBGL_ALWAYS_SOFTWARE="1",
                               QML_IMPORT_PATH=os.pathsep.join((str(ROOT.parent), str(ROOT / "imports"))),
                               LC_ALL="C.UTF-8",
                               EITR_RENDER_CONFIG=json.dumps(settings),
                               EITR_RENDER_DESIGN=design.as_uri(),
                               EITR_RENDER_OUTPUT=str(design.parent / "preview.png"))
            if design.parent.name == 'eitr':
                environment['EITR_RENDER_AURORA'] = aurora.render(settings, 3840, 2160)
            environment.pop("QT_QUICK_BACKEND", None)
            result = subprocess.run(["quickshell", "-n", "-p", str(HERE / "render-preview.qml")],
                                    env=environment, capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            print(design.parent.relative_to(ROOT / "themes"), flush=True)


if __name__ == "__main__":
    main()
