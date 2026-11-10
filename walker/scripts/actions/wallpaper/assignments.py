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
    parser.add_argument('action', choices=['summary', 'preview', 'cancel', 'apply', 'clear'])
    parser.add_argument('--scope', choices=['global', 'monitor', 'workspace'], default='global')
    parser.add_argument('--monitor', default='')
    parser.add_argument('--number', type=int, default=0)
    parser.add_argument('--key', default='')
    parser.add_argument('--owner', default='')
    parser.add_argument('--path', default='')
    args = parser.parse_args()
    if args.action == 'summary':
        print(json.dumps(choices.summary(args.monitor)))
        return
    scope = args.key or choices.key(args.scope, args.monitor, args.number)
    path = str(Path(args.path).resolve(strict=True)) if args.path else ''
    if args.action == 'apply' and scope == 'global':
        choices.change('cancel', scope, '', args.owner)
        transition.apply(path)
    else:
        choices.change(args.action, scope, path, args.owner)
    defaults = transition.wallpapers(config('theme/current/backgrounds'))
    _, _, failures = choices.reconcile(vars(transition), str(defaults[0]) if defaults else '')
    if failures:
        raise RuntimeError(tr('hyprpaper failed on: {outputs}', outputs=', '.join(failures)))
    print(json.dumps(choices.summary(args.monitor)))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        sys.exit(str(error))
