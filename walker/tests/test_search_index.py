import importlib.util
import json
import os
import shutil
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('search_index',
    Path(__file__).parents[1] / 'scripts/menus/search-index.py')
search = importlib.util.module_from_spec(spec)
spec.loader.exec_module(search)


class SearchIndexTests(unittest.TestCase):
    item = dict(provider='menus:toggle', identifier='toggle:abc', text='Idle Lock',
                actions=['open'], icon='lock')

    def output(self, *items):
        return '\n'.join(json.dumps({'item': item}) for item in items)

    def test_battery_folder_and_choices_are_not_indexed_without_system_battery(self):
        folder = dict(self.item, provider='menus:system-devices', text='Battery Charge Limit')
        choice = dict(self.item, provider='menus:battery-limit', text='Charge Limit 80%')
        definitions = {'system-devices': {'entries': [{'text': 'Battery Charge Limit', 'submenu': 'battery-limit'}]}}
        with patch.object(search, 'system_batteries', return_value=[]):
            self.assertEqual(search.snapshot(self.output(folder, choice), menus=definitions), [])
        with patch.object(search, 'system_batteries', return_value=[Path('/mock/BAT0')]):
            self.assertEqual(len(search.snapshot(self.output(folder, choice), menus=definitions)), 2)

    def test_private_clipboard_and_index_are_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('main.toml', 'clipboard.lua', 'search-index.lua', 'apps.lua'):
                (root / name).touch()
            self.assertEqual(search.providers(root), ['menus:apps', 'menus:main'])
        self.assertEqual(search.snapshot(self.output(dict(self.item, provider='menus:clipboard'))), [])

    def test_search_keeps_cloud_accounts_but_not_what_lies_below_them(self):
        # Below an account (services, resources, logs) is searched only inside the
        # opened menu; the background index never queries resource pickers either.
        indexed = set(search.providers())
        for name in json.loads(search.CLOUD_MENUS.read_text()):
            with self.subTest(menu=name):
                self.assertNotIn('menus:' + name, indexed)
        for name in ('gcp-projects', 'gcp-logs-minutes', 'azure-logs-minutes'):
            self.assertNotIn('menus:' + name, indexed)
        for name in ('aws-profiles', 'gcp-contexts', 'azure-contexts', 'cloud'):
            self.assertIn('menus:' + name, indexed)

    def test_keyboard_layouts_stay_out_of_search(self):
        indexed = set(search.providers())
        self.assertNotIn('menus:keyboard', indexed)
        self.assertNotIn('menus:keyboard-add', indexed)

    def test_menus_below_an_account_are_found_through_their_parents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'main.toml').touch()
            (root / 'aws-profiles.lua').write_text('Parent = "cloud"\n')
            (root / 'aws-account.lua').write_text('Parent = "aws-profiles"\n')
            (root / 'aws-deep-logs.lua').write_text('Parent = "aws-ecs"\n')
            (root / 'aws-ecs.lua').write_text('Parent = "aws-account"\n')
            self.assertEqual(search.providers(root), ['menus:aws-profiles', 'menus:main'])

    def test_snapshot_deduplicates_and_keeps_actions_without_shell_code(self):
        rows = search.snapshot(self.output(self.item, self.item),
                               {('menus:toggle', 'Idle Lock'): ['idle']})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['keywords'], ['idle'])
        self.assertEqual(rows[0]['actions'], ['open'])
        self.assertNotIn('command', rows[0])

    def test_refresh_is_atomic_private_and_only_queries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = root / 'runtime/index.json'
            with patch.object(search, 'RUNTIME', index.parent), patch.object(search, 'INDEX', index), \
                    patch.object(search, 'providers', return_value=['menus:toggle']), \
                    patch.object(search, 'keyword_index', return_value={}), \
                    patch.object(search.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, self.output(self.item))) as run:
                search.refresh()
                self.assertEqual(index.stat().st_mode & 0o777, 0o600)
                self.assertEqual(index.parent.stat().st_mode & 0o777, 0o700)
                self.assertEqual(len(search.read_index()['rows']), 1)
                self.assertEqual(run.call_args.args[0][1], 'query')

    def test_global_apps_only_offer_launch(self):
        app = dict(self.item, provider='menus:apps', actions=['open', 'app_uninstall'])
        row = search.snapshot(self.output(app))[0]
        self.assertEqual(row['actions'], ['open'])
        row['actions'].append('app_uninstall')  # Reject old cached actions too.
        with patch.object(search, 'read_index', return_value={'rows': [row]}), \
                patch.object(search.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                search.activate(row['key'], 'app_uninstall')
            run.assert_not_called()

    def test_global_app_launch_has_enter_binding_not_delete(self):
        import tomllib
        config = tomllib.loads((Path(__file__).parents[1] / 'config.toml').read_text())
        fallback = config['providers']['actions']['fallback']
        launch = next(action for action in fallback if action['action'] == 'app_launch')
        self.assertEqual(launch['bind'], 'Return')
        self.assertNotIn('app_uninstall', [action['action'] for action in fallback])
        self.assertIn('app_uninstall', [action['action'] for action in config['providers']['actions']['menus:apps']])

    def test_fresh_cache_does_not_rebuild(self):
        with patch.object(search, 'read_index', return_value={'rows': [self.item]}), \
                patch.object(search, 'fresh', return_value=True), \
                patch.object(search, 'refresh') as refresh, patch.object(search.subprocess, 'Popen') as start:
            search.prepare()
            refresh.assert_not_called()
            start.assert_not_called()

    def test_stale_cache_refreshes_off_the_typing_path(self):
        with patch.object(search, 'read_index', return_value={'rows': [self.item]}), \
                patch.object(search, 'fresh', return_value=False), \
                patch.object(search.subprocess, 'Popen') as start:
            search.prepare()
            self.assertTrue(start.call_args.kwargs['start_new_session'])

    def test_warm_waits_for_elephant_then_builds_a_missing_index_once(self):
        answers = iter([1, 1, 0])
        with patch.object(search.subprocess, 'run', side_effect=lambda *arguments, **options:
                          subprocess.CompletedProcess(arguments, next(answers))) as run, \
                patch.object(search.time, 'sleep') as sleep, \
                patch.object(search, 'read_index', return_value={}), patch.object(search, 'refresh') as refresh:
            search.warm()
        self.assertEqual(run.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        refresh.assert_called_once_with()
        with patch.object(search.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)), \
                patch.object(search, 'fresh', return_value=True), patch.object(search, 'read_index', return_value={'rows': [1]}), \
                patch.object(search, 'refresh') as refresh:
            search.warm()
        refresh.assert_not_called()

    def test_activation_routes_to_original_provider(self):
        row = search.snapshot(self.output(self.item))[0]
        with patch.object(search, 'read_index', return_value={'rows': [row]}), \
                patch.object(search.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, self.output(self.item))) as run:
            search.activate(row['key'], 'open')
            self.assertEqual(run.call_args.args[0], ['elephant', 'activate', 'menus:toggle;toggle:abc;open;;'])

    def test_unknown_actions_and_expired_entries_do_not_execute(self):
        row = search.snapshot(self.output(self.item))[0]
        with patch.object(search, 'read_index', return_value={'rows': [row]}), \
                patch.object(search.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                search.activate(row['key'], 'shutdown')
            run.assert_not_called()
        with patch.object(search, 'read_index', return_value={'rows': [row]}), \
                patch.object(search.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '')) as run:
            with self.assertRaises(ValueError):
                search.activate(row['key'], 'open')
            self.assertEqual(run.call_count, 1)

    def test_rows_know_their_ancestors_and_data_submenus(self):
        with tempfile.TemporaryDirectory() as directory:
            elephant = Path(directory) / 'elephant'
            menus, rows = elephant / 'menus', elephant / 'menu-rows'
            menus.mkdir(parents=True)
            rows.mkdir()
            (menus / 'settings.lua').write_text('Name = "settings"\nParent = "main"\n')
            (rows / 'settings.json').write_text(json.dumps([{'text': 'Security', 'subtext': '>', 'submenu': 'security'}]))
            (menus / 'security.toml').write_text('name = "security"\nparent = "settings"\n'
                                                 '[[entries]]\ntext = "Fingerprint"\nsubmenu = "fingerprint"\n')
            (menus / 'git-accounts.lua').write_text('Name = "git-accounts"\nParent = "development"\n')
            parents, definitions = search.parents(menus), search.definitions(menus)
        self.assertEqual(parents, {'settings': 'main', 'security': 'settings', 'git-accounts': 'development'})
        output = self.output(
            dict(provider='menus:security', identifier='menus:fingerprint::1', text='Fingerprint', actions=['menus:open']),
            dict(provider='menus:settings', identifier='security:settings:2', text='Security', actions=['menus:open']),
            dict(provider='menus:git-accounts', identifier='menus:git-account::3', text='Work', actions=['menus:open']))
        rows = {row['text']: row for row in search.snapshot(output, {}, parents, definitions)}
        self.assertEqual(rows['Fingerprint']['menus'], ['settings', 'main'])
        self.assertEqual(rows['Fingerprint']['submenu'], 'fingerprint')
        self.assertEqual(rows['Security']['submenu'], 'security')
        # A generated menu's submenu needs the selected row's value; it keeps the helper.
        self.assertNotIn('submenu', rows['Work'])
        self.assertEqual(rows['Work']['menus'], ['development'])

    @unittest.skipUnless(shutil.which('lua'), 'Lua is required for search presentation tests')
    def test_live_accounts_show_assistant_path_and_fixed_rows_keep_their_description(self):
        from test_menu_translations import lua_value

        parent_of = {'ai-tools': 'development', 'development': 'main',
                     'ai-claude': 'ai-tools', 'ai-codex': 'ai-tools',
                     'ai-claude-accounts': 'ai-claude', 'ai-codex-accounts': 'ai-codex'}
        menus = {'ai-claude': {'entries': [
                    {'text': 'Accounts', 'subtext': '>', 'submenu': 'ai-claude-accounts'},
                    {'text': 'New', 'subtext': 'Start a Claude session'}]},
                 'ai-codex': {'entries': [
                    {'text': 'Accounts', 'subtext': '>', 'submenu': 'ai-codex-accounts'}]}}
        accounts = [dict(provider='menus:' + menu + '-accounts', identifier=menu + ':add',
                         text='Add Account…', subtext='Accounts: Sign in to a separate account', actions=['open'])
                    for menu in ('ai-claude', 'ai-codex')]
        folders = [dict(provider='menus:ai-tools', identifier='menus:' + menu + ':ai-tools:folder',
                        text=title, actions=['menus:open'])
                   for menu, title in (('ai-claude', 'Claude'), ('ai-codex', 'Codex'))]
        fixed = dict(provider='menus:ai-claude', identifier='ai-claude:new', text='New',
                     subtext='Claude: Start a Claude session', actions=['open'])
        # Account rows precede folder rows to exercise the two-pass label lookup.
        rows = search.snapshot(self.output(*accounts, fixed, *folders), parent_of=parent_of, menus=menus)
        by_identifier = {row['identifier']: row for row in rows}
        self.assertEqual(by_identifier['ai-claude:add']['path'][-2:], [
            {'menu': 'ai-claude', 'title': 'Claude'}, {'menu': 'ai-claude-accounts', 'title': 'Accounts'}])
        fixed_row = by_identifier['ai-claude:new']
        self.assertNotIn('path', fixed_row)
        self.assertEqual(fixed_row['subtext'], fixed['subtext'])
        root = Path(__file__).resolve().parents[2]
        script = 'local index = ' + lua_value({'rows': rows}) + '\n' + r'''
local root = os.getenv('EITR_CODE_ROOT')
local original_dofile = dofile
dofile = function(path)
    if path == root .. '/elephant/battery-state.lua' then return function() return {available=true} end end
    if path == root .. '/elephant/policies.lua' then return {row=function() return true end} end
    return original_dofile(path)
end
io.popen = function() error('Search must not run provider commands') end
os.execute = io.popen
io.open = function(path)
    assert(path == os.getenv('XDG_RUNTIME_DIR') .. '/eitr-search/index.json')
    return {read=function() return 'index' end, close=function() end}
end
jsonDecode = function(raw) assert(raw == 'index'); return index end
local search = dofile(root .. '/elephant/search-index-entries.lua')
local rows = search('ai-tools')
local expected = {['menus:ai-claude-accounts']='Claude › Accounts: Sign in to a separate account',
                  ['menus:ai-codex-accounts']='Codex › Accounts: Sign in to a separate account'}
local found=0
for _, entry in ipairs(rows) do
    if expected[entry.Provider] then
        assert(entry.Text == 'Add Account…')
        assert(entry.Subtext == expected[entry.Provider], tostring(entry.Subtext))
        assert(entry.Actions.open:find('activate',1,true))
        found=found+1
    elseif entry.Text == 'New' then
        assert(entry.Subtext == 'Claude: Start a Claude session')
        assert(entry.Provider == 'menus:ai-claude')
    end
end
assert(found == 2)
-- The path is relative to the searched menu, not a global breadcrumb.
for _, entry in ipairs(search('ai-claude')) do
    if entry.Text == 'Add Account…' then
        assert(entry.Subtext == 'Accounts: Sign in to a separate account')
    end
end
-- Search must not mutate the cached index or its fixed-row presentation.
assert(search('ai-tools')[1].Subtext == rows[1].Subtext)
'''
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(['lua', '-'], input=script, text=True, capture_output=True,
                                    env=dict(os.environ, EITR_CODE_ROOT=str(root),
                                             EITR_LIBRARY_ROOT=str(root / 'distro/lib'), XDG_RUNTIME_DIR=temporary))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_menu_with_submenus_searches_below_itself(self):
        root = Path(__file__).parents[2] / 'elephant'
        for path in (root / 'menus').glob('*.toml'):
            with self.subTest(menu=path.stem):
                self.assertNotIn('\nsubmenu = ', path.read_text())
        for rows in (root / 'menu-rows').glob('*.json'):
            with self.subTest(menu=rows.stem):
                lua = (root / 'menus' / f'{rows.stem}.lua').read_text()
                self.assertIn(f'Name = "{rows.stem}"', lua)
                call = f'dofile(paths.code("elephant/scoped-menu.lua"))("{rows.stem}"'
                self.assertRegex(lua, re.escape(call) + r'(?:\)|,\s*function\()')
                self.assertIn('FixedOrder = true', lua)

    def test_lua_search_only_reads_the_index(self):
        root = Path(__file__).parents[2] / 'elephant'
        lua = (root / 'search-index-entries.lua').read_text()
        self.assertIn('io.open(', lua)
        for menu in (root / 'search-index-entries.lua', root / 'scoped-menu.lua', root / 'menus/search-index.lua',
                     root / 'menus/main.lua'):
            with self.subTest(menu=menu.name):
                self.assertNotIn('io.popen(', menu.read_text())
                self.assertNotIn('os.execute(', menu.read_text())


if __name__ == '__main__':
    unittest.main()
