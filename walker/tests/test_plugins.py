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
            jsonDecode = function(action) return fixtures[action] end
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
