#!/usr/bin/env python3
"""Mode, HDR, scale, position and mirroring for each display.

  display-settings.py list               monitors and their saved settings, as JSON
  display-settings.py set NAME KEY VALUE apply a change and save it; a mode or HDR toggle is only tried
  display-settings.py keep               save the settings being tried
  display-settings.py revert             undo the settings being tried
  display-settings.py refresh-hdr        regenerate hardware-dependent rules without applying them
  display-settings.py edit               open ~/.config/hypr/local.lua, seeded with examples

KEY is hdr (on/off), sdr_brightness (1.0–2.0), mode (2560x1080@144), scale
(1.25), position or mirror (another output, or none). A position is either pixels (0x0) or SIDE:OTHER[:ALIGN], where SIDE is
left-of, right-of, above or below, and ALIGN is start, center or end along the
shared edge. That arrangement is saved, so when OTHER later changes resolution or
scale, the displays beside it move with it. Any number of displays can be
arranged this way; a change that would make two displays overlap is refused.

Saved settings live in the machine-local ~/.config/hypr/displays.json, and
displays.lua (generated from it) is loaded before ~/.config/hypr/local.lua, so
hand-written settings there still win. Position, scale and mirroring apply live
through hyprctl and are saved at once. A new resolution, refresh rate or HDR toggle
could leave a screen black, so it is only tried: unless kept, a systemd user timer that does
not depend on the bar undoes it after 15 s.
"""
import eitr_bootstrap
from eitr_i18n import tr
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

from eitr_paths import code
from eitr_app import app_command

DRM_ROOT = Path("/sys/class/drm")
HDR_ENV = ("PROTON_ENABLE_WAYLAND", "PROTON_ENABLE_HDR", "DXVK_HDR")

REVERT_SECONDS = 15
REVERT_UNIT = "eitr-display-revert"


def trial_file():
    return Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "eitr-display-trial.json"


def config_dir():
    base = os.environ.get("XDG_CONFIG_HOME", "")
    return (Path(base) if base.startswith("/") else Path.home() / ".config") / "hypr"


def monitors():
    return json.loads(subprocess.run(["hyprctl", "monitors", "all", "-j"], capture_output=True, text=True,
                                     check=True).stdout)


def edid_hdr(data):
    """Validate EDID blocks and inspect CTA HDR Static Metadata EOTFs."""
    if len(data) < 128 or data[:8] != b"\x00\xff\xff\xff\xff\xff\xff\x00":
        return False
    count = data[126] + 1
    if len(data) < count * 128 or any(sum(data[offset:offset + 128]) % 256
                                     for offset in range(0, count * 128, 128)):
        return False
    capable = False
    for offset in range(128, count * 128, 128):
        block = data[offset:offset + 128]
        if block[0] != 2:
            continue
        end = block[2]
        if end == 0:
            continue
        if not 4 <= end <= 127:
            return False
        cursor = 4
        while cursor < end:
            header = block[cursor]
            length = header & 31
            cursor += 1
            if cursor + length > end:
                return False
            if header >> 5 == 7 and length >= 3 and block[cursor] == 6 and block[cursor + 1] & 0x0c:
                capable = True
            cursor += length
    return capable


def hdr_capable(name):
    for connector in DRM_ROOT.glob("card*-*"):
        if connector.name.partition("-")[2] != name:
            continue
        try:
            if edid_hdr((connector / "edid").read_bytes()):
                return True
        except OSError:
            pass
    return False


def connected_hdr():
    for connector in DRM_ROOT.glob("card*-*"):
        try:
            if (connector / "status").read_text().strip() == "connected" and edid_hdr((connector / "edid").read_bytes()):
                return True
        except OSError:
            pass
    return False


def current(monitor):
    """A monitor's live settings in hl.monitor form."""
    mirror = monitor.get("mirrorOf") or "none"
    hdr = monitor.get("colorManagementPreset", "srgb").lower() in ("hdr", "hdredid")
    brightness = monitor.get("sdrBrightness", 1.0)
    if not hdr:
        brightness = saved().get(monitor.get("name"), {}).get("sdr_brightness", brightness)
    settings = {"mode": f"{monitor['width']}x{monitor['height']}@{monitor['refreshRate']:.2f}",
                "position": f"{monitor['x']}x{monitor['y']}", "scale": f"{monitor['scale']:g}",
                "mirror": None if mirror == "none" else mirror}
    # Only HDR monitors carry an HDR state, so SDR-only ones keep Hyprland's defaults.
    if hdr or hdr_capable(monitor.get("name", "")):
        settings.update(hdr=hdr, sdr_brightness=brightness)
    return settings


