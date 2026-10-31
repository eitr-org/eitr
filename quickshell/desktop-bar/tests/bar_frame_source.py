"""Adapt the frame dependencies to the existing isolated geometry stand-ins."""
from pathlib import Path
import re
import textwrap


def frame_source(directory):
    source = (Path(directory) / "BarWindow.qml").read_text()
    names = {
        'host': 'shell',
        'networkServiceRef': 'networkOwner',
        'notificationsRef': 'notificationsService',
        'remoteServiceRef': 'remoteAccessService',
        'dockClientsRef': 'dockClients',
        'idleLockProcessRef': 'toggleIdleLock',
    }
    source = source.replace("host: bar.host", "host: shell")
    return textwrap.indent(re.sub(r"\b(" + "|".join(names) + r")\b(?!\s*:)", lambda match: names[match[0]], source), " " * 12)
