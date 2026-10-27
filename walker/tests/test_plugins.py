"""Plugin fixtures never run plugin code or reach the real user service manager."""
from contextlib import redirect_stderr, redirect_stdout
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'distro/lib'))
import eitr_plugins as plugins


class PluginTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        environment = {name: str(self.home / name) for name in (
            'HOME', 'XDG_CONFIG_HOME', 'XDG_STATE_HOME', 'XDG_DATA_HOME', 'XDG_CACHE_HOME', 'XDG_RUNTIME_DIR')}
        self.environment = patch.dict(os.environ, environment)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.root_user = patch('eitr_plugins.os.geteuid', return_value=1000)
        self.root_user.start()
        self.addCleanup(self.root_user.stop)
        self.source = self.home / 'source'
        shutil.copytree(ROOT / 'distro/plugins/example', self.source)
        for name in ('HelloTile.qml', 'HelloPanel.qml', 'qmldir'):
            (self.source / name).unlink()
        legacy = self.spec()
        legacy['schemaVersion'] = 1
        legacy.pop('ui', None)
        (self.source / 'eitr-plugin.json').write_text(json.dumps(legacy))
        self.git(self.source, 'init', '-b', 'main')
        self.git(self.source, 'add', '.')
        self.git(self.source, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Initial plugin')
        self.bare = self.home / 'remote.git'
        self.git(None, 'clone', '--bare', str(self.source), str(self.bare))
        self.url = self.bare.as_uri()
        self.policies = {}
        policy = patch('eitr_policy.load', side_effect=lambda: self.policies)
        policy.start()
        self.addCleanup(policy.stop)
        self.blocklist = self.home / 'plugin-blocklist.json'
        self.block()
        blocklist = patch.object(plugins, 'BLOCKLIST', self.blocklist)
        blocklist.start()
        self.addCleanup(blocklist.stop)
        self.notices = []
        self.manager = plugins.Plugins(allow_file=True, notify=lambda *notice: self.notices.append(notice) or True)
        self.systemctl = patch.object(self.manager, 'systemctl')
        self.commands = self.systemctl.start()
        self.addCleanup(self.systemctl.stop)

    def git(self, root, *arguments):
        return plugins.git(root, *arguments, allow_file=True)

    def spec(self):
        return json.loads((self.source / 'eitr-plugin.json').read_text())

    def block(self, **entry):
        entries = [dict(entry, reason='Test entry: sends SSH keys away', date='2026-10-22')] if entry else []
        self.blocklist.write_text(json.dumps({'version': 1, 'entries': entries}))

    def cli(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('plugin_cli_test', ROOT / 'walker/scripts/actions/install/plugins.py')
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        return cli

    def commit_as(self, name, message='Updated plugin'):
        self.git(self.source, 'add', '.')
        self.git(self.source, '-c', 'user.name=' + name, '-c', f'user.email={name.lower()}@example.invalid', 'commit', '-m', message)
        self.git(self.source, 'push', str(self.bare), 'main')

    def write_spec(self, spec):
        (self.source / 'eitr-plugin.json').write_text(json.dumps(spec))

    def publish(self, spec=None):
        if spec:
            self.write_spec(spec)
        else:
            (self.source / 'revision').write_text('new revision')
        self.git(self.source, 'add', '.')
        self.git(self.source, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Updated plugin')
        self.git(self.source, 'push', str(self.bare), 'main')

    def install(self):
        self.assertTrue(self.manager.add(self.url, lambda url: True, lambda *details: True))
        return self.manager.records()['example']['commit']

    def test_manifest_refusals(self):
        valid = self.spec()
        cases = []
        for key, value in [('unknown', True), ('id', '../escape'), ('description', 'x' * 73), ('rows', [])]:
            spec = copy.deepcopy(valid)
            spec[key] = value
            cases.append(spec)
        for key, value in [('unknown', 'value'), ('description', 'x' * 73), ('run', '../escape'), ('run', '/bin/true'), ('run', 'eitr-plugin.json'), ('arguments', 'shell string'), ('arguments', ['bad\nargument'])]:
            spec = copy.deepcopy(valid)
            spec['rows'][0][key] = value
            cases.append(spec)
        for spec in cases:
            with self.subTest(spec=spec):
                self.write_spec(spec)
                with self.assertRaises((ValueError, OSError)):
                    plugins.manifest(self.source)
        self.write_spec(valid)
        (self.source / 'notify.sh').chmod(0o644)
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)
        (self.source / 'notify.sh').unlink()
        (self.source / 'notify.sh').symlink_to('/bin/true')
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)

    def test_duplicate_keys_and_service_fields_refused(self):
        path = self.source / 'eitr-plugin.json'
        path.write_text('{"id":"example","id":"other"}')
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)
        spec = json.loads((ROOT / 'distro/plugins/example/eitr-plugin.json').read_text())
        spec['service'] = {'run': 'notify.sh', 'unknown': True}
        self.write_spec(spec)
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)

    def test_url_validation(self):
        for url in ('file:///tmp/plugin', 'http://example.com/repo', 'https://user:password@example.com/repo', '-upload-pack=evil',
                    'ssh://-oProxyCommand=evil/repo', 'git@-oProxyCommand=evil:repo', 'git@example.com:../repo',
                    'ssh://git@example.com/../repo', 'ext::sh -c evil', 'git@example.com:-repo'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                plugins.repository_url(url)
        for url in ('https://example.com/repo.git', 'git@github-personal:owner/repo.git', 'ssh://git@example.com/owner/repo.git'):
            with self.subTest(url=url):
                self.assertEqual(plugins.repository_url(url), url)

    def test_install_approval_hooks_rows_and_removal(self):
        marker = self.home / 'executed'
        hooks = self.home / 'hooks'
        hooks.mkdir()
        hook = hooks / 'post-checkout'
        hook.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\n')
        hook.chmod(0o755)
        global_config = self.home / 'gitconfig'
        global_config.write_text('[core]\n hooksPath = ' + str(hooks) + '\n')
        with patch.dict(os.environ, {'GIT_CONFIG_GLOBAL': str(global_config)}):
            def refuse(root, spec, url):
                self.assertEqual(spec['author'], 'Eitr contributors')
                self.assertFalse(self.manager.state.exists())
                self.assertFalse(self.manager.folder.exists())
                self.assertFalse(marker.exists())
                self.commands.assert_not_called()
                return False
            self.assertFalse(self.manager.add(self.url, lambda url: True, refuse))
            approved = self.install()
        self.assertFalse(marker.exists())
        self.assertEqual(approved, plugins.commit(self.source))
        self.assertEqual(self.manager.rows()[0]['title'], 'Example notification')
        self.assertFalse(self.manager.remove('example', lambda record: False))
        self.assertTrue(self.manager.remove('example', lambda record: True))
        self.assertEqual(self.manager.records(), {})
        self.assertEqual(self.manager.rows(), [])
        self.assertFalse((self.manager.folder / 'example').exists())

    def test_update_refusal_success_and_invalid_candidate(self):
        old = self.install()
        self.publish()
        self.assertFalse(self.manager.update('example', lambda *details: False))
        self.assertEqual(plugins.commit(self.manager.folder / 'example'), old)
        def approve(changes):
            self.assertEqual(changes['old'], old)
            self.assertTrue(any('Updated plugin' in subject for subject in changes['subjects']))
            self.assertEqual([(change['status'], change['path'], change['added']) for change in changes['files']], [('A', 'revision', '1')])
            self.assertEqual(changes['flags'], [])
            return True
        self.assertTrue(self.manager.update('example', approve))
        approved = self.manager.records()['example']['commit']
        self.assertNotEqual(approved, old)
        invalid = self.spec()
        invalid['rows'][0]['run'] = '../escape'
        self.publish(invalid)
        with self.assertRaises(ValueError):
            self.manager.update('example', lambda *details: self.fail('Invalid code reached confirmation'))
        self.assertEqual(plugins.commit(self.manager.folder / 'example'), approved)
        self.assertEqual(self.manager.records()['example']['commit'], approved)

    def test_service_unit_and_update_failure_rollback(self):
        spec = self.spec()
        spec['service'] = {'run': 'notify.sh', 'arguments': ['a space', '%specifier', '$variable', '"quoted"']}
        self.publish(spec)
        old = self.install()
        unit = self.manager.unit('example')
        content = unit.read_text()
        self.assertIn('ExecStart="' + str(self.manager.folder / 'example/notify.sh') + '"', content)
        self.assertIn('Restart=on-failure', content)
        self.assertIn('\nNoNewPrivileges=yes\n', content)
        self.assertIn('RestartSec=5', content)
        self.assertIn('"a space" "%%specifier" "$$variable" "\\"quoted\\""', content)
        self.commands.assert_any_call('enable', '--now', unit.name)
        self.publish()
        def fail_start(*arguments):
            if arguments[0] == 'enable':
                raise subprocess.CalledProcessError(1, arguments)
        self.commands.side_effect = fail_start
        with self.assertRaises(subprocess.CalledProcessError):
            self.manager.update('example', lambda *details: True)
        self.assertEqual(plugins.commit(self.manager.folder / 'example'), old)
        self.assertEqual(self.manager.records()['example']['commit'], old)
        self.assertEqual(unit.read_text(), content)
        self.commands.side_effect = None
        self.manager.remove('example', lambda record: True)
        self.assertFalse(unit.exists())
        self.commands.assert_any_call('disable', '--now', unit.name)

    def test_failure_writing_state_rolls_back_without_service(self):
        old = self.install()
        self.publish()
        with patch.object(self.manager, 'save', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.manager.update('example', lambda *details: True)
        self.assertEqual(plugins.commit(self.manager.folder / 'example'), old)
        self.assertEqual(self.manager.records()['example']['commit'], old)

    def test_root_mutations_refused(self):
        with patch('eitr_plugins.os.geteuid', return_value=0), self.assertRaises(ValueError):
            self.manager.add(self.url, lambda url: True, lambda *details: True)

    def test_menu_parents_and_scoped_search(self):
        for name, parent in [('plugins', 'tools'), ('plugins-install', 'install'), ('plugin-actions', 'plugins-install')]:
            self.assertIn('Parent = "' + parent + '"', (ROOT / 'elephant/menus' / (name + '.lua')).read_text())
            self.assertEqual((ROOT / 'walker/themes/current' / ('item_menus-' + name + '.xml')).read_bytes(),
                             (ROOT / 'walker/themes/current/item_menus-main.xml').read_bytes())
        for name in ('tools', 'install'):
            rows = json.loads((ROOT / 'elephant/menu-rows' / (name + '.json')).read_text())
            self.assertTrue(any(row['text'] == 'Plugins' and row['subtext'] == '>' for row in rows))

    def test_declared_service_and_script_do_not_run_before_approval(self):
        marker = self.home / 'plugin-ran'
        (self.source / 'notify.sh').write_text('#!/bin/sh\ntouch "' + str(marker) + '"\n')
        spec = self.spec()
        spec['service'] = {'run': 'notify.sh'}
        self.publish(spec)
        def refuse(*details):
            self.assertFalse(marker.exists())
            self.assertFalse(self.manager.unit('example').exists())
            self.commands.assert_not_called()
            return False
        self.assertFalse(self.manager.add(self.url, lambda url: True, refuse))
        self.assertFalse(marker.exists())
        self.assertFalse(self.manager.state.exists())

    def test_update_service_addition_and_removal(self):
        self.install()
        spec = self.spec()
        spec['service'] = {'run': 'notify.sh'}
        self.publish(spec)
        self.assertTrue(self.manager.update('example', lambda *details: True))
        self.assertTrue(self.manager.unit('example').exists())
        self.commands.assert_any_call('enable', '--now', 'eitr-plugin-example.service')
        del spec['service']
        self.publish(spec)
        self.assertTrue(self.manager.update('example', lambda *details: True))
        self.assertFalse(self.manager.unit('example').exists())
        self.commands.assert_any_call('disable', '--now', 'eitr-plugin-example.service')

    def test_noninteractive_update_never_fetches(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('plugin_cli_test', ROOT / 'walker/scripts/actions/install/plugins.py')
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        with patch.object(cli.sys.stdin, 'isatty', return_value=False), patch.object(self.manager, 'update') as update:
            cli.update(self.manager)
        update.assert_not_called()

    def test_id_changes_and_fetch_failures_keep_the_approved_commit(self):
        old = self.install()
        spec = self.spec()
        spec['id'] = 'different'
        self.publish(spec)
        with self.assertRaises(ValueError):
            self.manager.update('example', lambda *details: self.fail('Changed id reached review'))
        with patch('eitr_plugins.clone', side_effect=subprocess.CalledProcessError(1, 'git')):
            with self.assertRaises(subprocess.CalledProcessError):
                self.manager.update('example', lambda *details: True)
        self.assertEqual(plugins.commit(self.manager.folder / 'example'), old)
        self.assertEqual(self.manager.records()['example']['commit'], old)

    def test_walker_entries_and_scoped_search_data(self):
        import importlib.util
        self.install()
        rows = self.manager.rows()
        def lua_rows(values):
            return '{' + ','.join('{' + ','.join(key + '=' + json.dumps(value, ensure_ascii=False)
                for key, value in row.items()) + '}' for row in values) + '}'
        harness = '''
            local fixtures = {rows = %s, installed = {{id="example", name="Example plugin", author="Eitr contributors", blocked=""},
                {id="bad", name="Bad plugin", author="Someone", blocked="blocklist"}}}
            io.popen = function(command)
                local action = command:match(" ([a-z]+)$")
                return {read = function() return action end, close = function() end}
            end
            jsonDecode = function(action)
                if action:sub(1, 1) == "[" then return {
                    {text="Visuals", subtext=">", submenu="plugin-visuals"},
                    {text="Remove", subtext="Remove this plugin and its service"},
                    {text="Update", subtext="Review a new plugin commit"}}
                end
                return fixtures[action]
            end
            lastMenuValue = function(name) assert(name == "plugins-install"); return "example" end
            for _, name in ipairs({"plugins", "plugins-install", "plugin-actions"}) do
                dofile("elephant/menus/" .. name .. ".lua")
                for _, entry in ipairs(GetEntries()) do
                    if entry.SubMenu then
                        assert(entry.State[1] == "submenu")
                    else
                        assert(entry.Subtext and entry.Subtext ~= "")
                    end
                    print(name .. " | " .. entry.Text .. " | " .. (entry.SubMenu or "-") .. " | " .. (entry.Subtext or ""))
                end
            end
        ''' % lua_rows(rows)
        environment = dict(os.environ, EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'), EITR_CODE_ROOT=str(ROOT))
        result = subprocess.run(['lua', '-e', harness], cwd=ROOT, env=environment, capture_output=True, text=True, check=True)
        self.assertIn('plugins | Example notification | - | Plugin by Eitr contributors · not reviewed by Eitr', result.stdout)
        self.assertIn('plugins-install | Bad plugin | - | Blocked by Eitr for your safety · select to remove', result.stdout)
        self.assertIn('plugins-install | Example plugin | plugin-actions | Plugin by Eitr contributors · not reviewed by Eitr', result.stdout)
        self.assertIn('plugin-actions | Remove |', result.stdout)
        self.assertIn('plugin-actions | Update |', result.stdout)
        print(result.stdout.strip())
        spec = importlib.util.spec_from_file_location('plugin_search_test', ROOT / 'walker/scripts/menus/search-index.py')
        search = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(search)
        output = json.dumps({'item': dict(provider='menus:plugins', identifier='example:0',
            text=rows[0]['title'], subtext=rows[0]['description'], actions=['open'])})
        snapshot = search.snapshot(output, parent_of=search.parents())
        self.assertIn('tools', snapshot[0]['menus'])
        self.assertIn('main', snapshot[0]['menus'])
        self.assertEqual(snapshot[0]['actions'], ['open'])

    def test_partial_install_copy_is_cleaned_up(self):
        def partial_copy(source, destination, **options):
            destination.mkdir(parents=True)
            (destination / 'partial').touch()
            raise OSError('disk full')
        with patch('eitr_plugins.shutil.copytree', side_effect=partial_copy):
            with self.assertRaises(OSError):
                self.manager.add(self.url, lambda url: True, lambda *details: True)
        self.assertFalse((self.manager.folder / 'example').exists())
        self.assertFalse(self.manager.state.exists())

    def test_directory_swap_failure_restores_previous_commit(self):
        old = self.install()
        self.publish()
        rename = Path.rename
        def fail_replacement(path, destination):
            if path.name == '.example-new':
                raise OSError('rename failed')
            return rename(path, destination)
        with patch.object(Path, 'rename', fail_replacement), self.assertRaises(OSError):
            self.manager.update('example', lambda *details: True)
        self.assertEqual(plugins.commit(self.manager.folder / 'example'), old)
        self.assertEqual(self.manager.records()['example']['commit'], old)

    def test_postapproval_manifest_change_is_refused(self):
        old = self.install()
        self.publish()
        def approve(changes):
            changes['spec']['name'] = 'not the reviewed manifest'
            return True
        with self.assertRaises(ValueError):
            self.manager.update('example', approve)
        self.assertEqual(plugins.commit(self.manager.folder / 'example'), old)
        self.assertEqual(self.manager.records()['example']['commit'], old)

    def test_nothing_is_cloned_before_the_safety_confirmation(self):
        with patch('eitr_plugins.clone') as clone:
            self.assertFalse(self.manager.add(self.url, lambda url: False, lambda *details: self.fail('reviewed')))
        clone.assert_not_called()
        self.assertFalse(self.manager.folder.exists())
        cli = self.cli()
        # Escape or Ctrl+C declines; other keys (y, n) do nothing until one of them.
        for keys in (['\x1b'], ['\x03'], ['y', 'n', '\x1b']):
            with self.subTest(keys=keys), patch('eitr_plugins.clone') as clone, \
                    patch.object(cli, 'read_key', side_effect=keys), redirect_stdout(io.StringIO()) as output:
                self.assertFalse(cli.add_in_terminal(self.manager, self.url))
            clone.assert_not_called()
            text = ' '.join(output.getvalue().split())
            self.assertIn('SSH keys and browser data', text)
            self.assertIn('never in a pop-up window', text)
            self.assertIn('exact author and commit', text)
            self.assertIn('Nothing was downloaded.', text)

    def test_terminal_add_needs_both_confirmations_and_noninteractive_add_is_refused(self):
        cli = self.cli()
        # Enter confirms the safety screen; Escape declines the review.
        with patch.object(cli, 'read_key', side_effect=['\r', '\x1b']), redirect_stdout(io.StringIO()) as output:
            self.assertFalse(cli.add_in_terminal(self.manager, self.url))
        self.assertFalse(self.manager.state.exists())
        review = ' '.join(output.getvalue().split())
        self.assertLess(review.index('Eitr has not reviewed this code'), review.index('Plugin: Example plugin'))
        self.assertIn('Plugin by Eitr contributors · not reviewed by Eitr', review)
        self.assertIn('Executable files: 1', review)
        self.assertIn('Nothing was installed; the downloaded copy was deleted.', review)
        # Other keys do nothing; Enter confirms both steps.
        with patch.object(cli, 'read_key', side_effect=['y', '\r', 'n', '\r']), redirect_stdout(io.StringIO()):
            self.assertTrue(cli.add_in_terminal(self.manager, self.url))
        with patch.object(cli.sys.stdin, 'isatty', return_value=False), patch('eitr_plugins.clone') as clone:
            with self.assertRaises(ValueError):
                cli.add(self.manager, self.url)
        clone.assert_not_called()

    def test_review_lines_show_service_executables_and_binary_warnings(self):
        spec = self.spec()
        spec['service'] = {'run': 'notify.sh'}
        (self.source / 'blob.bin').write_bytes(b'\0\1\2')
        self.write_spec(spec)
        lines = self.cli().review_lines(self.source, plugins.manifest(self.source), self.url)
        self.assertTrue(lines[0].startswith('Plugins run with your account'))
        self.assertIn('Background service: Yes', lines)
        self.assertIn('⚠ Starts a background service at every login: notify.sh', lines)
        self.assertIn('⚠ Binary file: blob.bin', lines)

    def test_update_risk_flags_from_real_history(self):
        old = self.install()
        spec = self.spec()
        spec['service'] = {'run': 'notify.sh', 'arguments': ['--watch']}
        self.write_spec(spec)
        (self.source / 'helper.sh').write_text('#!/bin/sh\n')
        (self.source / 'helper.sh').chmod(0o755)
        (self.source / 'notify.sh').write_text('#!/usr/bin/env bash\necho changed\n')
        (self.source / 'blob.bin').write_bytes(b'\0binary')
        self.commit_as('Mallory', 'Add a helper')
        seen = {}
        def approve(changes):
            seen.update(changes)
            return False
        self.assertFalse(self.manager.update('example', approve))
        flags = seen['flags']
        self.assertIn('Background service added: notify.sh --watch', flags)
        self.assertIn('Manifest changed: eitr-plugin.json', flags)
        self.assertIn('New executable file: helper.sh', flags)
        self.assertIn('Changed executable file: notify.sh', flags)
        self.assertIn('Binary file: blob.bin', flags)
        self.assertIn('Commit by a different author than the approved one: Mallory <mallory@example.invalid>', flags)
        files = {change['path']: change for change in seen['files']}
        self.assertTrue(files['blob.bin']['binary'])
        self.assertEqual((files['notify.sh']['added'], files['notify.sh']['removed']), ('1', '2'))
        self.assertEqual(self.manager.records()['example']['commit'], old)
        self.assertTrue(self.manager.update('example', lambda changes: True))
        del spec['service']
        self.write_spec(spec)
        self.commit_as('Mallory')
        self.manager.update('example', approve)
        self.assertEqual(seen['flags'], ['Background service removed', 'Manifest changed: eitr-plugin.json'])

    def test_rewritten_history_is_refused_before_review(self):
        old = self.install()
        (self.source / 'revision').write_text('rewritten')
        self.git(self.source, 'add', '.')
        self.git(self.source, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--amend', '-m', 'Rewritten')
        self.git(self.source, 'push', '--force', str(self.bare), 'main')
        with self.assertRaisesRegex(ValueError, 'rewritten'):
            self.manager.update('example', lambda changes: self.fail('Rewritten history reached review'))
        self.assertEqual(self.manager.records()['example']['commit'], old)

    def test_update_keys_pager_and_default(self):
        cli = self.cli()
        old = self.install()
        self.publish()
        which = {'less': '/usr/bin/less'}
        with patch.object(cli.sys.stdin, 'isatty', return_value=True), patch.object(cli, 'read_key', side_effect=['\x1b']), \
                redirect_stdout(io.StringIO()) as output:
            cli.update(self.manager)
        self.assertIn('Plugin by Eitr contributors · not reviewed by Eitr', output.getvalue())
        self.assertIn('A  revision  +1 −0', output.getvalue())
        self.assertIn('kept the current version', output.getvalue())
        self.assertEqual(self.manager.records()['example']['commit'], old)
        for key in ('\x1b', '\x03'):
            with patch.object(cli.sys.stdin, 'isatty', return_value=True), patch.object(cli, 'read_key', side_effect=[key]), \
                    redirect_stdout(io.StringIO()):
                cli.update(self.manager)
            self.assertEqual(self.manager.records()['example']['commit'], old)
        with patch.object(cli.sys.stdin, 'isatty', return_value=True), patch.object(cli, 'read_key', side_effect=['d', '\r']), \
                patch.object(cli.shutil, 'which', side_effect=which.get), patch.object(cli, 'run_pager') as pager, \
                redirect_stdout(io.StringIO()):
            cli.update(self.manager)
        command, text, environment = pager.call_args.args
        self.assertEqual(command, ['less', '-R'])
        self.assertEqual(environment['LESSSECURE'], '1')
        self.assertIn('new revision', text)
        self.assertNotEqual(self.manager.records()['example']['commit'], old)
        with patch.object(cli.shutil, 'which', side_effect={'delta': '/usr/bin/delta', 'less': '/usr/bin/less'}.get):
            self.assertEqual(cli.pager_command(), (['delta', '--paging=always'], False))

    def test_blocklist_parser_is_strict(self):
        valid = {'url': 'https://example.com/a/b.git', 'reason': 'Steals keys', 'date': '2026-10-22'}
        for entry in (dict(valid, extra=True), {**valid, 'id': 'b'}, dict(valid, date='22.10.2026'), dict(valid, date='2026-02-30'),
                      {'commit': 'ABC', 'reason': 'x', 'date': '2026-10-22'}, {'id': '../x', 'reason': 'x', 'date': '2026-10-22'},
                      {'url': 'ext::sh -c evil', 'reason': 'x', 'date': '2026-10-22'}, {'reason': 'x', 'date': '2026-10-22'}):
            with self.subTest(entry=entry):
                self.blocklist.write_text(json.dumps({'version': 1, 'entries': [entry]}))
                with self.assertRaisesRegex(ValueError, 'blocklist could not be read'):
                    plugins.blocklist()
        for text in ('', '[]', '{"version": 2, "entries": []}', '{"version": 1, "entries": [], "entries": []}'):
            self.blocklist.write_text(text)
            with self.assertRaises(ValueError):
                plugins.blocklist()
        self.assertEqual(plugins.blocklist(ROOT / 'distro/plugin-blocklist.json'), [])
        self.assertEqual(plugins.normalized_url('git@GitHub.com:Owner/Repo.git'), plugins.normalized_url('https://github.com/owner/repo/'))
        self.assertEqual(plugins.normalized_url('ssh://git@github.com:22/owner/repo.git'), 'github.com/owner/repo')

    def test_blocklist_refuses_add_by_url_commit_and_id(self):
        commit = plugins.commit(self.source)
        consent = unittest.mock.Mock(return_value=True)
        for entry in (dict(id='example'), dict(commit=commit)):
            with self.subTest(entry=entry):
                self.block(**entry)
                with self.assertRaisesRegex(ValueError, 'blocklist: Test entry'):
                    self.manager.add(self.url, consent, lambda *details: self.fail('Blocked plugin reached review'))
        with patch.object(plugins, 'normalized_url', side_effect=lambda value: 'blocked/repo'):
            self.block(url='https://blocked.example/repo')
            consent.reset_mock()
            with self.assertRaisesRegex(ValueError, 'blocklist'):
                self.manager.add(self.url, consent, lambda *details: True)
            consent.assert_not_called()
        self.assertFalse(self.manager.state.exists())

    def test_blocklist_refuses_update_to_a_blocked_commit(self):
        old = self.install()
        self.publish()
        self.block(commit=plugins.commit(self.source))
        with self.assertRaisesRegex(ValueError, 'blocklist'):
            self.manager.update('example', lambda changes: self.fail('Blocked commit reached review'))
        self.assertEqual(self.manager.records()['example']['commit'], old)

    def test_blocked_installed_plugin_is_hidden_stopped_refused_and_notified_once(self):
        spec = self.spec()
        spec['service'] = {'run': 'notify.sh'}
        self.publish(spec)
        self.install()
        unit = self.manager.unit('example')
        self.commands.reset_mock()
        self.block(id='example')
        self.assertEqual(self.manager.rows(), [])
        self.commands.assert_called_once_with('disable', '--now', unit.name)
        self.assertTrue(unit.exists())
        self.assertTrue((self.manager.folder / 'example/notify.sh').exists())
        self.assertEqual(self.notices, [('example', 'Example plugin', 'blocklist', 'Test entry: sends SSH keys away')])
        self.assertEqual(self.manager.rows(), [])
        with patch('eitr_plugins.subprocess.Popen') as popen, self.assertRaisesRegex(ValueError, 'blocklist'):
            self.manager.launch('example', 0)
        popen.assert_not_called()
        self.assertEqual(len(self.notices), 1)
        self.commands.assert_called_once()
        self.assertEqual(self.manager.installed()[0]['blocked'], 'blocklist')
        cli = self.cli()
        with patch.object(cli.sys.stdin, 'isatty', return_value=True), patch.object(self.manager, 'update') as update, \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
            cli.update(self.manager)
        update.assert_not_called()
        self.assertIn('Test entry', errors.getvalue())
        title, body = cli.notice_text('Example plugin', 'blocklist', 'Test entry.')
        self.assertIn('Example plugin', title)
        self.assertIn(plugins.REPORT_URL, body)
        self.block()
        self.assertEqual(len(self.manager.rows()), 1)

    def test_notification_waits_for_remove_in_a_detached_helper(self):
        cli = self.cli()
        self.install()
        self.block(id='example')
        self.manager.notify = None
        self.manager.enforce()
        with patch.object(cli.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'remove\n')) as run, \
                patch.object(cli.subprocess, 'Popen') as popen:
            cli.notice(self.manager, 'example')
        self.assertIn('--action=remove=Remove', run.call_args.args[0])
        self.assertEqual(popen.call_args.args[0][-2:], ['remove', 'example'])
        with patch.dict(os.environ, {'DBUS_SESSION_BUS_ADDRESS': ''}), patch.object(cli.subprocess, 'Popen') as popen:
            self.assertFalse(cli.notify_blocked('example', 'Example plugin', 'blocklist', 'reason'))
        popen.assert_not_called()

    def test_organization_policy_off_and_allowlist(self):
        self.install()
        self.policies = {'plugins': False}
        consent = unittest.mock.Mock(return_value=True)
        with self.assertRaisesRegex(ValueError, 'turned off by your organization'):
            self.manager.add(self.url, consent, lambda *details: True)
        consent.assert_not_called()
        self.assertEqual(self.manager.rows(), [])
        self.assertEqual(self.notices[-1][2], 'policy')
        with self.assertRaisesRegex(ValueError, 'organization'):
            self.manager.update('example', lambda changes: True)
        with patch('eitr_plugins.subprocess.Popen'), self.assertRaisesRegex(ValueError, 'organization'):
            self.manager.launch('example', 0)
        cli = self.cli()
        with patch.object(cli.sys.stdin, 'isatty', return_value=True), self.assertRaisesRegex(ValueError, 'organization'):
            cli.add(self.manager)
        import eitr_policy
        for menu in ('plugins', 'plugins-install', 'plugin-actions'):
            self.assertFalse(eitr_policy.row_allowed({'submenu': menu}, self.policies))
        self.assertTrue(eitr_policy.row_allowed({'submenu': 'plugins'}, {'plugins': {'allow': [self.url]}}))
        self.policies = {'plugins': {'allow': ['https://example.com/approved/plugin.git']}}
        self.assertEqual(self.manager.rows(), [])
        self.assertEqual(self.manager.installed()[0]['blocked'], 'policy')
        self.manager.remove('example', lambda record: True)
        with self.assertRaisesRegex(ValueError, 'approved repositories'):
            self.manager.add(self.url, consent, lambda *details: True)
        self.policies = {'plugins': {'allow': [self.url + '/']}}
        self.assertTrue(self.manager.add(self.url, lambda url: True, lambda *details: True))

    def test_symlinks_anywhere_are_refused_at_add_and_update(self):
        (self.source / 'docs').mkdir()
        (self.source / 'docs/link').symlink_to('../notify.sh')
        self.commit_as('Fixture')
        with self.assertRaisesRegex(ValueError, 'symlinks: docs/link'):
            self.manager.add(self.url, lambda url: True, lambda *details: self.fail('Symlink reached review'))
        self.git(self.source, 'rm', '-q', 'docs/link')
        self.commit_as('Fixture')
        old = self.install()
        (self.source / 'folder-link').symlink_to('docs')
        self.commit_as('Fixture')
        with self.assertRaisesRegex(ValueError, 'symlinks: folder-link'):
            self.manager.update('example', lambda changes: self.fail('Symlink reached review'))
        self.assertEqual(self.manager.records()['example']['commit'], old)

    def test_schema_versions_and_hooks(self):
        valid = self.spec()
        for version in (None, 1):
            spec = copy.deepcopy(valid)
            if version is None:
                del spec['schemaVersion']
            self.write_spec(spec)
            self.assertEqual(plugins.manifest(self.source), spec)
        for version in (3, 0, -1, True, '1', 1.0, None):
            spec = dict(valid, schemaVersion=version)
            self.write_spec(spec)
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, 'newer Eitr' if version == 3 else 'schemaVersion'):
                plugins.manifest(self.source)
        for hooks in ({'unknown': {'run': 'notify.sh'}}, {'login': {'run': '../escape'}},
                      {'login': {'run': 'notify.sh', 'arguments': [1]}}, [], {'login': {'run': '/bin/true'}}):
            self.write_spec(dict(valid, hooks=hooks))
            with self.subTest(hooks=hooks), self.assertRaises(ValueError):
                plugins.manifest(self.source)
        self.write_spec(valid)
        lines = self.cli().review_lines(self.source, valid, self.url)
        self.assertTrue(any('Event hook: theme-changed' in line for line in lines))
        del valid['schemaVersion']
        self.assertTrue(any('should declare schemaVersion' in line for line in self.cli().review_lines(self.source, valid, self.url)))

    def test_hook_runner_context_timeout_and_failures(self):
        approved = self.install()
        commit_mock = patch('eitr_plugins.commit', return_value=approved)
        commit_mock.start()
        self.addCleanup(commit_mock.stop)
        with patch('eitr_plugins.subprocess.Popen') as popen, patch.dict(os.environ, {'EITR_THEME': 'forest', 'EITR_WALLPAPER': 'stale'}):
            popen.return_value.wait.return_value = 0
            self.manager.hooks('theme-changed')
            argv = popen.call_args.args[0]
            options = popen.call_args.kwargs
            self.assertEqual(argv[1:], ['The theme changed'])
            self.assertEqual(options['cwd'], self.manager.folder / 'example')
            self.assertEqual(options['env']['EITR_EVENT'], 'theme-changed')
            self.assertEqual(options['env']['EITR_THEME'], 'forest')
            self.assertNotIn('EITR_WALLPAPER', options['env'])
            self.assertTrue(options['start_new_session'])
            popen.return_value.wait.assert_called_once_with(timeout=30)
        for failure in (OSError('cannot launch'), None):
            with patch('eitr_plugins.subprocess.Popen', side_effect=failure) as popen:
                if failure is None:
                    popen.return_value.wait.return_value = 7
                self.manager.hooks('theme-changed')
        with patch('eitr_plugins.subprocess.Popen') as popen, patch('eitr_plugins.os.killpg') as kill:
            popen.return_value.pid = 123
            popen.return_value.wait.side_effect = [subprocess.TimeoutExpired('hook', 30), 0]
            self.manager.hooks('theme-changed')
            kill.assert_called_once_with(123, plugins.signal.SIGKILL)
        log = plugins.state('eitr/plugin-hooks.log').read_text()
        for message in ('cannot launch', 'exited with 7', 'timeout after 30 seconds'):
            self.assertIn(message, log)
        for policy in ({'plugins': False}, {'plugins': {'allow': []}}):
            self.policies = policy
            with patch('eitr_plugins.subprocess.Popen') as popen:
                self.manager.hooks('theme-changed')
                popen.assert_not_called()
        self.policies = {}
        self.block(id='example')
        with patch('eitr_plugins.subprocess.Popen') as popen:
            self.manager.hooks('theme-changed')
            popen.assert_not_called()

    def test_hook_update_flags_and_detached_dispatch(self):
        self.install()
        spec = self.spec()
        spec['hooks']['theme-changed']['arguments'] = ['changed']
        spec['hooks']['login'] = {'run': 'notify.sh'}
        self.publish(spec)
        def approve(changes):
            self.assertIn('Event hook added or changed: theme-changed', changes['flags'])
            self.assertIn('Event hook added or changed: login', changes['flags'])
            self.assertTrue(any('RISK: Event hook' in line for line in self.cli().summary_lines(changes)))
            return False
        self.manager.update('example', approve)
        with patch('eitr_plugins.subprocess.Popen') as popen:
            plugins.dispatch_hooks('wallpaper-changed', EITR_WALLPAPER='/example/image.png')
            self.assertEqual(popen.call_args.args[0][-2:], ['hooks', 'wallpaper-changed'])
            self.assertTrue(popen.call_args.kwargs['start_new_session'])
            popen.return_value.wait.assert_not_called()
        with patch('eitr_plugins.subprocess.Popen', side_effect=OSError('missing')):
            plugins.dispatch_hooks('login')

    def test_after_update_fires_only_when_updates_were_installed(self):
        script = (ROOT / 'walker/scripts/actions/system/update.sh').read_text()
        up_to_date = script[script.index('if [[ "${1:-}" == system ]] && no_updates; then'):]
        up_to_date = up_to_date[:up_to_date.index('\nfi\n')]
        self.assertNotIn('plugin_after_update', up_to_date)
        self.assertEqual(script.count('\n    plugin_after_update\n'), 1)

    def test_event_trigger_sites_are_detached(self):
        for filename, event in (('walker/scripts/actions/style/apply.sh', 'theme-changed'),
                                ('walker/scripts/actions/system/update.sh', 'after-update')):
            text = (ROOT / filename).read_text()
            line = next(line for line in text.splitlines() if 'hooks ' + event in line)
            self.assertIn('setsid python3', line)
            self.assertTrue(line.endswith('&'))
            with tempfile.TemporaryDirectory() as directory:
                trace = Path(directory) / 'calls'
                environment = dict(os.environ, EITR_CODE_ROOT=str(ROOT), EITR_THEME='forest', THEME_NAME='forest', TRACE=str(trace))
                harness = 'setsid() { printf "%s\\n" "$*" > "$TRACE"; };\n' + line + '\nwait\n'
                subprocess.run(['bash', '-c', harness], env=environment, check=True)
                self.assertIn('hooks ' + event, trace.read_text())
        wallpaper = (ROOT / 'walker/scripts/actions/wallpaper/transition.py').read_text()
        self.assertIn('dispatch_hooks("wallpaper-changed", EITR_WALLPAPER=path)', wallpaper)
        bar = (ROOT / 'quickshell/desktop-bar/shell.qml').read_text()
        self.assertIn('Quickshell.execDetached(["python3", Eitr.Paths.code("walker/scripts/actions/install/plugins.py"), "hooks", "login"])', bar)
        if shutil.which('node'):
            handler = bar.split('running: !pluginSession.dispatched', 1)[1].split('onTriggered: {', 1)[1].split('        }', 1)[0]
            harness = ("const calls = []; const pluginSession = {dispatched: false}; "
                       "const Eitr = {Paths: {code: path => path}}; "
                       "const Quickshell = {execDetached: argv => calls.push(argv)}; "
                       + handler + "; console.log(JSON.stringify({calls, dispatched: pluginSession.dispatched}));")
            result = subprocess.run(['node', '-e', harness], check=True, capture_output=True, text=True)
            observed = json.loads(result.stdout)
            self.assertTrue(observed['dispatched'])
            self.assertEqual(observed['calls'], [['python3', 'walker/scripts/actions/install/plugins.py', 'hooks', 'login']])



    def test_login_once_per_desktop_session(self):
        spec = self.spec()
        spec['hooks'] = {'login': {'run': 'notify.sh'}}
        self.publish(spec)
        approved = self.install()
        commit_mock = patch('eitr_plugins.commit', return_value=approved)
        commit_mock.start()
        self.addCleanup(commit_mock.stop)
        Path(os.environ['XDG_RUNTIME_DIR']).mkdir(parents=True)
        with patch.dict(os.environ, {'HYPRLAND_INSTANCE_SIGNATURE': 'fixture-session'}), patch('eitr_plugins.subprocess.Popen') as popen:
            popen.return_value.wait.return_value = 0
            self.manager.hooks('login')
            self.manager.hooks('login')
            popen.assert_called_once()
        with patch.dict(os.environ, {'HYPRLAND_INSTANCE_SIGNATURE': 'next-session'}), patch('eitr_plugins.subprocess.Popen') as popen:
            popen.return_value.wait.return_value = 0
            self.manager.hooks('login')
            popen.assert_called_once()

    def test_failure_does_not_stop_other_hooks(self):
        self.install()
        record = self.manager.records()['example']
        with patch.object(self.manager, 'records', return_value={'example': record, 'second': record}), \
                patch('eitr_plugins.commit', return_value=record['commit']), \
                patch('eitr_plugins.manifest', return_value=self.spec()), \
                patch('eitr_plugins.command', return_value=['fixture-script']), \
                patch('eitr_plugins.subprocess.Popen') as popen:
            popen.return_value.wait.side_effect = [7, 0]
            self.manager.hooks('theme-changed')
            self.assertEqual(popen.call_count, 2)


class VisualPluginTests(unittest.TestCase):
    setUp = PluginTests.setUp
    git = PluginTests.git
    spec = PluginTests.spec
    block = PluginTests.block
    cli = PluginTests.cli
    commit_as = PluginTests.commit_as
    write_spec = PluginTests.write_spec
    publish = PluginTests.publish
    install = PluginTests.install

    def visual(self):
        for name in ('HelloTile.qml', 'HelloPanel.qml', 'qmldir'):
            shutil.copy(ROOT / 'distro/plugins/example' / name, self.source / name)
        value = self.spec()
        value['schemaVersion'] = 2
        value['ui'] = {'tiles': [{'id': 'hello', 'title': 'Hello', 'qml': 'HelloTile.qml',
                                  'dataCommand': {'run': 'notify.sh'}, 'refreshInterval': 1000}],
                       'panels': [{'id': 'hello-panel', 'title': 'Hello status', 'qml': 'HelloPanel.qml'}]}
        value['ui']['widgets'] = [{'id': 'clock', 'title': 'Clock', 'qml': 'HelloPanel.qml',
                                   'minWidth': 96, 'minHeight': 96, 'defaultWidth': 240, 'defaultHeight': 144}]
        value['ui']['barItems'] = [{'id': 'dot', 'title': 'Status', 'qml': 'HelloTile.qml', 'panel': 'hello-panel'}]
        return value

    def test_v2_valid_and_v1_unchanged(self):
        value = self.visual()
        self.write_spec(value)
        self.assertEqual(plugins.manifest(self.source), value)
        value['schemaVersion'] = 1
        self.write_spec(value)
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)
        value.pop('ui')
        self.write_spec(value)
        self.assertEqual(plugins.manifest(self.source), value)

    def test_visual_only_plugin_needs_no_rows(self):
        value = self.visual()
        value['rows'] = []
        self.write_spec(value)
        self.assertEqual(plugins.manifest(self.source)['rows'], [])
        value.pop('ui')
        self.write_spec(value)
        with self.assertRaisesRegex(ValueError, '1..20 rows'):
            plugins.manifest(self.source)

    def test_tile_panel_reference_validation(self):
        value = self.visual()
        value['ui']['tiles'][0]['panel'] = 'missing'
        with self.assertRaises(ValueError):
            plugins.validate_ui(self.source, value['ui'])
        value['ui']['tiles'][0]['panel'] = 'hello-panel'
        plugins.validate_ui(self.source, value['ui'])
        value['ui']['panels'][0]['panel'] = 'hello-panel'
        with self.assertRaises(ValueError):
            plugins.validate_ui(self.source, value['ui'])
        value['ui']['panels'] = None
        with self.assertRaises(ValueError):
            plugins.validate_ui(self.source, value['ui'])

    def test_ui_validation(self):
        for field, invalid in [('qml', '../HelloTile.qml'), ('qml', '/tmp/HelloTile.qml'),
                               ('qml', 'notify.sh'), ('qml', 'missing.qml'), ('id', 'Bad id'),
                               ('refreshInterval', True), ('refreshInterval', 999),
                               ('refreshInterval', 3600001), ('dataCommand', {'run': '/bin/true'}),
                               ('unknown', 'value')]:
            value = self.visual()
            value['ui']['tiles'][0][field] = invalid
            self.write_spec(value)
            with self.subTest(field=field, invalid=invalid), self.assertRaises((ValueError, OSError)):
                plugins.manifest(self.source)
        value = self.visual()
        value['ui']['panels'][0]['id'] = 'hello'
        self.write_spec(value)
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)
        value = self.visual()
        value['ui']['tiles'] *= 9
        self.write_spec(value)
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)
        self.write_spec(self.visual())
        (self.source / 'HelloTile.qml').write_text('x' * 65537)
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)

    def test_review_shows_every_qml_full_source_and_flags(self):
        value = self.visual()
        self.write_spec(value)
        lines = self.cli().review_lines(self.source, value, self.url)
        for name in ('HelloTile.qml', 'HelloPanel.qml'):
            self.assertIn('QML: ' + name, lines)
            for line in (self.source / name).read_text().splitlines():
                self.assertIn(plugins.printable(line), lines)
        self.assertTrue(any('QML runs inside the bar' in flag for flag in plugins.add_flags(self.source, value)))
        self.install()
        (self.source / 'HelloTile.qml').write_text('import QtQuick\nItem { required property var api }\n')
        self.commit_as('Fixture')
        observed = []
        self.manager.update('example', lambda changes: observed.append(changes) or False)
        self.assertTrue(any('QML added, changed or removed' in flag for flag in observed[0]['flags']))

    def test_failure_threshold_persistence_and_reenable(self):
        self.publish(self.visual())
        approved = self.install()
        for count in range(1, 4):
            outcome = self.manager.ui_failure('example', approved, 'broken\x1b')
            self.assertEqual(outcome, {'failures': count, 'disabled': count == 3})
        self.assertTrue(all(entry['disabled'] for entry in self.manager.ui()))
        self.assertIn('broken?', plugins.state('eitr/plugin-ui.log').read_text())
        with self.assertRaises(ValueError):
            self.manager.ui_failure('example', '0' * 40)
        cli = self.cli()
        with patch.object(cli, 'Plugins', return_value=self.manager):
            self.assertEqual(cli.main(['enable-ui', 'example']), 0)
        self.assertTrue(all(not entry['disabled'] for entry in self.manager.ui()))
        self.block(id='example')
        self.assertEqual(self.manager.ui(), [])

    def test_data_helper_only_runs_declared_command(self):
        self.publish(self.visual())
        self.install()
        entries = self.manager.ui()
        self.assertTrue(entries)
        self.assertTrue(all(entry['pluginName'] == self.visual()['name'] for entry in entries))
        with patch.object(self.manager, 'ui', return_value=entries), patch('eitr_plugins.subprocess.Popen') as process:
            process.return_value.wait.return_value = 0
            self.assertEqual(self.manager.ui_data('example', 'hello'), '')
            self.assertEqual(process.call_args.args[0][0], str(self.manager.folder / 'example/notify.sh'))
            with self.assertRaises(ValueError):
                self.manager.ui_data('example', 'undeclared')
            self.assertEqual(process.call_count, 1)

    def test_widget_dimensions_and_bar_panel_validation(self):
        for field, invalid in [('minWidth', True), ('defaultWidth', 95), ('minHeight', 0),
                               ('defaultHeight', 4097), ('defaultHeight', '200')]:
            value = self.visual()
            value['ui']['widgets'][0][field] = invalid
            with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                plugins.validate_ui(self.source, value['ui'])
        value = self.visual()
        value['ui']['barItems'][0]['panel'] = 'missing'
        with self.assertRaises(ValueError):
            plugins.validate_ui(self.source, value['ui'])
        value = self.visual()
        value['ui']['barItems'][0]['id'] = 'clock'
        with self.assertRaises(ValueError):
            plugins.validate_ui(self.source, value['ui'])

    def test_explicit_placements_persist_when_monitor_disappears(self):
        self.publish(self.visual())
        self.install()
        self.assertEqual(self.manager.placements(), dict(version=2, widgets=[], barItems=[]))
        self.manager.place('example', 'clock', 'DP-test')
        self.manager.place('example', 'dot')
        geometry = dict(x=60, y=90, width=300, height=180)
        self.manager.place('example', 'clock', 'DP-test', geometry=geometry)
        saved = self.manager.placements()
        self.assertEqual(saved['widgets'][0], dict(plugin='example', id='clock', monitor='DP-test', aboveWindows=False, **geometry))
        self.assertEqual(plugins.Plugins().placements(), saved)
        # Querying or disabling declarations never rewrites user placements.
        for _ in range(3):
            self.manager.ui_failure('example', self.manager.records()['example']['commit'])
        self.manager.ui()
        self.assertEqual(self.manager.placements(), saved)
        self.manager.enable_ui('example')
        self.assertEqual(self.manager.placements(), saved)
        self.manager.place('example', 'clock', 'DP-test', remove=True)
        self.manager.place('example', 'dot', remove=True)
        self.assertEqual(self.manager.placements(), dict(version=2, widgets=[], barItems=[]))

    def test_placement_validation_and_visual_menu_reenable(self):
        self.publish(self.visual())
        approved = self.install()
        with self.assertRaises(ValueError):
            self.manager.place('example', 'clock', 'DP-test', geometry=dict(x=0, y=0, width=2, height=2))
        with self.assertRaises(ValueError):
            self.manager.place('example', 'unknown')
        self.manager.place('example', 'clock', 'missing-monitor')
        for _ in range(3):
            self.manager.ui_failure('example', approved)
        rows = self.cli().visual_rows(self.manager, 'example', ['connected-monitor'])
        labels = [row['text'] for row in rows]
        self.assertEqual(labels, sorted(labels, key=str.casefold))
        self.assertIn('Re-enable visuals', labels)
        self.assertTrue(any('missing-monitor' in label and label.startswith('Remove') for label in labels))
        self.assertTrue(any('connected-monitor' in label and label.startswith('Add') for label in labels))
        self.assertTrue(all(row['subtext'] and row['actions']['open'] for row in rows))
        command = next(row['actions']['open'] for row in rows if row['text'] == 'Re-enable visuals')
        import shlex
        with patch.object(self.cli(), 'Plugins', return_value=self.manager):
            self.assertIn('enable-ui', shlex.split(command))
        self.manager.enable_ui('example')
        self.assertNotIn('Re-enable visuals', [row['text'] for row in self.cli().visual_rows(self.manager, 'example', [])])


