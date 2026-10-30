"""Offline reader/action double for the NetworkService QML harness."""
import json
import os
from pathlib import Path
import sys
import time

kind = sys.argv[1] if len(sys.argv) > 1 else "qr"
with Path(os.environ["NETWORK_TEST_LOG"]).open("a") as output:
    output.write(kind + "\n")
if kind in ("connect", "power", "qr"):
    request = json.loads(sys.stdin.readline())
    if kind == "connect" and request.get("password") != "fixture-secret":
        raise ValueError("Missing fixture stdin credentials")
time.sleep(0.15)
fixtures = json.loads(Path(__file__).with_name("network.json").read_text())
result = fixtures["latency"] if kind == "probe" else fixtures["connected"]
if kind in ("connect", "power"):
    result = {"ok": True}
if kind == "qr":
    result = {"image": "fixture-image"}
print(json.dumps(result))