SIDES = ("left-of", "right-of", "above", "below")
ALIGNS = ("start", "center", "end")


def parse_anchor(value):
    """'right-of:DP-3' or 'right-of:DP-3:center' as an anchor; None for pixel positions."""
    side, _, rest = value.partition(":")
    if side not in SIDES:
        if "x" not in value:
            raise ValueError(tr('Unknown position {value}', value=value))
        return None
    other, _, align = rest.partition(":")
    align = align or "start"
    if not other or align not in ALIGNS:
        raise ValueError(tr('Unknown position {value}', value=value))
    return {"side": side, "of": other, "align": align}


def mode_size(settings, monitor):
    """Logical width and height of a monitor with these settings."""
    width, height = (int(part) for part in settings["mode"].split("@")[0].split("x"))
    if monitor.get("transform", 0) % 2:
        width, height = height, width
    scale = float(settings["scale"])
    return width / scale, height / scale


def beside(anchor, size, other_position, other_size):
    """Pixel position of a display of SIZE placed by ANCHOR next to the other display."""
    (width, height), (other_x, other_y), (other_width, other_height) = size, other_position, other_size
    share = {"start": 0, "center": 0.5, "end": 1}[anchor["align"]]
    if anchor["side"] in ("left-of", "right-of"):
        x = other_x - width if anchor["side"] == "left-of" else other_x + other_width
        y = other_y + (other_height - height) * share
    else:
        y = other_y - height if anchor["side"] == "above" else other_y + other_height
        x = other_x + (other_width - width) * share
    return round(x), round(y)


def pixels(position):
    x, y = position.split("x")
    return int(x), int(y)


def chain(name, anchors):
    """The displays NAME is placed beside, nearest first."""
    seen = []
    while name in anchors and anchors[name]["of"] not in seen and anchors[name]["of"] != name:
        name = anchors[name]["of"]
        seen.append(name)
    return seen


def arrange(settings, anchors, live):
    """Place every anchored display beside its target, targets first; others keep their position."""
    by_name = {monitor["name"]: monitor for monitor in live}
    placed = {}

    def place(name):
        if name not in placed:
            anchor = anchors.get(name)
            if anchor and anchor["of"] in by_name and not settings[name].get("mirror"):
                other = place(anchor["of"])
                size = mode_size(settings[name], by_name[name])
                other_size = mode_size(settings[anchor["of"]], by_name[anchor["of"]])
                settings[name]["position"] = "{}x{}".format(*beside(anchor, size, pixels(other), other_size))
            placed[name] = settings[name]["position"]
        return placed[name]

    for name in settings:
        place(name)
    check_overlaps(settings, live)


def normalize(settings):
    """Shift the layout so it starts at 0x0; mirrored displays have no position of their own."""
    placed = [pixels(values["position"]) for values in settings.values() if not values.get("mirror")]
    if not placed:
        return
    left, top = min(x for x, _ in placed), min(y for _, y in placed)
    for values in settings.values():
        if not values.get("mirror"):
            x, y = pixels(values["position"])
            values["position"] = f"{x - left}x{y - top}"


def check_overlaps(settings, live):
    boxes = []
    for monitor in live:
        values = settings[monitor["name"]]
        if values.get("mirror"):
            continue
        (x, y), (width, height) = pixels(values["position"]), mode_size(values, monitor)
        for other, (other_x, other_y, other_width, other_height) in boxes:
            if x < other_x + other_width and other_x < x + width and y < other_y + other_height and other_y < y + height:
                raise ValueError(tr('{display} would overlap {other}', display=monitor['name'], other=other))
        boxes.append((monitor["name"], (x, y, width, height)))


