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
    # Reconcile cached account IDs, including new/deleted accounts, without a request.
    previous = {provider["name"]: provider for provider in data.get("providers", [])}
    labels = {"claude": "Claude", "codex": "Codex", "gemini": "Gemini CLI",
              "grok": "Grok", "copilot": "Copilot", "agy": "Antigravity"}
    providers = {}
    for identifier, account in backend.usage_accounts():
        name = labels[identifier]
        cached_accounts = {entry.get("id"): entry for entry in previous.get(name, {}).get("accounts", [])}
        entry = dict(cached_accounts.get(account["id"], {"windows": [], "error": backend.tr('No data')}))
        entry.update(id=account["id"], label=account["label"])
        providers.setdefault(name, {"name": name, "accounts": []})["accounts"].append(entry)
    data["providers"] = list(providers.values())
    print(json.dumps(data))
else:
    result = subprocess.run(['python3', str(Path(__file__).with_name('ai-usage.py'))],
                            capture_output=True, text=True,
                            timeout=max(30, 25 * ((len(backend.usage_accounts()) + 5) // 6)), check=True)
    data = json.loads(result.stdout)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    temporary = CACHE.with_suffix('.tmp')
    import os
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        os.fchmod(output.fileno(), 0o600)
        output.write(json.dumps(data))
    temporary.replace(CACHE)
    print(json.dumps(data))
