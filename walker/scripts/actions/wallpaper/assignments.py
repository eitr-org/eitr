#!/usr/bin/env python3
"""Wallpaper picker commands; all renderers share eitr_wallpapers resolution."""
import argparse
import json
from pathlib import Path
import sys
import transition
from eitr_paths import config
from eitr_i18n import tr
import eitr_wallpapers as choices


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['summary', 'preview', 'cancel', 'apply', 'clear', 'per-display', 'current'])
    parser.add_argument('value', nargs='?', choices=['on', 'off'])
    parser.add_argument('--owner', default='')
    parser.add_argument('--path', default='')
    args = parser.parse_args()
    if args.action == 'summary':
        print(json.dumps(choices.summary()))
        return
    if args.action == 'current':
        monitor = choices.focused_monitor()
        selected = choices.resolve({'name': monitor}, choices.saved_global(), temporary={})
        for candidate in transition.wallpapers(config('theme/current/backgrounds')):
            if choices.canonical(str(candidate)) == selected:
                selected = str(candidate)
                break
        print(selected)
        return
    path = str(Path(args.path).resolve(strict=True)) if args.path else ''
    output = ''
    if args.action == 'per-display':
        if args.value is None:
            parser.error('per-display requires on or off')
        choices.set_per_display(args.value == 'on')
    elif args.action == 'clear':
        choices.clear_assignments()
        print(json.dumps(choices.summary()))
        return
    elif args.action == 'cancel':
        choices.change('cancel', '', '', args.owner)
    else:
        monitor = choices.target()
        output = monitor
        if args.action == 'apply' and not monitor:
            if choices.previewing(args.owner, path):
                # The picture is already on every display: save it, then drop the preview,
                # so the old wallpaper never shows in between.
                transition.commit(path)
                choices.change('cancel', '', '', args.owner)
                transition.dispatch_hooks('wallpaper-changed', EITR_WALLPAPER=path)
            else:
                choices.change('cancel', '', '', args.owner)
                transition.apply(path)
        else:
            choices.change(args.action, monitor, path, args.owner)
    defaults = transition.wallpapers(config('theme/current/backgrounds'))
    _, _, failures = choices.reconcile(vars(transition), str(defaults[0]) if defaults else '', output=output)
    if failures:
        raise RuntimeError(tr('hyprpaper failed on: {outputs}', outputs=', '.join(failures)))
    print(json.dumps(choices.summary()))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        sys.exit(str(error))
