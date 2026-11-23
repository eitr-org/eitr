"""Install the package's AI Usage default once, preserving later removal."""
from eitr_plugins import Plugins

Plugins().ensure_bundled()
