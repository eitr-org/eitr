"""Read-only remote access adapter shared with the standalone CLI."""
import importlib.util
from pathlib import Path


class RemoteDomain:
    def __init__(self):
        spec = importlib.util.spec_from_file_location("remote_status", Path(__file__).with_name("remote-status.py"))
        self.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.adapter)

    def read(self, topic):
        if topic == "remote.availability":
            from eitr_policy import allowed
            return {"allowed": allowed("remote_access")}
        return self.adapter.status()
