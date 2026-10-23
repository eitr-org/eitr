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
import shutil
import time
import unicodedata
from datetime import datetime
from eitr_i18n import tr


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
    theme = text(current / "display-name", text(cache_home / "current-theme", "Default"))
    def custom(value):
        return {"type": "custom", "key": " ", "format": value}

    def border(title=None):
        if title is None:
            line = "└" + "─" * (width - 2) + "┘"
        else:
            heading = " " + title + " "
            remaining = width - 2 - cell_width(heading)
            line = "┌" + "─" * (remaining // 2) + heading + "─" * (remaining - remaining // 2) + "┐"
        return custom("{#2}" + line + "{#}")

    def row(kind, icon, label, tint, value=None, branch="├", **options):
        guide = "  " if not branch else branch + "─"
        key = "{#2}│{#} {#" + tint + "}" + guide + " " + icon + " " + label + ":{#} "
        module = {"type": kind, "key": key, **options}
        if value is not None:
            module["format"] = value
        return module

    logo = code("fastfetch/assets/eitr-logo.png")
    logo_source = terminal_logo(logo) if image and logo.exists() else None
    # Leave room for the existing 34-cell logo and its six cells of padding.
    width = min(76, max(38, shutil.get_terminal_size((120, 40)).columns - (40 if logo_source else 0)))
    hardware = color("color2", accent)
    software = color("color4", accent)
    clock = color("color3", accent)
    try:
        font = json.loads((config_home / "eitr/font.json").read_text()).get("family")
    except (OSError, ValueError, AttributeError):
        font = None
    release, separator, build = eitr_version().partition(" (")
    system = f"Eitr {release} on Arch Linux" + (f" ({build}" if separator else "")
    modules = [
        border(tr("Hardware")),
        row("host", "󰌢", tr("PC"), hardware, "{vendor} {name}", branch=""),
        row("cpu", "", "CPU", hardware, "{name}"),
        row("gpu", "󰢮", "GPU", hardware, "{name}"),
        row("memory", "", tr("Memory"), hardware, "{used} / {total} ({percentage})"),
        row("disk", "󰋊", tr("Disk"), hardware,
            "/: {size-used} / {size-total} ({size-percentage}) {filesystem}", branch="└", folders="/"),
        border(), "break", border(tr("Software")),
        row("custom", "", "OS", software, system, branch=""),
        row("kernel", "", tr("Kernel"), software),
        row("packages", "󰏖", tr("Packages"), software, "{pacman} (pacman), {flatpak-all} (flatpak)"),
        row("custom", "", tr("Shell"), software, Path(os.environ.get("SHELL", "/bin/sh")).name, branch="└"),
        row("lm", "󰍂", tr("Login"), software, branch=""),
        row("wm", "", "WM", software),
        row("terminal", "", tr("Terminal"), software),
        *([row("custom", "", tr("Font"), software, " ".join(font.split()))]
          if isinstance(font, str) and font.strip() else []),
        row("custom", "󰏘", tr("Theme"), software, theme, branch="└"),
        border(), "break", border(tr("Uptime / Age / Date")),
        row("custom", "󰃭", tr("OS age"), clock, os_age(), branch=""),
        row("uptime", "󰅐", tr("Uptime"), clock),
        row("datetime", "󰥔", tr("Date"), clock,
            "{year}-{month-pretty}-{day-pretty} {hour-pretty}:{minute-pretty}:{second-pretty}", branch="└"),
        border(),
        custom(" ".join("{#" + color(f"color{index}", foreground) + "}●{#}" for index in range(16))),
    ]
    return {
        "logo": {"type": "data", "source": logo_source,
                 "color": {"1": accent}, "padding": {"right": 4, "left": 2}}
                if logo_source else {"type": "none"},
        "display": {"separator": "", "showErrors": True, "color": {"keys": foreground},
                    "key": {"paddingLeft": 0}},
        "modules": modules,
    }


def os_age(root=Path("/"), log=Path("/var/log/pacman.log")):
    """Root birth time, falling back to the earliest timestamp in pacman's log."""
    try:
        result = subprocess.run(["stat", "-c", "%W", str(root)], capture_output=True,
                                text=True, check=False, timeout=2)
        installed = int(result.stdout.strip())
    except (OSError, ValueError, subprocess.TimeoutExpired):
        installed = 0
    if installed <= 0:
        installed = None
        try:
            with log.open() as entries:
                for entry in entries:
                    match = re.match(r"\[([^]]+)\]", entry)
                    if match:
                        try:
                            timestamp = datetime.fromisoformat(match[1]).timestamp()
                            installed = min(installed, timestamp) if installed is not None else timestamp
                        except ValueError:
                            continue
        except OSError:
            pass
    if installed is None or installed <= 0 or installed > time.time():
        return tr("Unavailable")
    return tr("{days} days", days=int((time.time() - installed) // 86400))


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def cell_width(value):
    return sum(0 if unicodedata.combining(character) else
               2 if unicodedata.east_asian_width(character) in ("W", "F") else 1
               for character in ANSI.sub("", value))


def fit_cells(value, width):
    """Preserve SGR colours while fitting terminal cells, including wide text."""
    truncated = cell_width(value) > width
    limit = width - 1 if truncated else width
    parts, used, position = [], 0, 0
    while position < len(value):
        escape = ANSI.match(value, position)
        if escape:
            parts.append(escape[0])
            position = escape.end()
            continue
        character = value[position]
        size = cell_width(character)
        if used + size > limit:
            break
        parts.append(character)
        used += size
        position += 1
    if truncated:
        parts.append("…")
        used += 1
    return "".join(parts) + "\x1b[0m" + " " * (width - used)


def align_boxes(output):
    """Fit Fastfetch's native module rows without changing its left-hand logo.
    Rows have no right border: icon widths differ between terminals, so a closing
    │ would not line up; long values are cut with … to the box width instead."""
    width = None
    lines = []
    for line in output.splitlines():
        if "┌" in line:
            width = cell_width(line[line.index("┌"):].rstrip())
        elif width and "│" in line:
            start = line.index("│")
            line = line[:start] + "\x1b[2m│\x1b[0m" + fit_cells(line[start + 1:].rstrip(), width - 2).rstrip()
        lines.append(line)
    return "\n".join(lines)


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
        rendered = align_boxes(result.stdout.strip("\n"))
        if not sys.stdout.isatty():
            rendered = ANSI.sub("", rendered)
        print("\n" + rendered + "\n", flush=True)
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