class LivePluginTests(unittest.TestCase):
    setUp = PluginTests.setUp
    git = PluginTests.git
    spec = PluginTests.spec
    block = PluginTests.block
    cli = PluginTests.cli
    commit_as = PluginTests.commit_as
    write_spec = PluginTests.write_spec
    publish = PluginTests.publish
    install = PluginTests.install
    visual = VisualPluginTests.visual

    def test_enabled_state_stops_all_execution_and_preserves_placements(self):
        value = self.visual()
        value['service'] = {'run': 'notify.sh'}
        self.publish(value)
        self.install()
        self.manager.place('example', 'clock', 'test-monitor')
        placements = self.manager.placements()
        self.manager.set_enabled('example', False)
        self.assertFalse(self.manager.records()['example']['enabled'])
        self.assertEqual(self.manager.rows(), [])
        self.assertEqual(self.manager.ui(), [])
        self.assertEqual(self.manager.placements(), placements)
        self.assertFalse(self.manager.installed()[0]['enabled'])
        self.assertIn(unittest.mock.call('disable', '--now', 'eitr-plugin-example.service'), self.commands.call_args_list)
        with patch('eitr_plugins.subprocess.Popen') as process:
            self.manager.hooks('theme-changed')
            process.assert_not_called()
            with self.assertRaises(ValueError):
                self.manager.launch('example', 0)
            with self.assertRaises(ValueError):
                self.manager.ui_data('example', 'hello')
            process.assert_not_called()
        value['version'] = 'disabled-update'
        self.publish(value)
        self.commands.reset_mock()
        def service_call(*arguments):
            if arguments[0] == 'stop' and not self.manager.unit('example').exists():
                raise subprocess.CalledProcessError(5, arguments)
        with patch.object(self.manager, 'systemctl', side_effect=service_call):
            self.assertTrue(self.manager.update('example', lambda changes: True))
        self.assertFalse(self.manager.records()['example']['enabled'])
        self.assertFalse(self.manager.unit('example').exists())
        self.assertEqual(self.manager.placements(), placements)
        self.manager.set_enabled('example', True)
        self.assertTrue(self.manager.rows())
        self.assertTrue(self.manager.ui())
        self.assertEqual(self.manager.placements(), placements)
        self.assertIn(unittest.mock.call('enable', '--now', 'eitr-plugin-example.service'), self.commands.call_args_list)
        self.manager.set_enabled('example', False)
        self.block(id='example')
        with self.assertRaises(ValueError):
            self.manager.set_enabled('example', True)

    def test_author_appearance_validation(self):
        value = self.visual()
        plugins.validate_ui(self.source, value['ui'])
        for kind, field, valid, invalid in (
                ('tiles', 'look', ('eitr', 'custom'), ('theme', False, None, [])),
                ('panels', 'surface', ('none', 'panel'), ('blur', True, None, [])),
                ('panels', 'header', (True, False), ('false', 0, 1, None)),
                ('widgets', 'surface', ('none', 'panel'), ('blur', True, None, []))):
            entry = value['ui'][kind][0]
            for choice in valid:
                entry[field] = choice
                plugins.validate_ui(self.source, value['ui'])
            for choice in invalid:
                entry[field] = choice
                with self.assertRaises(ValueError):
                    plugins.validate_ui(self.source, value['ui'])
            del entry[field]

    def test_surface_default_override_and_validation(self):
        value = self.visual()
        value['ui']['widgets'][0]['surface'] = 'none'
        self.publish(value)
        self.install()
        self.manager.place('example', 'clock', 'test-monitor')
        self.assertEqual(next(entry for entry in self.manager.ui() if entry['id'] == 'clock')['surface'], 'none')
        self.manager.place('example', 'clock', 'test-monitor', surface='panel')
        saved = self.manager.placements()['widgets'][0]
        self.assertEqual(saved['surface'], 'panel')
        geometry = dict(x=63, y=78, width=330, height=198)
        self.manager.place('example', 'clock', 'test-monitor', geometry=geometry)
        self.assertEqual(self.manager.placements()['widgets'][0], dict(saved, **geometry))
        with self.assertRaises(ValueError):
            self.manager.place('example', 'clock', 'test-monitor', surface='blur')
        value['ui']['widgets'][0]['surface'] = 'blur'
        with self.assertRaises(ValueError):
            plugins.validate_ui(self.source, value['ui'])

    def test_artwork_headers_sizes_paths_and_review(self):
        from PIL import Image
        value = self.visual()
        Image.new('RGB', (128, 128)).save(self.source / 'icon.png')
        Image.new('RGB', (640, 360)).save(self.source / 'preview.jpg')
        value.update(icon='icon.png', preview='preview.jpg', homepage='https://example.invalid/plugin')
        self.write_spec(value)
        self.assertEqual(plugins.manifest(self.source), value)
        lines = self.cli().review_lines(self.source, value, self.url)
        self.assertIn('icon: icon.png', lines)
        self.assertIn('preview: preview.jpg', lines)
        for field, invalid in [('icon', '../icon.png'), ('icon', '/tmp/icon.png'), ('icon', 'notify.sh'),
                               ('preview', 'icon.svg'), ('homepage', 'http://example.invalid'),
                               ('homepage', 'https://user:password@example.invalid')]:
            with self.subTest(field=field, invalid=invalid):
                self.write_spec(dict(value, **{field: invalid}))
                with self.assertRaises((ValueError, OSError)):
                    plugins.manifest(self.source)
        self.write_spec(value)
        for dimensions in ((63, 63), (1025, 1025), (128, 64)):
            Image.new('RGB', dimensions).save(self.source / 'icon.png')
            with self.assertRaises(ValueError):
                plugins.manifest(self.source)
        (self.source / 'icon.png').write_bytes(b'\x89PNG\r\n\x1a\nnot an image')
        with self.assertRaises((ValueError, OSError)):
            plugins.manifest(self.source)
        (self.source / 'icon.png').write_bytes(b'x' * (512 * 1024 + 1))
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)
        (self.source / 'icon.png').unlink()
        (self.source / 'icon.png').symlink_to(self.source / 'preview.jpg')
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)
        (self.source / 'icon.png').unlink()
        Image.new('RGB', (128, 128)).save(self.source / 'icon.png')
        Image.new('RGB', (3841, 10)).save(self.source / 'preview.jpg')
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)
        Image.new('RGB', (640, 360)).save(self.source / 'preview.jpg')
        with (self.source / 'preview.jpg').open('ab') as output:
            output.write(b'x' * (2 * 1024 * 1024))
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)
        value.pop('preview')
        value['icon'] = 'icon.svg'
        self.write_spec(value)
        for svg in ('not svg', '<svg xmlns="http://www.w3.org/2000/svg" width="128" height="64"/>',
                    '<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128"><script/></svg>'):
            (self.source / 'icon.svg').write_text(svg)
            with self.assertRaises(ValueError):
                plugins.manifest(self.source)

    def test_iconless_legacy_keeps_working_but_new_v2_install_requires_icon(self):
        value = self.visual()
        value.pop('icon', None)
        self.write_spec(value)
        self.assertEqual(plugins.manifest(self.source), value)
        self.assertTrue(any('generic icon' in line for line in self.cli().review_lines(self.source, value, self.url)))
        self.publish(value)
        with self.assertRaisesRegex(ValueError, 'requires a plugin icon'):
            self.install()
        # Model an approval made before artwork became mandatory.
        self.manager.folder.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.source, self.manager.folder / 'example')
        self.manager.save({'example': dict(id='example', url=self.url, commit=plugins.commit(self.source), installed='fixture')})
        self.assertTrue(self.manager.ui())
        self.assertEqual(self.manager.installed()[0]['icon'], '')
        value['version'] = 'legacy-update'
        self.publish(value)
        self.assertTrue(self.manager.update('example', lambda changes: True))
        self.assertTrue(self.manager.ui())


    def test_capabilities_and_stream_validation(self):
        value = self.visual()
        value['capabilities'] = ['audio-spectrum']
        value['ui']['widgets'][0]['dataStream'] = {'run': 'notify.sh', 'arguments': ['fixed']}
        self.write_spec(value)
        self.assertEqual(plugins.manifest(self.source), value)
        for capabilities in (['microphone'], ['audio-spectrum', 'audio-spectrum'], 'audio-spectrum', [True], [{}], None):
            with self.subTest(capabilities=capabilities):
                invalid = dict(value, capabilities=capabilities)
                self.write_spec(invalid)
                with self.assertRaises(ValueError):
                    plugins.manifest(self.source)
        for stream in ('notify.sh', {'run': '/bin/true'}, {'run': '../notify.sh'}, {'run': 'notify.sh', 'shell': True}):
            invalid = copy.deepcopy(value)
            invalid['ui']['widgets'][0]['dataStream'] = stream
            self.write_spec(invalid)
            with self.assertRaises(ValueError):
                plugins.manifest(self.source)
        value['schemaVersion'] = 1
        value.pop('ui')
        self.write_spec(value)
        with self.assertRaises(ValueError):
            plugins.manifest(self.source)

    def test_live_review_and_update_risks(self):
        original = self.visual()
        self.publish(original)
        self.install()
        value = copy.deepcopy(original)
        value['capabilities'] = ['audio-spectrum']
        value['ui']['widgets'][0]['dataStream'] = {'run': 'notify.sh'}
        self.publish(value)
        lines = self.cli().review_lines(self.source, value, self.url)
        self.assertTrue(any('levels only, no audio is recorded or sent' in line for line in lines))
        self.assertTrue(any('dataStream: notify.sh' in line for line in lines))
        reviews = []
        self.manager.update('example', lambda changes: reviews.append(changes) or False)
        self.assertTrue(any('spectrum' in flag for flag in reviews[0]['flags']))
        self.assertTrue(any('dataStream' in flag for flag in reviews[0]['flags']))
        self.assertTrue(any('levels only' in line for line in self.cli().summary_lines(reviews[0])))
        self.assertTrue(any('dataStream: notify.sh' in line for line in self.cli().summary_lines(reviews[0])))
        unchanged = dict(reviews[0], flags=[])
        self.assertTrue(any('levels only' in line for line in self.cli().summary_lines(unchanged)))
        self.assertFalse(plugins.live_flags(value, value))

    def test_layer_migration_and_toggle(self):
        self.publish(self.visual())
        self.install()
        path = plugins.config('eitr/plugin-placements.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        old = dict(version=1, widgets=[dict(plugin='example', id='clock', monitor='test', x=24, y=24, width=240, height=144)], barItems=[])
        path.write_text(json.dumps(old))
        migrated = self.manager.placements()
        self.assertEqual(migrated['version'], 2)
        self.assertFalse(migrated['widgets'][0]['aboveWindows'])
        self.assertEqual(json.loads(path.read_text()), old)
        self.manager.place('example', 'clock', 'test', toggle_layer=True)
        self.assertTrue(self.manager.placements()['widgets'][0]['aboveWindows'])
        self.manager.place('example', 'clock', 'test', geometry=dict(x=0, y=0, width=300, height=200))
        self.assertTrue(self.manager.placements()['widgets'][0]['aboveWindows'])
        rows = self.cli().visual_rows(self.manager, 'example', ['test'])
        self.assertTrue(any(row['text'].startswith('Show behind windows · Clock · test') and 'toggle-layer' in row['actions']['open'] for row in rows))
        migrated['widgets'][0]['aboveWindows'] = 'yes'
        path.write_text(json.dumps(migrated))
        with self.assertRaises(ValueError):
            self.manager.placements()

    def test_stream_bounds(self):
        from eitr_plugin_stream import Lines, MAX_LINE, MAX_RATE
        parser = Lines()
        self.assertEqual(parser.feed(b'part', 1), [])
        self.assertEqual(parser.feed(b'ial\nnext\n', 1), ['partial', 'next'])
        self.assertEqual(len(parser.feed(b'x\n' * 100, 1)), MAX_RATE - 2)
        self.assertEqual(parser.feed(b'x\n', 2), ['x'])
        self.assertEqual(parser.feed(b'x' * (MAX_LINE + 1), 2), [])
        self.assertLessEqual(len(parser.pending), MAX_LINE)
        self.assertEqual(parser.feed(b'more\nvalid\n', 2), ['valid'])
        self.assertEqual(parser.feed(b'x' * MAX_LINE + b'\n', 3), ['x' * MAX_LINE])

    def test_stream_supervisor_cleans_up_descendants(self):
        import time
        marker = self.home / 'child'
        script = self.home / 'stream.py'
        script.write_text('''import subprocess, sys, time
from pathlib import Path
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
Path(sys.argv[1]).write_text(str(child.pid))
print('ready', flush=True)
time.sleep(60)
''')
        for shutdown in ('terminate', 'kill'):
            with self.subTest(shutdown=shutdown):
                supervisor = subprocess.Popen([sys.executable, '-c',
                    'from pathlib import Path; from eitr_plugin_stream import run_stream; import sys; run_stream(sys.argv[1:], Path.cwd())',
                    sys.executable, str(script), str(marker)], stdout=subprocess.PIPE, text=True)
                try:
                    import selectors
                    with selectors.DefaultSelector() as selector:
                        selector.register(supervisor.stdout, selectors.EVENT_READ)
                        self.assertTrue(selector.select(3), 'Stream did not start')
                        self.assertEqual(supervisor.stdout.readline().strip(), 'ready')
                    child_pid = int(marker.read_text())
                    getattr(supervisor, shutdown)()
                    supervisor.wait(timeout=3)
                    for attempt in range(30):
                        status = Path(f'/proc/{child_pid}/stat')
                        if not status.exists() or status.read_text().split()[2] == 'Z':
                            break
                        time.sleep(.02)
                    else:
                        self.fail('Stream child survived supervisor unload')
                finally:
                    if supervisor.poll() is None:
                        supervisor.kill()
                        supervisor.wait()
                    supervisor.stdout.close()
