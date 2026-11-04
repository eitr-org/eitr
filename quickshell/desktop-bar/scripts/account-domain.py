"""Observed account picture, shared with the standalone avatar helper."""
from pathlib import Path
import eitr_bootstrap
import eitr_avatar


class AccountDomain:
    def read(self, topic):
        result = eitr_avatar.status()
        try:
            result['version'] = Path(result['path']).stat().st_mtime_ns if result['path'] else 0
        except OSError:
            result['version'] = 0
        return result
