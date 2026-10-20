#!/usr/bin/env python3
"""Keep the native popup on the existing usage backend and shared cache."""
import json
from pathlib import Path
import subprocess
import sys
import importlib.util

spec = importlib.util.spec_from_file_location("ai_usage", Path(__file__).with_name("ai-usage.py"))
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)

CACHE = Path.home() / '.cache/desktop-ai-usage.json'

if len(sys.argv) > 1 and sys.argv[1] == 'cached':
    try:
        data = json.loads(CACHE.read_text())
    except (OSError, ValueError):
        data = {}
    available = backend.available_providers()
    previous = {provider["name"]: provider for provider in data.get("providers", [])}
    data["providers"] = [previous.get(name, {"name": name, "windows": []}) for name in available]
    print(json.dumps(data))
else:
    result = subprocess.run(['python3', str(Path(__file__).with_name('ai-usage.py'))],
                            capture_output=True, text=True, timeout=30, check=True)
    data = json.loads(result.stdout)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    temporary = CACHE.with_suffix('.tmp')
    temporary.write_text(json.dumps(data))
    temporary.replace(CACHE)
    print(json.dumps(data))
