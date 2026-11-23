"""Install the package's Hardware default once, replacing external eitr-plugins Hardware in place and preserving later removal."""
from eitr_plugins import Plugins

Plugins().ensure_bundled()
