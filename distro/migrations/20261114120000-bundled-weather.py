"""Install the package's Weather default once, preserving later removal."""
from eitr_plugins import Plugins

Plugins().ensure_bundled()
