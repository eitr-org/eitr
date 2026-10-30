"""Imported display readers; topology is retained for all display consumers."""
import eitr_bootstrap
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import threading


class DisplayDomain:
    def __init__(self):
        self.adapters = {}
        self.lock = threading.Lock()
        self.live = None

    def adapter(self, name):
        with self.lock:
            if name not in self.adapters:
                path = Path(__file__).with_name(name + '.py')
                if name == 'nightlight':
                    from eitr_paths import code
                    path = code('walker/scripts/actions/toggle/nightlight.py')
                spec = importlib.util.spec_from_file_location('display_' + name.replace('-', '_'), path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.adapters[name] = module
            return self.adapters[name]

    def read(self, topic):
        if topic == 'display.topology':
            primary = self.adapter('display-primary')
            live = json.loads(subprocess.run(["hyprctl", "monitors", "all", "-j"],
                                            capture_output=True, text=True, check=True, timeout=5).stdout)
            active = [monitor for monitor in live if not monitor.get("disabled", False)]
            preferred = primary.preferred_outputs()
            gaps = {}
            for key, option in [('windowGaps', 'in'), ('screenGaps', 'out')]:
                result = subprocess.run(['hyprctl', '-j', 'getoption', 'general:gaps_' + option],
                                        capture_output=True, text=True, check=True, timeout=5)
                values = [float(value) for value in json.loads(result.stdout)['css'].split()]
                if len(values) != 4 or any(value < 0 or not math.isfinite(value) for value in values):
                    raise ValueError('invalid-gaps')
                gaps[key] = values
            with self.lock:
                self.live = live
            return dict(monitors=active, primary=primary.choose_primary(active, primary.saved_primary(), preferred),
                        preferred=preferred, **gaps)
        if topic == 'display.settings':
            with self.lock:
                if self.live is None:
                    raise ValueError("topology-unavailable")
                live = list(self.live)
            return self.adapter('display-settings').list_settings(live)
        return self.adapter('brightness' if topic == 'display.brightness' else 'nightlight').status()
