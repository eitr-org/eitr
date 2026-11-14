"""Validated Store kind registry, shared by dispatch and the QML projection."""
import json
from pathlib import Path
import re


def load(path=None):
    if path is None:
        from eitr_paths import code_root
        path = code_root() / 'distro/store-kinds.json'
    rows = json.loads(Path(path).read_text())
    if not isinstance(rows, list) or not rows:
        raise ValueError('Expected Store kinds')
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'id', 'label', 'rune', 'icon', 'descriptions', 'sources', 'backend', 'capabilities'}:
            raise ValueError('Invalid Store kind fields')
        if not isinstance(row['id'], str) or not re.fullmatch(r'[a-z][a-z0-9-]*', row['id']) or row['id'] in seen:
            raise ValueError('Invalid or duplicate Store kind')
        seen.add(row['id'])
        if not isinstance(row['backend'], str) or not re.fullmatch(r'[a-z][a-z0-9_]*', row['backend']):
            raise ValueError('Invalid Store backend')
        for field in ('label', 'rune', 'icon'):
            if not isinstance(row[field], str) or not row[field]:
                raise ValueError('Invalid Store label')
        if not re.fullmatch(r'[A-Fa-f0-9]{4,6}', row['icon']):
            raise ValueError('Invalid Store icon')
        if not isinstance(row['descriptions'], dict) or set(row['descriptions']) != {'installed', 'discover'} or any(not isinstance(value, str) or not value for value in row['descriptions'].values()):
            raise ValueError('Invalid Store descriptions')
        if not isinstance(row['sources'], list) or any(not isinstance(source, str) for source in row['sources']) or not row['sources'] or len(set(row['sources'])) != len(row['sources']) or set(row['sources']) - {'official', 'community'}:
            raise ValueError('Invalid Store sources')
        if not isinstance(row['capabilities'], dict) or set(row['capabilities']) != {'useOnClick', 'remove', 'update', 'needsAdministrator'} or any(type(value) is not bool for value in row['capabilities'].values()):
            raise ValueError('Invalid Store capabilities')
    return rows


def registry():
    return {row['id']: row for row in load()}
