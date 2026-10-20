#!/usr/bin/env python3
"""Create a WiFi sharing image in memory; never save passwords or QR files."""
import eitr_bootstrap
from eitr_i18n import tr
import base64
import json
import subprocess
import sys


def escape(value):
    return "".join("\\" + char if char in '\\;,:"' else char for char in value)


def payload(network, password):
    kind = network.get("type")
    if kind not in ("open", "psk"):
        raise ValueError(tr('Sharing this network security type is not supported'))
    if kind == "psk" and not password:
        raise ValueError(tr('Enter the WiFi password'))
    auth = "nopass" if kind == "open" else "WPA"
    return f"WIFI:T:{auth};S:{escape(network['name'])};P:{escape(password)};;"


if __name__ == "__main__":
    try:
        request = json.loads(sys.stdin.readline())
        png = subprocess.check_output(["qrencode", "-t", "PNG", "-s", "8", "-m", "4", "-o", "-"],
                                      input=payload(request["network"], request.get("password", "")).encode(), timeout=5)
        print(json.dumps({"image": "data:image/png;base64," + base64.b64encode(png).decode()}))
    except Exception as error:
        print(json.dumps({"error": str(error) if isinstance(error, ValueError) else "Could not generate QR code"}))
