"""Keep tests that fake the home folder away from the real one.

A desktop session exports XDG_CONFIG_HOME, XDG_CACHE_HOME and friends, and
eitr_paths prefers them over Path.home(). A test run outside tools/check.sh
would then write its fixtures into the owner's real config and cache, for
example pointing the saved wallpaper at a deleted temporary image. Import
setUpModule and tearDownModule from here in any test module that patches
Path.home().
"""
import os
from unittest.mock import patch

_XDG_FOLDERS = patch.dict(os.environ, {name: "" for name in (
    "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_DATA_HOME")})


def setUpModule():
    _XDG_FOLDERS.start()


def tearDownModule():
    _XDG_FOLDERS.stop()
