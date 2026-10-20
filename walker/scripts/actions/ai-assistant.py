#!/usr/bin/env python3
"""Run an assistant through Eitr's shared first-use workflow."""
from pathlib import Path
import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
import json
from eitr_assistants import launch, assistants, executable, default_assistant, set_default, open_default, sync_themes

if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else ''
    if action == 'run' and len(sys.argv) > 2:
        sys.exit(launch(sys.argv[2], sys.argv[3:]))
    elif action == 'installed':
        print(json.dumps([{'id': identifier, 'label': metadata['label']}
                          for identifier, metadata in assistants().items() if executable(identifier)]))
    elif action == 'get':
        print(default_assistant())
    elif action == 'set' and len(sys.argv) == 4 and sys.argv[2] == 'assistant':
        set_default(sys.argv[3])
    elif action == 'theme':
        from eitr_paths import config
        sync_themes((config('theme/current') / 'light.mode').exists())
    elif action == 'open':
        open_default()
    else:
        sys.exit(2)
