"""Resolve production type paths for tests that enumerate QML names."""
from pathlib import Path


def qml_path(filename):
    registry = Path(__file__).resolve().parents[1] / "qmldir"
    for line in registry.read_text().splitlines():
        fields = line.split()
        if fields and Path(fields[-1]).name == filename:
            return fields[-1]
    raise ValueError(f"Unregistered QML component: {filename}")