def lua_call(name, settings):
    fields = [f'output = "{name}"', f'mode = "{settings["mode"]}"', f'position = "{settings["position"]}"',
              f'scale = {settings["scale"]}']
    if settings.get("mirror"):
        fields.append(f'mirror = "{settings["mirror"]}"')
    # hdredid takes the monitor's own peak and black levels from its EDID, so games
    # tone-map to what the panel can show. Off is written out: Hyprland keeps the
    # previous preset when the fields are missing.
    if settings.get("hdr"):
        fields += ['cm = "hdredid"', 'bitdepth = 10', f'sdrbrightness = {float(settings.get("sdr_brightness", 1)):g}']
    elif settings.get("hdr") is False:
        fields += ['cm = "srgb"', 'bitdepth = 8']
    return "hl.monitor({ " + ", ".join(fields) + " })"


def apply(name, settings):
    subprocess.run(["hyprctl", "eval", lua_call(name, settings)], capture_output=True, text=True, check=True)


PARKING_GAP = 20000


def apply_all(settings, previous=None):
    """Give every display an explicit rule. A display left on the generic automatic position
    would be moved by Hyprland whenever another one changes. Unchanged displays go first.

    Rules apply one display at a time, so when several displays move, one could land on
    another that has not moved yet; Hyprland reports that as an overlapping layout. Those
    displays are parked far to the right first, then placed."""
    previous = previous or {}
    moving = [name for name in settings if not settings[name].get("mirror")
              and settings[name]["position"] != previous.get(name, {}).get("position")]
    if len(moving) > 1:
        edges = [pixels(values["position"])[0] for values in list(settings.values()) + list(previous.values())
                 if values.get("position") and not values.get("mirror")]
        parking = max(edges, default=0) + PARKING_GAP
        for index, name in enumerate(moving):
            apply(name, dict(settings[name], position=f"{parking + index * PARKING_GAP}x0"))
    for name in sorted(settings, key=lambda display: settings[display] != previous.get(display)):
        apply(name, settings[name])
    subprocess.run(["python3", str(Path(__file__).with_name("display-primary.py")), "refresh-walker"],
                   check=True)


def saved():
    try:
        data = json.loads((config_dir() / "displays.json").read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(settings):
    directory = config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "displays.json").write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n")
    write_generated(settings)


def write_generated(settings):
    directory = config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    lines = ["-- Generated by Eitr's display settings from displays.json; edit them there or in the",
             "-- Display panel. local.lua is loaded after this file, so its monitors win."]
    if connected_hdr():
        lines += [f'hl.env("{variable}", "1", true)' for variable in HDR_ENV]
    lines += [lua_call(name, values) for name, values in sorted(settings.items())]
    (directory / "displays.lua").write_text("\n".join(lines) + "\n")


def main_display(live):
    """The display that hosts the bar (display-primary.py owns that choice); others are placed around it."""
    spec = importlib.util.spec_from_file_location("eitr_display_primary", Path(__file__).with_name("display-primary.py"))
    primary = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(primary)
    return primary.choose_primary(live, primary.saved_primary(), primary.preferred_outputs())


def saved_anchors(live):
    """Saved arrangements of the connected displays, with targets that are still connected."""
    names = {monitor["name"] for monitor in live}
    return {name: values["anchor"] for name, values in saved().items()
            if name in names and isinstance(values, dict) and isinstance(values.get("anchor"), dict)
            and values["anchor"].get("of") in names}


