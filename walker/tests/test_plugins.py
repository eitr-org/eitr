"""Plugin fixtures never run plugin code or reach the real user service manager."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
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
        self.manager = plugins.Plugins(allow_file=True)
        self.systemctl = patch.object(self.manager, 'systemctl')
        self.commands = self.systemctl.start()
        self.addCleanup(self.systemctl.stop)

    def git(self, root, *arguments):
        return plugins.git(root, *arguments, allow_file=True)

    def spec(self):
        return json.loads((self.source / 'eitr-plugin.json').read_text())

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
        self.assertTrue(self.manager.add(self.url, lambda *details: True))
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
        for url in ('file:///tmp/plugin', 'http://example.com/repo', 'https://user:password@example.com/repo', '-upload-pack=evil', 'ssh://example.com/repo'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                plugins.repository_url(url)
        self.assertEqual(plugins.repository_url('https://example.com/repo.git'), 'https://example.com/repo.git')

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
            self.assertFalse(self.manager.add(self.url, refuse))
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
        def approve(spec, previous, current, subjects, changed):
            self.assertEqual(previous, old)
            self.assertIn('Updated plugin', subjects)
            self.assertIn('revision', changed)
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
            self.manager.add(self.url, lambda *details: True)

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
        self.assertFalse(self.manager.add(self.url, refuse))
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
            local fixtures = {rows = %s, installed = {{id="example", name="Example plugin"}}}
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
                        assert(entry.State[1] == "submenu" and entry.Subtext == nil)
                    else
                        assert(entry.Subtext and entry.Subtext ~= "")
                    end
                    print(name .. " | " .. entry.Text .. " | " .. (entry.SubMenu or entry.Subtext))
                end
            end
        ''' % lua_rows(rows)
        environment = dict(os.environ, EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'), EITR_CODE_ROOT=str(ROOT))
        result = subprocess.run(['lua', '-e', harness], cwd=ROOT, env=environment, capture_output=True, text=True, check=True)
        self.assertIn('plugins | Example notification | Show a greeting', result.stdout)
        self.assertIn('plugins-install | Example plugin | plugin-actions', result.stdout)
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
                self.manager.add(self.url, lambda *details: True)
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
        def approve(spec, *details):
            spec['name'] = 'not the reviewed manifest'
            return True
        with self.assertRaises(ValueError):
            self.manager.update('example', approve)
        self.assertEqual(plugins.commit(self.manager.folder / 'example'), old)
        self.assertEqual(self.manager.records()['example']['commit'], old)
