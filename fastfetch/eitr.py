#!/usr/bin/env python3
"""Render Eitr's About page using the active desktop theme and Fastfetch."""
import argparse
import json
import os
from pathlib import Path

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code, config as user_config
import re
import subprocess
import tempfile
import tomllib


def terminal_logo(path, width=34, height=34):
    """Render the selected logo's alpha mask as theme-colored terminal cells.

    Returns None when the logo has no visible alpha mask to render.
    """
    from PIL import Image
    with Image.open(path) as source:
        if "A" not in source.getbands():
            return None
        alpha = source.getchannel("A")
        bounds = alpha.getbbox()
        if bounds is None:
            return None
        alpha = alpha.crop(bounds).resize((width, height), Image.Resampling.LANCZOS)
        rows = []
        for y in range(0, height, 2):
            rows.append("".join(" ▄▀█"[(alpha.getpixel((x, y)) >= 128) * 2
                                      + (alpha.getpixel((x, y + 1)) >= 128)]
                                for x in range(width)))
        return "$1" + "\n".join(rows)


def text(path, fallback):
    try:
        return " ".join(path.read_text().split()) or fallback
    except OSError:
        return fallback


def eitr_version():
    """The release and build of the installed eitr-desktop, for example 0.6.3 "Mimir" (beta, build ...)."""
    release, stamp = code("release.json"), code("version")
    if not release.is_file() or not stamp.is_file():
        return "development checkout"
    data = json.loads(release.read_text())
    build = stamp.read_text().strip().removeprefix(data["version"] + ".")
    return f'{data["version"]} "{data["codename"]}" ({data["stage"]}, build {build})'



def build_config(config_home, cache_home, image=True):
    current = config_home / "theme/current"
    try:
        palette = tomllib.loads((current / "colors.toml").read_text())
        palette = palette.get("colors", palette)
    except (OSError, tomllib.TOMLDecodeError):
        palette = {}
    def color(name, fallback):
        value = palette.get(name, fallback)
        return value if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value) else fallback
    accent = color("accent", "#509475")
    foreground = color("foreground", "#cdd6f4")
    background = color("background", "#1e1e2e")
    theme = text(current / "display-name", text(cache_home / "current-theme", "Default"))
    try:
        settings = json.loads((config_home / "quickshell/desktop-bar/bar-settings.json").read_text())
    except (OSError, ValueError):
        settings = {}
    appearance = "Theme Color" if settings.get("appearance") == "solid" else "Blur"
    def custom(key, value):
        return {"type": "custom", "key": key, "format": value}
    def swatches(start):
        parts = []
        for i in range(start, start + 8):
            value = color(f"color{i}", foreground)
            parts.append("{#" + value + "}██{#}")
        return " ".join(parts)
    logo = code("fastfetch/assets/eitr-logo.png")
    logo_source = terminal_logo(logo) if image and logo.exists() else None
    wordmark = code("fastfetch/assets/eitr-wordmark.png")
    wordmark_source = terminal_logo(wordmark, 24, 10) if image and wordmark.exists() else None
    # A space suppresses Fastfetch's default "Custom" key for empty strings.
    heading = [custom(" ", "{#" + accent + "}" + row + "{#}")
               for row in wordmark_source.removeprefix("$1").splitlines()] if wordmark_source else []
    return {
        "logo": {"type": "data", "source": logo_source,
                 "color": {"1": accent}, "padding": {"right": 4, "left": 2}}
                if logo_source else {"type": "none"},
        "display": {"separator": "  ", "color": {"keys": accent}},
        "modules": [
            *heading,
            custom("Eitr", "Arch-based Linux desktop"), custom("Version", eitr_version()), "break",
            {"type": "os", "key": "Base"}, "kernel", "uptime", "packages",
            "wm", custom("Shell", Path(os.environ.get("SHELL", "/bin/sh")).name), "terminal", "display", "break",
            "cpu", "gpu", "memory", {"type": "disk", "folders": "/"}, "break",
            custom("Theme", theme), custom("Appearance", appearance),
            custom("Accent", accent), custom("Foreground", foreground),
            custom("Background", background), custom("Palette 0–7", swatches(0)),
            custom("Palette 8–15", swatches(8)),
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-only", action="store_true")
    parser.add_argument("--no-logo", action="store_true")
    args = parser.parse_args()
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", user_config()))
    cache_home = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    config = build_config(config_home, cache_home, not args.no_logo)
    if args.config_only:
        print(json.dumps(config, ensure_ascii=False, indent=2))
        return
    # Private, per-invocation config: no shared mutable generated state or stale themes.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as output:
        json.dump(config, output, ensure_ascii=False)
        output.flush()
        try:
            # Capturing output lets us normalize only outer blank lines. Keep
            # terminal colors enabled when the final destination is a terminal.
            import sys
            result = subprocess.run(
                ["fastfetch", "--config", output.name, "--pipe",
                 "false" if sys.stdout.isatty() else "true"],
                check=False, stdout=subprocess.PIPE, text=True)
        except FileNotFoundError:
            parser.exit(1, "Fastfetch is not installed. Install the distro's fastfetch package.\n")
        print("\n" + result.stdout.strip("\n") + "\n", flush=True)
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
