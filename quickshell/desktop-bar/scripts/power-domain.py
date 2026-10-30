"""Canonical battery capability, power reads and ordered helper actions."""
import importlib.util
from pathlib import Path
import threading


def system_batteries():
    import eitr_bootstrap
    from eitr_battery import system_batteries as read_batteries
    return read_batteries()


class PowerDomain:
    def __init__(self):
        self.adapters = {}
        self.lock = threading.Lock()
        self.batteries = None

    def read(self, topic):
        with self.lock:
            if self.batteries is None:
                self.batteries = system_batteries()
            name = {"power.battery": "battery", "power.profile": "power-profile", "power.radios": "airplane"}[topic]
            if name not in self.adapters:
                spec = importlib.util.spec_from_file_location("power_" + name.replace("-", "_"), Path(__file__).with_name(name + ".py"))
                adapter = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(adapter)
                self.adapters[name] = adapter
            adapter = self.adapters[name]
        if topic == "power.battery":
            return adapter.status(batteries=self.batteries)
        if topic == "power.profile":
            return adapter.status(battery_available=bool(self.batteries))
        return adapter.status()
