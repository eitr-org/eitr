"""How fast this computer is downloading and uploading, for Settings > Overview: the kernel's
byte counters of the physical network adapters (wired and WiFi; not loopback, containers or
VPN tunnels, whose traffic also crosses an adapter), turned into bytes per second from the
difference since the previous read. The first read after a pause has nothing to compare
with, so it reports no speed yet."""
from pathlib import Path
import threading
import time

NET = Path('/sys/class/net')


def counters(root=NET):
    """{interface: (received, sent)} in bytes for every adapter backed by a device."""
    found = {}
    for interface in root.iterdir() if root.is_dir() else ():
        if not (interface / 'device').exists():
            continue
        try:
            found[interface.name] = tuple(int((interface / 'statistics' / name).read_text())
                                          for name in ('rx_bytes', 'tx_bytes'))
        except (OSError, ValueError):
            continue
    return found


class ThroughputDomain:
    # A previous read older than this is not compared with: the speed would be an average
    # over the time no one was looking.
    STALE = 10

    def __init__(self, root=NET, clock=time.monotonic):
        self.root = root
        self.clock = clock
        self.lock = threading.Lock()
        self.previous = None

    def read(self, topic):
        with self.lock:
            now, current = self.clock(), counters(self.root)
            previous, self.previous = self.previous, (now, current)
        result = dict(download=None, upload=None, interfaces=sorted(current))
        if previous and 0 < now - previous[0] <= self.STALE:
            elapsed = now - previous[0]
            # Only adapters present both times; a counter that went back (a driver reset) counts as zero.
            shared = current.keys() & previous[1].keys()
            result['download'] = sum(max(0, current[name][0] - previous[1][name][0]) for name in shared) / elapsed
            result['upload'] = sum(max(0, current[name][1] - previous[1][name][1]) for name in shared) / elapsed
        return result
