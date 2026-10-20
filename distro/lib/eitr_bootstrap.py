"""Expose Eitr's shared Python library to directly executed entrypoints."""
from pathlib import Path
import sys

LIBRARY = Path(__file__).resolve().parent
if str(LIBRARY) not in sys.path:
    sys.path.insert(0, str(LIBRARY))
