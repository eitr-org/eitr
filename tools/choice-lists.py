#!/usr/bin/env python3
"""Generate fixed choice projections; --check also verifies docs and shipped designs."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'tools/choice-lists.json'


def load_catalog(path=CATALOG):
    catalog = json.loads(path.read_text())
    for group in ('workspace_styles', 'lockscreen_designs'):
        rows = catalog[group]
        fields = {'id', 'label', 'handbook_labels'} if group == 'workspace_styles' else {'id', 'label'}
        if not rows or any(set(row) != fields or
                           any(not isinstance(row[key], str) or not row[key] for key in ('id', 'label'))
                           for row in rows):
            raise ValueError(f'Invalid {group} rows')
        if group == 'workspace_styles':
            for row in rows:
                translations = row['handbook_labels']
                if (not isinstance(translations, dict) or set(translations) != {'de', 'es', 'fr', 'pt_BR'} or
                        any(not isinstance(label, str) or not label for label in translations.values())):
                    raise ValueError('Invalid workspace Handbook labels')
        if len({row['id'] for row in rows}) != len(rows):
            raise ValueError(f'Duplicate {group} ids')
        if rows != sorted(rows, key=lambda row: row['label'].casefold()):
            raise ValueError(f'{group} must be alphabetical by label')
    return catalog


def projections(catalog):
    styles = [row['id'] for row in catalog['workspace_styles']]
    names = {row['id']: row['label'] for row in catalog['lockscreen_designs']}
    bar = 'quickshell/desktop-bar/'
    for name, prefix in (('panels/WorkspaceStyleMenu.qml', 'readonly property var styles: '),
                         ('panels/ControlCenterStyle.qml', 'Repeater { model: '),
                         ('handbook-controls-preview.qml', 'model: ')):
        pattern = re.escape(prefix) + r'\[[^\]\n]*\]'
        if name == 'panels/ControlCenterStyle.qml':
            pattern += r'(?=\s+PanelButton \{\s+textSize: 12; iconSize: 16\s+id: workspaceChoice)'
        yield bar + name, pattern, prefix + json.dumps(styles)
    yield 'elephant/menus/workspaces.lua', r'local choices = \{[^\n]*\}', 'local choices = {' + ', '.join(json.dumps(style) for style in styles) + '}'
    yield bar + 'scripts/workspace-style.py', r'^STYLES = [^\n]*$', 'STYLES = ' + repr(tuple(styles))
    yield bar + 'scripts/workspace-color.py', r'^if style not in [^\n]*:$', 'if style not in ' + repr(tuple(styles)) + ':'
    yield 'quickshell/lockscreen/scripts/settings.py', r'^NAMES = \{.*?^\}', 'NAMES = {\n' + ''.join(f'    {identifier!r}: {label!r},\n' for identifier, label in names.items()) + '}'
    gallery = '[\n' + ',\n'.join('        {id: ' + json.dumps(identifier) + ', title: Eitr.I18n.tr(' + json.dumps(label, ensure_ascii=False) + ')}' for identifier, label in names.items()) + '\n    ]'
    yield 'quickshell/lockscreen/design-gallery.qml', r'(?<=readonly property var designs: )\[.*?^    \]', gallery


def check_documentation(catalog, root=ROOT):
    errors = []
    labels = [row['label'].replace(' · ', ' ') for row in catalog['lockscreen_designs']]
    documents = [root / 'quickshell/lockscreen/README.md', *sorted((root / 'quickshell/desktop-bar/handbook/content').rglob('appearance.md'))]
    for path in documents:
        text = ' '.join(path.read_text().split())
        start = text.find(labels[0])
        end = text.find(labels[-1], start)
        enumeration = text[start:end + len(labels[-1])] if start >= 0 and end >= 0 else ''
        pattern = r'(?:,?\s+(?:and|und|et|y|e)\s+|,\s*)'.join(re.escape(label) for label in labels)
        if not re.fullmatch(pattern, enumeration):
            errors.append(f'{path.relative_to(root)}: stale or unordered design enumeration')
        # English count mentions are checked wherever the full list is documented.
        for count in re.findall(r'\b(\w+) (?:shipped (?:EITR )?designs|designs\.)', text):
            words = dict(enumerate(('zero', 'one', 'two', 'three', 'four', 'five',
                                    'six', 'seven', 'eight', 'nine', 'ten', 'eleven',
                                    'twelve', 'thirteen', 'fourteen', 'fifteen',
                                    'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty')))
            if count not in (str(len(labels)), words.get(len(labels))):
                errors.append(f'{path.relative_to(root)}: stale design count {count}')
    localized_counts = {
        'de': (r'Vergleiche die (\w+) Designs', {9: 'neun'}),
        'es': (r'Compara los (\w+) diseños', {9: 'nueve'}),
        'fr': (r'Comparez les (\w+) modèles', {9: 'neuf'}),
        'pt_BR': (r'Compare os (\w+) desenhos', {9: 'nove'}),
    }
    for locale, (pattern, words) in localized_counts.items():
        path = root / f'quickshell/desktop-bar/handbook/content/{locale}/appearance.md'
        counts = re.findall(pattern, path.read_text())
        if len(counts) != 1 or counts[0] not in (str(len(labels)), words.get(len(labels))):
            errors.append(f'{path.relative_to(root)}: stale or missing design count')
    for path in sorted((root / 'quickshell/desktop-bar/handbook/content').rglob('desktop-bar.md')):
        locale = path.parent.name
        choices = [row.get('handbook_labels', {}).get(locale, row['label'])
                   for row in catalog['workspace_styles']]
        pattern = r'(?:,?\s+(?:or|oder|o|ou)\s+|,\s*)'.join(re.escape(label) for label in choices)
        text = ' '.join(path.read_text().split())
        if not re.search(pattern, text):
            errors.append(f'{path.relative_to(root)}: stale workspace styles')
    text = (root / 'quickshell/desktop-bar/README.md').read_text()
    expected = ', '.join(row['label'] for row in catalog['workspace_styles'][:-1]) + ' or ' + catalog['workspace_styles'][-1]['label']
    if expected not in text:
        errors.append('desktop-bar/README.md: stale workspace styles')
    actual = {str(path.parent.relative_to(root / 'quickshell/lockscreen/themes')) for path in (root / 'quickshell/lockscreen/themes').rglob('Main.qml')}
    if actual != {row['id'] for row in catalog['lockscreen_designs']}:
        errors.append('Lockscreen catalog differs from shipped Main.qml designs')
    return errors


def synchronize(check=False):
    catalog = load_catalog()
    errors = []
    for relative, pattern, replacement in projections(catalog):
        path = ROOT / relative
        original = path.read_text()
        updated, count = re.subn(pattern, lambda match: replacement, original, flags=re.MULTILINE | re.DOTALL)
        if count != 1:
            errors.append(f'{relative}: expected one choice projection, found {count}')
        elif updated != original:
            if check:
                errors.append(f'{relative}: stale choices; run python3 tools/choice-lists.py')
            else:
                path.write_text(updated)
    return errors + check_documentation(catalog)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    arguments = parser.parse_args()
    failures = synchronize(arguments.check)
    for failure in failures:
        print(failure)
    raise SystemExit(bool(failures))