def set_setting(name, key, value):
    if key not in ("mode", "scale", "position", "mirror", "hdr", "sdr_brightness"):
        raise ValueError(tr('Unknown setting {key}', key=key))
    if trial_file().exists():
        revert()
    live = monitors()
    if name not in {monitor["name"] for monitor in live}:
        raise ValueError(tr('No display named {name}', name=name))
    before = {monitor["name"]: current(monitor) for monitor in live}
    after = {display: dict(values) for display, values in before.items()}
    anchors = saved_anchors(live)
    main = main_display(live)
    anchors.pop(main, None)
    if key == "position" and name == main:
        raise ValueError(tr('The main display stays where it is; place the other displays around it.'))
    if key == "position":
        anchor = parse_anchor(value)
        if anchor is None:
            pixels(value)
            after[name]["position"] = value
            anchors.pop(name, None)
        else:
            if anchor["of"] not in before or anchor["of"] == name:
                raise ValueError(tr('No other display named {value}', value=anchor['of']))
            anchors[name] = anchor
            # When the target sits beside this display (directly or through others), the link
            # back to this display is dropped, so that display keeps its current place.
            path = [anchor["of"]] + chain(anchor["of"], anchors)
            if name in path:
                anchors.pop(path[path.index(name) - 1])
    elif key == "hdr":
        if value not in ("on", "off"):
            raise ValueError(tr('Unknown HDR value {value}', value=value))
        if value == "on" and not hdr_capable(name):
            raise ValueError(tr('This display does not report HDR support.'))
        after[name]["hdr"] = value == "on"
    elif key == "sdr_brightness":
        brightness = float(value)
        if not math.isfinite(brightness) or not 1 <= brightness <= 2:
            raise ValueError(tr('SDR content brightness must be between 1 and 2.'))
        after[name][key] = brightness
    elif key == "mirror":
        value = None if value == "none" else value
        if value is not None and value not in {display for display in before if display != name}:
            raise ValueError(tr('No other display named {value}', value=value))
        after[name]["mirror"] = value
    else:
        if key == "scale":
            float(value)
        after[name][key] = value
    arrange(after, anchors, live)
    normalize(after)
    if key in ("mode", "hdr"):
        trial_file().write_text(json.dumps({"before": before, "after": after, "anchors": anchors}) + "\n")
        subprocess.run(["systemctl", "--user", "stop", f"{REVERT_UNIT}.timer"], capture_output=True)
        subprocess.run(["systemd-run", "--user", "--quiet", f"--unit={REVERT_UNIT}", f"--on-active={REVERT_SECONDS}s",
                        "--timer-property=AccuracySec=1s", "python3", str(Path(__file__).resolve()), "revert"], check=True)
        apply_all(after, before)
        return dict(after[name], trial=True)
    apply_all(after, before)
    store(after, anchors)
    return after[name]


def store(after, anchors):
    settings = saved()
    # Every connected display is saved with an explicit position, so the layout comes back
    # the same after a reboot instead of Hyprland placing the others automatically.
    for display, values in after.items():
        settings[display] = dict(values, **({"anchor": anchors[display]} if display in anchors else {}))
    save(settings)


def keep():
    try:
        trial = json.loads(trial_file().read_text())
    except (OSError, ValueError):
        return False
    subprocess.run(["systemctl", "--user", "stop", f"{REVERT_UNIT}.timer"], capture_output=True)
    store(trial.get("after", {}), trial.get("anchors", {}))
    trial_file().unlink(missing_ok=True)
    return True


def revert():
    try:
        trial = json.loads(trial_file().read_text())
    except (OSError, ValueError):
        return False
    trial_file().unlink(missing_ok=True)
    subprocess.run(["systemctl", "--user", "stop", f"{REVERT_UNIT}.timer"], capture_output=True)
    apply_all(trial.get("before", {}), trial.get("after", {}))
    return True


def edit():
    """Open local.lua for hand-written layouts, seeded with commented examples when it is new."""
    local = config_dir() / "local.lua"
    if not local.exists():
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(code("hypr/local.lua.template").read_text())
    command = ["code", str(local)] if shutil.which("code") else ["--terminal", "--directory", str(local.parent), "nvim", str(local)]
    subprocess.Popen(app_command(command), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)


def main(argv):
    if argv == ["refresh-hdr"]:
        write_generated(saved())
        return 0
    if argv == ["list"]:
        live = monitors()
        write_generated(saved())
        anchors = saved_anchors(live)
        main = main_display(live)
        anchors.pop(main, None)
        print(json.dumps({"main": main, "monitors": [{**current(monitor), "name": monitor["name"], "anchor": anchors.get(monitor["name"]),
                                        "hdr_capable": hdr_capable(monitor["name"]), "modes": monitor["availableModes"]} for monitor in live],
                          "saved": saved()}))
        return 0
    if len(argv) == 4 and argv[0] == "set":
        print(json.dumps(set_setting(*argv[1:])))
        return 0
    if argv == ["keep"]:
        return 0 if keep() else 1
    if argv == ["revert"]:
        return 0 if revert() else 1
    if argv == ["edit"]:
        edit()
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (ValueError, subprocess.SubprocessError, OSError) as error:
        sys.exit(f"display-settings: {error}")
