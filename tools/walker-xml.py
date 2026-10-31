#!/usr/bin/env python3
"""Generate Walker's provider row layouts from its two canonical XML files."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# These providers retain the single-line layout, including providers that used
# Walker's item.xml fallback. All other menus use the shared description row.
SINGLE_LINE_MENUS = frozenset({
    'apps', 'bar-appearance', 'bar-layout', 'bar-position', 'clipboard',
    'cursor-color', 'cursor-family', 'cursor-size', 'fonts', 'lockscreen',
    'projects-nvim', 'projects-vscode', 'search-index', 'system-shortcuts', 'theme-dark', 'theme-light', 'wallpaper',
})
# Keep externally addressable filenames even though their menus are retired.
COMPATIBILITY_MENUS = frozenset({'aws-development', 'aws-production'})
NATIVE_PROVIDERS = ('desktopapplications', 'providerlist', 'websearch')


def layouts(root):
    """Elephant discovers Lua menu files in elephant/menus (menus.toml)."""
    providers = {path.stem for path in (root / 'elephant/menus').glob('*.lua')}
    if not providers or not SINGLE_LINE_MENUS <= providers:
        raise ValueError('Menu sources missing or single-line menu classification is stale')
    result = {f'item_menus-{name}.xml': 'item.xml' if name in SINGLE_LINE_MENUS | COMPATIBILITY_MENUS
              else 'item_menus-main.xml' for name in (providers | COMPATIBILITY_MENUS) - {'workspaces'}}
    result.update({f'item_{name}.xml': 'item.xml' for name in NATIVE_PROVIDERS})
    return result


def generate(root=ROOT, check=False):
    directory = root / 'walker/themes/current'
    expected = layouts(root)
    templates = {name: (directory / name).read_bytes()
                 for name in {'item.xml', 'item_menus-main.xml'}}
    errors = []
    for name, template in sorted(expected.items()):
        target = directory / name
        if not target.is_file() or target.read_bytes() != templates[template]:
            if check:
                errors.append(f'{name}: missing or differs from {template}')
            else:
                target.write_bytes(templates[template])
    if not (directory / 'item_menus-workspaces.xml').is_file():
        errors.append('item_menus-workspaces.xml: missing custom workspace layout')
    actual = {path.name for path in directory.glob('item*.xml')}
    for name in sorted(actual - (set(expected) | set(templates) | {'item_menus-workspaces.xml'})):
        errors.append(f'{name}: unexpected row layout; classify its provider')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='validate without writing files')
    arguments = parser.parse_args()
    try:
        errors = generate(check=arguments.check)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    if errors:
        parser.exit(1, '\n'.join(errors) + '\nRun python3 tools/walker-xml.py to regenerate.\n')


if __name__ == '__main__':
    main()
