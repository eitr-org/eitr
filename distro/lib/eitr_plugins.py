"""Public plugin API; validation, installation and execution have separate owners.

Owner modules resolve shared calls here so public overrides keep applying.
"""
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

import eitr_policy
from eitr_i18n import mark, tr
from eitr_paths import config, data, state

from eitr_plugin_manifest import (
    HOOK_EVENTS,
    SLUG,
    command,
    identifier,
    image_asset,
    manifest,
    object_keys,
    plugin_files,
    qml_files,
    repository_plugins,
    string,
    unique_object,
    validate_ui,
)
from eitr_plugin_runtime import (
    HOOK_TIMEOUT,
    UI_FAILURE_LIMIT,
    dispatch_hooks,
    unit_content,
    PluginRuntime as _PluginRuntime,
)
from eitr_plugin_install import (
    ALL_INSTALLED,
    ALREADY_INSTALLED,
    BLOCKLIST,
    COMMIT,
    OFFICIAL_REPOSITORY,
    REPORT_URL,
    SSH_SHORT,
    add_flags,
    binary_files,
    blocked_reason,
    blocklist,
    clone,
    commit,
    executable_files,
    git,
    live_flags,
    normalized_url,
    official,
    policy_reason,
    printable,
    repository_url,
    service_text,
    short_author,
    update_changes,
    PluginInstall as _PluginInstall,
)


class Plugins(_PluginInstall, _PluginRuntime):
    """Per-user approved installations and their runtime operations."""
