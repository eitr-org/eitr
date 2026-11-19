#!/usr/bin/env python3
"""Optional CJK input-method setup, profile seeding, and first-login offer (fcitx5)."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break

from eitr_i18n import mark, select_locale, tr  # noqa: E402
from eitr_paths import code, config, data, state  # noqa: E402

PRESETS = {
    "japanese": {
        "label": mark("Japanese (Mozc)"),
        "engine": "mozc",
        "locale": "ja",
        "packages": ["fcitx5", "fcitx5-gtk", "fcitx5-qt", "fcitx5-configtool", "fcitx5-mozc"],
        "layout": "",
    },
    "korean": {
        "label": mark("Korean (Hangul)"),
        "engine": "hangul",
        "locale": "ko",
        "packages": ["fcitx5", "fcitx5-gtk", "fcitx5-qt", "fcitx5-configtool", "fcitx5-hangul"],
        "layout": "us",
    },
    "chinese": {
        "label": mark("Chinese (Pinyin)"),
        "engine": "pinyin",
        "locale": "zh_CN",
        "packages": ["fcitx5", "fcitx5-gtk", "fcitx5-qt", "fcitx5-configtool", "fcitx5-chinese-addons"],
        "layout": "",
    },
}
LOCALE_TO_PRESET = {preset["locale"]: key for key, preset in PRESETS.items()}
NON_LATIN_LAYOUTS = frozenset(
    "af am ara bd bg by et ge gr il in iq ir kg kh kz la lk mk mm mn mv np rs ru sy th tj ua".split()
)


def is_installed():
    return bool(shutil.which("fcitx5"))


def packages_for(identifier):
    if not identifier:
        return []
    if identifier not in PRESETS:
        raise ValueError(f"Unknown input method: {identifier}")
    return list(PRESETS[identifier]["packages"])


def preset_for_locale(locale):
    return LOCALE_TO_PRESET.get(locale, "")


def atomic_write(path, content):
    """Write text atomically, following config symlinks and preserving permissions."""
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text() == content:
        return False
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd, temporary = tempfile.mkstemp(prefix=".eitr-im-", dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def primary_keyboard_layout(config_home=None):
    """First configured XKB layout/variant in fcitx5's naming, defaulting to us."""
    root = Path(config_home) if config_home is not None else config()
    source = root / "hypr/keyboard-layouts.lua"
    layout, variant = "us", ""
    if source.is_file():
        text = source.read_text()
        layout_match = re.search(r'layout\s*=\s*"([^"]*)"', text)
        variant_match = re.search(r'variant\s*=\s*"([^"]*)"', text)
        if layout_match and layout_match[1].strip():
            layout = layout_match[1].split(",")[0].strip() or "us"
        if variant_match:
            variant = variant_match[1].split(",")[0].strip()
    if layout in NON_LATIN_LAYOUTS:
        layout, variant = "us", ""
    combined = f"{layout}-{variant}" if variant else layout
    if not re.fullmatch(r"[A-Za-z0-9_-]+", combined):
        return "us"
    return combined


def engine_layout(identifier, group_layout):
    """Positional engines like Hangul keep US positions when paired with Dvorak/AZERTY."""
    override = PRESETS[identifier]["layout"]
    if not override or group_layout == override or group_layout.split("-")[0] in ("kr", "jp"):
        return ""
    return override


def is_stock_profile(text):
    """True when the profile is missing, empty, or fcitx5's untouched single keyboard-us."""
    if not text.strip():
        return True
    sections = {}
    current = ""
    for line in text.splitlines():
        header = re.match(r"^\s*\[([^]]+)\]\s*$", line)
        if header:
            current = header[1]
            sections.setdefault(current, {})
        elif current and "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            sections[current][key.strip()] = value.strip()
    group_keys = [key for key in sections if re.fullmatch(r"Groups/\d+", key)]
    item_keys = [key for key in sections if re.fullmatch(r"Groups/\d+/Items/\d+", key)]
    items = [sections[key].get("Name", "") for key in item_keys]
    group = sections.get("Groups/0", {})
    return (
        items == ["keyboard-us"]
        and group_keys == ["Groups/0"]
        and group.get("Name", "Default") == "Default"
        and group.get("Default Layout", "us") == "us"
        and not sections.get("Groups/0/Items/0", {}).get("Layout")
    )


