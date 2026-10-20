#!/usr/bin/env python3
"""Show the CPU temperature on a liquid cooler's two-digit display.

Supports the USB "temperature display" HID device aa88:8666 (东莞铭研电子科技 /
Dongguan Mingyan), found on several AIO pumps. It shows whatever it receives:
a 10-byte output report whose first byte is the temperature in °C (0-99). It
sends nothing back and holds the last value, so `run` refreshes it every two
seconds. The owner's machine only; see README.md here.
"""
import argparse
import os
from pathlib import Path
import sys
import time

HID_ID = "0000AA88:00008666"
# CPU package sensors: Intel coretemp, then AMD k10temp/zenpower.
CPU_SENSORS = ("Package id 0", "Tctl", "Tdie")
INTERVAL = 2
HIDRAW = Path("/sys/class/hidraw")
HWMON = Path("/sys/class/hwmon")


def find_display(hidraw=HIDRAW):
    """The display's /dev path, or None when it is not connected."""
    if not hidraw.is_dir():
        return None
    for node in sorted(hidraw.iterdir()):
        try:
            if f"HID_ID=0003:{HID_ID}" in (node / "device/uevent").read_text():
                return Path("/dev") / node.name
        except OSError:
            continue
    return None


def cpu_temperature(hwmon=HWMON):
    """The CPU package temperature in °C, or None when no known sensor exists."""
    readings = {}
    for label in sorted(hwmon.glob("hwmon*/temp*_label")):
        try:
            name = label.read_text().strip()
            if name in CPU_SENSORS and name not in readings:
                readings[name] = int(label.with_name(label.name.replace("_label", "_input")).read_text()) / 1000
        except (OSError, ValueError):
            continue
    for name in CPU_SENSORS:
        if name in readings:
            return readings[name]
    return None


def report(celsius):
    """The output report: report ID 0 (the device has none), then the 10-byte payload."""
    value = max(0, min(99, round(celsius)))
    return bytes([0, value] + [0] * 9)


def run():
    """Keep the display on the CPU temperature; wait while it is unplugged."""
    descriptor = None
    while True:
        if descriptor is None:
            path = find_display()
            if path is not None:
                try:
                    descriptor = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
                except OSError as error:
                    print(f"Cannot open {path}: {error}", file=sys.stderr, flush=True)
        celsius = cpu_temperature()
        if descriptor is not None and celsius is not None:
            try:
                os.write(descriptor, report(celsius))
            except OSError:
                os.close(descriptor)
                descriptor = None
        time.sleep(INTERVAL if descriptor is not None else 5)


def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["run", "status"],
                        help="run: refresh the display until stopped; status: show the device and reading")
    args = parser.parse_args(arguments)
    if args.command == "run":
        run()
    else:
        print(f"Display: {find_display() or 'not connected'}; CPU: {cpu_temperature()} °C")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
