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
    parser.add_argument('action', choices=['summary', 'preview', 'cancel', 'apply', 'clear', 'per-display', 'current', 'get', 'set'])
    parser.add_argument('value', nargs='*')
    parser.add_argument('--owner', default='')
    parser.add_argument('--path', default='')
    args = parser.parse_args()
    # Walker's choice menus ask "get per-display" and send "set per-display on|off".
    if args.action == 'get':
        if args.value != ['per-display']:
            parser.error('get takes per-display')
        print('on' if choices.per_display() else 'off')
        return
    if args.action == 'set':
        if args.value[:1] != ['per-display']:
            parser.error('set takes per-display on|off')
        args.action, args.value = 'per-display', args.value[1:]
    if args.action == 'per-display' and args.value not in (['on'], ['off']):
        parser.error('per-display requires on or off')
    if args.action != 'per-display' and args.value:
        parser.error('only per-display takes a value')
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
        choices.set_per_display(args.value == ['on'])
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
