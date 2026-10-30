#!/usr/bin/env python3
"""Standalone popup API sharing the broker's cache implementation."""
import importlib.util
import json
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location('ai_domain', Path(__file__).with_name('ai-domain.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if __name__ == '__main__':
    adapter = module.AiDomain()
    data = adapter.cached() if len(sys.argv) > 1 and sys.argv[1] == 'cached' else adapter.save(adapter.backend.collect())
    print(json.dumps(data))
