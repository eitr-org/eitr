"""One observed sampler with session-local hardware identity, including failed GPU probes."""
import importlib.util
from pathlib import Path


class HardwareDomain:
    def __init__(self):
        spec = importlib.util.spec_from_file_location("hardware_details", Path(__file__).with_name("system-details.py"))
        self.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.adapter)
        self.identity = {}

    def read(self, topic):
        return self.adapter.snapshot(self.identity)
