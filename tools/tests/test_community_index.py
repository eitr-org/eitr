"""Community schema, deterministic generation and pinned content verification."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from eitr_community import build, entry, validate_index, fetch


class CommunityIndexTests(unittest.TestCase):
    def row(self, **changes):
        return dict(id='example', repository='https://github.com/example/themes', folder='themes/example',
                    maintainer='Example', license='MIT', description='Example theme', **changes)

    def test_strict_entry_schema(self):
        row = self.row()
        self.assertEqual(entry(row, 'themes'), row)
        self.assertEqual(entry(dict(row, commit='a' * 40), 'plugins')['commit'], 'a' * 40)
        for changes in ({'id': '../bad'}, {'repository': 'file:///tmp/repo'}, {'folder': '../theme'},
                        {'license': 'Made-Up-License'}, {'description': 'x' * 73}, {'extra': True}, {'maintainer': ''}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                entry(dict(row, **changes), 'themes')
        for commit in ('HEAD', 'a' * 39, 'g' * 40, True):
            with self.assertRaises(ValueError):
                entry(dict(row, commit=commit), 'plugins')

    def test_generator_and_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for kind in ('themes', 'plugins'):
                (root / kind).mkdir()
            (root / 'removed.json').write_text('[]')
            path = root / 'themes/example.json'
            path.write_text(json.dumps(self.row()))
            index = build(root)
            self.assertEqual(index['themes'], [self.row()])
            (root / 'removed.json').write_text(json.dumps([dict(kind='themes', id='example', reason='Removed')]))
            with self.assertRaisesRegex(ValueError, 'still listed'):
                build(root)
            (root / 'removed.json').write_text('[]')
            path.write_text(json.dumps(dict(self.row(), id='different')))
            with self.assertRaisesRegex(ValueError, 'filename'):
                build(root)
            path.write_text('{"id":"example","id":"duplicate"}')
            with self.assertRaises(ValueError):
                build(root)

    def test_verifier_pins_and_refuses_links_without_checkout(self):
        calls = []
        def fake_git(root, *arguments, **options):
            calls.append(arguments)
            if arguments[0] == 'rev-parse':
                return 'a' * 40
            if arguments[0] == 'ls-tree':
                return '120000 blob abc\tlink\0'
            return ''
        with tempfile.TemporaryDirectory() as directory, patch('eitr_community.git', side_effect=fake_git):
            with self.assertRaisesRegex(ValueError, 'Links'):
                fetch(dict(self.row(), commit='a' * 40), 'plugins', Path(directory))
        self.assertTrue(any(arguments[0] == 'fetch' and arguments[-1] == 'a' * 40 for arguments in calls))
        self.assertTrue(any('--no-checkout' in arguments for arguments in calls))
        self.assertFalse(any(arguments[0] == 'checkout' for arguments in calls))

    def test_plugin_verification_validates_files_without_running_commands(self):
        manifest = dict(id='example', name='Example', description='Example plugin', author='Example', version='1',
                        rows=[dict(title='Example', description='Example action', run='main.sh')])
        blobs = {'manifest': json.dumps(manifest).encode(), 'script': b'#!/bin/sh\nexit 99\n'}
        def fake_git(root, *arguments, **options):
            if arguments[0] == 'rev-parse':
                return 'a' * 40
            if arguments[0] == 'ls-tree':
                return '100644 blob manifest\teitr-plugin.json\0' + '100755 blob script\tmain.sh\0'
            if arguments[:2] == ('cat-file', '-s'):
                return str(len(blobs[arguments[2]]))
            if arguments[:2] == ('cat-file', 'blob'):
                return blobs[arguments[2]]
            return ''
        with tempfile.TemporaryDirectory() as directory, patch('eitr_community.git', side_effect=fake_git):
            package, spec, revision = fetch(dict(self.row(), commit='a' * 40), 'plugins', Path(directory))
            self.assertEqual(spec['id'], 'example')
            self.assertEqual(revision, 'a' * 40)
            self.assertEqual((package / 'main.sh').read_bytes(), blobs['script'])
