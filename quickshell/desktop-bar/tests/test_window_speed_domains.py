"""Unit tests for WindowDomain, SpeedDomain, and bar-data.py query/cancel routing."""
import http.server
import importlib.util
import json
import os
from pathlib import Path
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


window_domain = load_module("window_domain", "window-domain.py")
speed_domain = load_module("speed_domain", "speed-domain.py")
bar_data = load_module("bar_data", "bar-data.py")


class FakeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/__down"):
            query = self.path.partition("bytes=")[2]
            size = int(query.split("&")[0]) if query else 0
            payload = b"x" * size
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith("/__up"):
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


class WindowDomainTests(unittest.TestCase):
    def test_info_by_address_and_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = Path(tmp) / "proc"
            (proc / "4242").mkdir(parents=True)
            (proc / "4242" / "comm").write_text("kitty\n")

            calls = []
            client = {
                "address": "0x55a1b2",
                "title": "zsh — kitty",
                "class": "kitty",
                "initialClass": "kitty",
                "pid": 4242,
                "workspace": {"id": 2, "name": "2"},
                "at": [100, 120],
                "size": [900, 600],
                "floating": False,
                "pinned": False,
                "fullscreen": 0,
            }

            def fake_run(cmd, **kwargs):
                calls.append(cmd)
                sub = cmd[1]
                if sub == "clients":
                    return subprocess.CompletedProcess(cmd, 0, json.dumps([client]), "")
                if sub == "workspaces":
                    return subprocess.CompletedProcess(cmd, 0, json.dumps([{"id": 2, "name": "2"}]), "")
                if sub == "activewindow":
                    return subprocess.CompletedProcess(cmd, 0, json.dumps(client), "")
                if sub == "eval":
                    if "window.float" in cmd[2]:
                        client["floating"] = not client["floating"]
                    elif "window.pin" in cmd[2]:
                        client["pinned"] = not client["pinned"]
                    elif "window.move" in cmd[2]:
                        client["workspace"] = {"id": 4, "name": "4"}
                    return subprocess.CompletedProcess(cmd, 0, "ok\n", "")
                raise AssertionError(f"Unexpected hyprctl command: {cmd}")

            domain = window_domain.WindowDomain(
                runner=fake_run,
                proc_root=proc,
                preferences_reader=lambda: {"workspaceCount": 5},
            )
            deadline = time.monotonic() + 10

            result = domain.query("info", {"address": "55A1B2"}, deadline)
            self.assertEqual(result["window"]["address"], "0x55a1b2")
            self.assertEqual(result["window"]["process"], "kitty")
            self.assertEqual(result["window"]["size"], [900, 600])
            self.assertEqual([w["id"] for w in result["workspaces"]], [1, 2, 3, 4, 5])

            floated = domain.query("float", {"address": "0x55a1b2"}, deadline)
            self.assertTrue(floated["window"]["floating"])
            self.assertIn("hl.dsp.window.float", calls[-3][2])

            pinned = domain.query("pin", {"address": "0x55a1b2"}, deadline)
            self.assertTrue(pinned["window"]["pinned"])

            moved = domain.query("move", {"address": "0x55a1b2", "workspace": 4}, deadline)
            self.assertEqual(moved["window"]["workspace"]["id"], 4)

            closed = domain.query("close", {"address": "0x55a1b2"}, deadline)
            self.assertTrue(closed["closed"])
            self.assertIsNone(closed["window"])

            # Empty address falls back to activewindow.
            fallback = domain.query("info", {"address": ""}, deadline)
            self.assertEqual(fallback["window"]["class"], "kitty")


class SpeedDomainTests(unittest.TestCase):
    def test_disk_speed_and_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            domain = speed_domain.SpeedDomain(cache_home=tmp)
            result = domain.query("disk", {"bytes": 2 * 1024 * 1024}, time.monotonic() + 10, threading.Event())
            self.assertEqual(result["kind"], "disk")
            self.assertGreater(result["writeMBps"], 0)
            self.assertGreater(result["readMBps"], 0)
            self.assertEqual(list((Path(tmp) / "eitr").glob("eitr-speed-*")), [])

    def test_disk_cancel_cleans_up_temp_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            domain = speed_domain.SpeedDomain(cache_home=tmp)
            cancelled = threading.Event()
            cancelled.set()
            with self.assertRaises(InterruptedError):
                domain.query("disk", {"bytes": 2 * 1024 * 1024}, time.monotonic() + 10, cancelled)
            self.assertEqual(list((Path(tmp) / "eitr").glob("eitr-speed-*")), [])

    def test_network_speed_against_fake_http_server(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), FakeHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ, {"no_proxy": "127.0.0.1,localhost", "NO_PROXY": "127.0.0.1,localhost"}):
                domain = speed_domain.SpeedDomain(base_url=f"http://127.0.0.1:{port}")
                result = domain.query(
                    "network",
                    {"downloadBytes": 262144, "uploadBytes": 131072},
                    time.monotonic() + 10,
                    threading.Event(),
                )
            self.assertEqual(result["kind"], "network")
            self.assertGreaterEqual(result["latencyMs"], 0)
            self.assertGreater(result["downloadMbps"], 0)
            self.assertGreater(result["uploadMbps"], 0)
        finally:
            server.shutdown()
            server.server_close()


class BrokerValidationTests(unittest.TestCase):
    def test_invalid_window_and_speed_queries_rejected(self):
        broker = bar_data.Broker(lambda frame: None)
        with self.assertRaises(ValueError):
            broker.request({"v": 1, "op": "query", "topic": "window", "name": "bogus", "args": {}, "id": "w1"})
        with self.assertRaises(ValueError):
            broker.request({"v": 1, "op": "query", "topic": "window", "name": "move", "args": {}, "id": "w2"})
        with self.assertRaises(ValueError):
            broker.request({"v": 1, "op": "query", "topic": "speed", "name": "cpu", "args": {}, "id": "s1"})


if __name__ == "__main__":
    unittest.main()