def render_profile(group_layout, engine, engine_xkb_layout):
    return (
        "[Groups/0]\n"
        "Name=Default\n"
        f"Default Layout={group_layout}\n"
        f"DefaultIM={engine}\n\n"
        "[Groups/0/Items/0]\n"
        f"Name=keyboard-{group_layout}\n"
        "Layout=\n\n"
        "[Groups/0/Items/1]\n"
        f"Name={engine}\n"
        f"Layout={engine_xkb_layout}\n\n"
        "[GroupOrder]\n"
        "0=Default\n"
    )


def append_engine(text, engine, engine_xkb_layout):
    """Append an IM engine to Groups/0 without overwriting existing choices."""
    if re.search(rf"(?m)^Name\s*=\s*{re.escape(engine)}\s*$", text):
        return text
    indices = [int(match[1]) for match in re.finditer(r"(?m)^\[Groups/0/Items/(\d+)\]\s*$", text)]
    if not indices:
        return text
    next_index = max(indices) + 1
    block = f"\n[Groups/0/Items/{next_index}]\nName={engine}\nLayout={engine_xkb_layout}\n"
    order = re.search(r"(?m)^\[GroupOrder\]\s*$", text)
    if order:
        return text[:order.start()].rstrip() + "\n" + block + "\n" + text[order.start():]
    return text.rstrip() + "\n" + block


def seed_profile(identifier, config_home=None):
    """Write or update fcitx5 profile and Wayland-safe defaults without overriding Ctrl+Space."""
    if identifier not in PRESETS:
        raise ValueError(f"Unknown input method: {identifier}")
    root = Path(config_home) if config_home is not None else config()
    fcitx_dir = root / "fcitx5"
    group_layout = primary_keyboard_layout(root)
    engine = PRESETS[identifier]["engine"]
    engine_xkb = engine_layout(identifier, group_layout)

    profile = fcitx_dir / "profile"
    existing = profile.read_text() if profile.is_file() else ""
    if is_stock_profile(existing):
        atomic_write(profile, render_profile(group_layout, engine, engine_xkb))
    else:
        updated = append_engine(existing, engine, engine_xkb)
        if updated != existing:
            atomic_write(profile, updated)

    # Keep Latin typing active by default and leave Ctrl+Space as fcitx5's trigger.
    main_conf = fcitx_dir / "config"
    if not main_conf.exists():
        atomic_write(main_conf, "[Behavior]\nActiveByDefault=False\n")
    # Compositor XKB settings come from Hyprland; prevent fcitx5 addons from overriding them.
    for conf_name in ("conf/wayland.conf", "conf/xcb.conf"):
        target = fcitx_dir / conf_name
        if not target.exists():
            atomic_write(target, "Allow Overriding System XKB Settings=False\n")


