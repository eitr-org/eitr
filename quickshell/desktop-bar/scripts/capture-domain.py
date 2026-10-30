"""Lazily imported OBS read adapter; action control stays in the broker."""
import importlib.util
from pathlib import Path
import threading


class CaptureDomain:
    def __init__(self):
        self.adapter = None
        self.adapter_lock = threading.Lock()

    def read(self, topic):
        with self.adapter_lock:
            if self.adapter is None:
                spec = importlib.util.spec_from_file_location("capture_obs", Path(__file__).with_name("obs-control.py"))
                adapter = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(adapter)
                self.adapter = adapter
        if topic == "capture.options":
            return self.adapter.capture_options()
        return self.adapter.details() if topic == "capture.details" else self.adapter.status()
