#!/usr/bin/env python3
"""Generate an fcitx5 classicui theme from the current Eitr theme and font."""
import argparse
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def atomic_write(path, content):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text() == content:
        return False
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd, temporary = tempfile.mkstemp(prefix=".eitr-fcitx5-", dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def render_theme(palette_colors, palette_module):
    surface = palette_colors.get("surface") or palette_colors["background"]
    foreground = palette_colors["foreground"]
    accent = palette_colors["accent"]
    highlight_fg = max(
        (palette_colors["background"], foreground),
        key=lambda candidate: palette_module.contrast(candidate, accent),
    )
    muted = palette_colors.get("muted") or palette_colors.get("color8") or foreground
    return f"""[Metadata]
Name=Eitr
Version=1
Author=Eitr
Description=Generated from the current Eitr theme
ScaleWithDPI=True

[InputPanel]
NormalColor={foreground}
HighlightCandidateColor={highlight_fg}
HighlightColor={highlight_fg}
HighlightBackgroundColor={accent}
PageButtonAlignment=Last Candidate

[InputPanel/TextMargin]
Left=12
Right=12
Top=8
Bottom=8

[InputPanel/ContentMargin]
Left=6
Right=6
Top=6
Bottom=6

[InputPanel/Background]
Color={surface}
BorderColor={accent}
BorderWidth=2

[InputPanel/Background/Margin]
Left=2
Right=2
Top=2
Bottom=2

[InputPanel/Highlight]
Color={accent}

[InputPanel/Highlight/Margin]
Left=8
Right=8
Top=5
Bottom=5

[InputPanel/PrevPage]
Image=prev.svg

[InputPanel/PrevPage/ClickMargin]
Left=6
Right=6
Top=5
Bottom=5

[InputPanel/NextPage]
Image=next.svg

[InputPanel/NextPage/ClickMargin]
Left=6
Right=6
Top=5
Bottom=5

[Menu]
NormalColor={foreground}
HighlightCandidateColor={highlight_fg}

[Menu/Background]
Color={surface}
BorderColor={accent}
BorderWidth=2

[Menu/Background/Margin]
Left=2
Right=2
Top=2
Bottom=2

[Menu/ContentMargin]
Left=6
Right=6
Top=6
Bottom=6

[Menu/CheckBox]
Image=radio.svg

[Menu/SubMenu]
Image=arrow.svg

[Menu/Highlight]
Color={accent}

[Menu/Highlight/Margin]
Left=8
Right=8
Top=5
Bottom=5

[Menu/Separator]
Color={muted}

[Menu/TextMargin]
Left=12
Right=12
Top=8
Bottom=8
"""


def update_classicui(conf_path, font_family, activate=False):
    text = conf_path.read_text() if conf_path.is_file() else ""
    lines = text.splitlines()
    result = []
    seen = set()
    font_value = f'"{font_family} 11"'
    stock_themes = {"", "default", "default-dark"}

    for line in lines:
        match = re.match(r"^\s*([A-Za-z0-9_ ]+?)\s*=\s*(.*?)\s*$", line)
        if not match or line.lstrip().startswith("#"):
            result.append(line)
            continue
        key, value = match[1].strip(), match[2].strip()
        if key in ("Font", "MenuFont"):
            result.append(f"{key}={font_value}")
            seen.add(key)
        elif key in ("Theme", "DarkTheme"):
            if activate or value in stock_themes:
                result.append(f"{key}=eitr")
            else:
                result.append(line)
            seen.add(key)
        else:
            result.append(line)

    for key in ("Theme", "DarkTheme"):
        if key not in seen:
            result.append(f"{key}=eitr")
    for key in ("Font", "MenuFont"):
        if key not in seen:
            result.append(f"{key}={font_value}")

    atomic_write(conf_path, "\n".join(result) + "\n")


def link_packaged_glyphs(theme_dir):
    packaged = Path(os.environ.get("EITR_FCITX5_PACKAGED_THEME") or "/usr/share/fcitx5/themes/default")
    if not packaged.is_dir():
        return
    for glyph in sorted(packaged.glob("*.svg")):
        target = theme_dir / glyph.name
        if target.is_symlink() and target.resolve() == glyph.resolve():
            continue
        if target.is_symlink() or not target.exists():
            target.unlink(missing_ok=True)
            target.symlink_to(glyph)


def reload_running_fcitx5():
    if os.environ.get("EITR_NO_SESSION") == "1":
        return
    if not shutil.which("busctl"):
        return
    running = subprocess.run(
        ["pgrep", "-u", str(os.getuid()), "-x", "fcitx5"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0
    if not running:
        return
    subprocess.run(
        ["busctl", "--user", "--auto-start=no", "call",
         "org.fcitx.Fcitx5", "/controller", "org.fcitx.Fcitx.Controller1",
         "ReloadAddonConfig", "s", "classicui"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=5,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activate", action="store_true", help="Point classicui Theme/DarkTheme at eitr")
    args = parser.parse_args(argv)

    palette_module = load_module("eitr_palette", HERE / "palette.py")
    fonts_module = load_module("eitr_fonts", HERE.parent / "actions/style/fonts.py")

    theme_dir_source = Path(os.environ.get("THEME_DIR") or (
        Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "theme/current"
    ))
    colors = palette_module.load(theme_dir_source)
    if not all(key in colors for key in ("foreground", "background", "accent")):
        return 0

    data_home = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    config_home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    target_dir = data_home / "fcitx5/themes/eitr"
    target_dir.mkdir(parents=True, exist_ok=True)
    atomic_write(target_dir / "theme.conf", render_theme(colors, palette_module))
    link_packaged_glyphs(target_dir)

    classicui_conf = config_home / "fcitx5/conf/classicui.conf"
    if args.activate or classicui_conf.exists() or shutil.which("fcitx5"):
        update_classicui(classicui_conf, fonts_module.current(), activate=args.activate)

    reload_running_fcitx5()
    return 0


if __name__ == "__main__":
    sys.exit(main())