def fcitx5_running():
    return subprocess.run(
        ["pgrep", "-u", str(os.getuid()), "-x", "fcitx5"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0


def stop_fcitx5(timeout=5.0):
    """Stop a running fcitx5 and wait: it saves its in-memory profile on exit, and a newly
    installed engine only loads at start, so the profile is updated between the two."""
    if not fcitx5_running():
        return False
    subprocess.run(["pkill", "-u", str(os.getuid()), "-x", "fcitx5"], check=False, timeout=5)
    deadline = time.monotonic() + timeout
    while fcitx5_running() and time.monotonic() < deadline:
        time.sleep(0.1)
    return True


def setup(identifier, config_home=None, data_home=None, start=True):
    """Configure profile, activate Eitr theme, and (re)start fcitx5 if in a session."""
    in_session = start and bool(os.environ.get("WAYLAND_DISPLAY")) and is_installed()
    if in_session:
        stop_fcitx5()
    seed_profile(identifier, config_home)
    env = dict(os.environ)
    if config_home is not None:
        env["XDG_CONFIG_HOME"] = str(config_home)
    if data_home is not None:
        env["XDG_DATA_HOME"] = str(data_home)
    generator = code("walker/scripts/themes/fcitx5.py")
    if generator.is_file():
        subprocess.run([sys.executable, str(generator), "--activate"], env=env, check=False, timeout=20)
    if not in_session:
        return
    launcher = code("walker/bin/app-launch")
    command = [str(launcher), "fcitx5", "-d"] if launcher.is_file() else ["fcitx5", "-d"]
    subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


def check_packages(packages):
    """Query pacman once for all packages; returns {package: bool}."""
    unique = list(dict.fromkeys(packages))
    if not unique or not shutil.which("pacman"):
        return {name: False for name in unique}
    result = subprocess.run(
        ["pacman", "-Q", "--", *unique],
        capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"}, timeout=10,
    )
    missing = set(re.findall(r"^error: package '([^']+)' was not found$", result.stderr, re.M))
    if result.returncode and not missing:
        return {name: False for name in unique}
    return {name: name not in missing for name in unique}


def summary(locale=None):
    active_locale = locale or select_locale()
    recommended = preset_for_locale(active_locale)
    all_packages = [pkg for preset in PRESETS.values() for pkg in preset["packages"]]
    installed_map = check_packages(all_packages)
    methods = []
    for identifier, preset in PRESETS.items():
        methods.append({
            "id": identifier,
            "label": tr(preset["label"]),
            "packages": list(preset["packages"]),
            "installed": all(installed_map.get(pkg, False) for pkg in preset["packages"]),
            "recommended": identifier == recommended,
        })
    return {
        "fcitx5Installed": is_installed(),
        "configtoolAvailable": bool(shutil.which("fcitx5-configtool")),
        "recommended": recommended,
        "methods": methods,
    }


def first_login_offer(locale=None, state_root=None):
    """Notify once when a CJK locale is active and its input method is not installed."""
    active_locale = locale or select_locale()
    preset_id = preset_for_locale(active_locale)
    if not preset_id:
        return {"offered": False, "reason": "locale"}
    info = summary(active_locale)
    method = next((item for item in info["methods"] if item["id"] == preset_id), None)
    if method and method["installed"]:
        return {"offered": False, "reason": "installed"}
    marker = (Path(state_root) / "eitr" if state_root else state("eitr")) / f"input-method-offered-{active_locale}"
    if marker.exists():
        return {"offered": False, "reason": "already-offered"}
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    if shutil.which("notify-send"):
        title = method["label"] if method else tr(PRESETS[preset_id]["label"])
        body = tr("Install {label} in Settings > Input or Install > Input Methods to type in this language.", label=title)
        subprocess.run(["notify-send", "--app-name=Eitr", title, body], check=False, timeout=5)
    return {"offered": True, "id": preset_id, "locale": active_locale}


def launch_configtool():
    if not shutil.which("fcitx5-configtool"):
        raise FileNotFoundError(tr("fcitx5-configtool is not installed"))
    launcher = code("walker/bin/app-launch")
    command = [str(launcher), "fcitx5-configtool"] if launcher.is_file() else ["fcitx5-configtool"]
    subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


def install_in_terminal(identifier):
    if identifier not in PRESETS:
        raise ValueError(f"Unknown input method: {identifier}")
    presenter = code("walker/scripts/actions/task-terminal.py")
    software = code("walker/scripts/actions/install/software.py")
    terminal = code("walker/bin/menu-path/kitty")
    subprocess.Popen(
        [str(terminal), "--class", "eitr-software", "-e", "python3", str(presenter),
         "python3", str(software), "recipe", "input-methods", identifier],
        start_new_session=True,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("summary")
    sub.add_parser("offer")
    sub.add_parser("configtool")
    seed_cmd = sub.add_parser("seed")
    seed_cmd.add_argument("id", choices=sorted(PRESETS))
    setup_cmd = sub.add_parser("setup")
    setup_cmd.add_argument("id", choices=sorted(PRESETS))
    install_cmd = sub.add_parser("install")
    install_cmd.add_argument("id", choices=sorted(PRESETS))
    args = parser.parse_args(argv)
    if args.command == "summary":
        print(json.dumps(summary()))
    elif args.command == "offer":
        print(json.dumps(first_login_offer()))
    elif args.command == "configtool":
        launch_configtool()
    elif args.command == "seed":
        seed_profile(args.id)
    elif args.command == "setup":
        setup(args.id)
    elif args.command == "install":
        install_in_terminal(args.id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
