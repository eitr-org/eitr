import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
CLOUD = ROOT / 'walker/scripts/menus/cloud'
sys.path.insert(0, str(CLOUD))
spec = importlib.util.spec_from_file_location('navigation', CLOUD / 'navigation.py')
navigation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(navigation)


class CloudNavigationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.state = Path(self.temporary.name) / 'navigation.json'
        self.patcher = patch.object(navigation, 'state_path', return_value=self.state)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def select(self, provider='aws', value='test-profile'):
        with patch.object(navigation, 'show'):
            navigation.select(provider, value)

    def test_every_parent_is_the_real_previous_menu(self):
        for name, menu in navigation.MENUS.items():
            with self.subTest(menu=name):
                source = (ROOT / 'elephant/menus' / (name + '.lua')).read_text()
                self.assertIn('Parent = ' + json.dumps(menu['parent']), source)
                self.assertTrue((ROOT / 'walker/themes/current' / ('item_menus-' + name + '.xml')).is_file())
                visited = {name}
                parent = menu['parent']
                while parent in navigation.MENUS:
                    self.assertNotIn(parent, visited)
                    visited.add(parent)
                    parent = navigation.MENUS[parent]['parent']
                self.assertEqual(parent, 'aws-profiles' if menu['provider'] == 'aws' else menu['provider'] + '-contexts')
                for action in menu.get('actions', []):
                    if action.get('submenu'):
                        self.assertEqual(navigation.MENUS[action['submenu']]['parent'], name)
                if menu.get('next'):
                    self.assertEqual(navigation.MENUS[menu['next']]['parent'], name)

    def test_all_aws_service_menus_return_directly_to_account(self):
        for name, menu in navigation.MENUS.items():
            if menu.get('script') and name != 'aws-account' and menu['provider'] == 'aws':
                self.assertEqual(menu['parent'], 'aws-account', name)

    def test_account_choice_saves_private_state_and_clears_resources(self):
        self.select()
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o600)
        state = navigation.read_state()
        state['aws']['picks']['choose_vpc'] = 'old-vpc'
        navigation.write_state(state)
        self.select(value='another-profile')
        self.assertEqual(navigation.selected('aws'), {'selection': 'another-profile', 'picks': {}})

    def test_entries_read_current_selection_and_folders_precede_actions(self):
        self.select()
        first = navigation.entries('aws-account')
        self.assertTrue(any('test-profile' in row.get('Subtext', '') for row in first))
        self.select(value='second-profile')
        rows = navigation.entries('aws-account')
        self.assertTrue(any('second-profile' in row.get('Subtext', '') for row in rows))
        self.assertFalse(any('test-profile' in row.get('Subtext', '') for row in rows))
        self.assertEqual(rows, sorted(rows, key=lambda row: (not bool(row.get('SubMenu')), row['Text'].casefold())))

    def test_resource_query_uses_saved_profile_and_normalizes_display_rows(self):
        self.select()
        menu = navigation.MENUS['aws-vpc-subnets-1']
        with patch.object(navigation.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'Friendly VPC  vpc-123\n')) as run:
            self.assertEqual(navigation.resource_rows(menu, navigation.selected('aws')), [('Friendly VPC  vpc-123', 'vpc-123')])
        self.assertEqual(run.call_args.kwargs['env']['AWS_PROFILE'], 'test-profile')
        self.assertIn('choose_vpc', run.call_args.args[0])

    def test_dispatch_retains_action_commands_and_real_menu_return(self):
        self.select()
        with patch.object(navigation.subprocess, 'run') as run:
            navigation.run('aws-s3', '\U000f024b  List buckets')
        environment = run.call_args.kwargs['env']
        self.assertEqual(environment['AWS_PROFILE'], 'test-profile')
        self.assertEqual(environment['EITR_CLOUD_ACTION'], '\U000f024b  List buckets')
        self.assertEqual(environment['CLOUD_MENU_RETURN_COMMAND'], navigation.command('show', 'aws-s3'))
        self.assertEqual(run.call_args.args[0][-1], 'test-profile')

    def test_stale_resource_row_does_not_write_or_launch(self):
        self.select()
        before = self.state.read_text()
        with patch.object(navigation, 'resource_rows', return_value=[('actual', 'vpc-123')]), patch.object(navigation, 'run') as run:
            with self.assertRaises(ValueError):
                navigation.pick('aws-vpc-subnets-1', 'vpc-456')
        self.assertEqual(before, self.state.read_text())
        run.assert_not_called()
    def test_every_generated_menu_reads_the_stored_provider_selection(self):
        import providers
        contexts = {
            'gcp': {'label': 'Saved Google', 'configuration': 'saved-config', 'account': 'saved@example.org', 'project': 'saved-project'},
            'azure': {'label': 'Saved Azure', 'subscription': '12345678-1234-1234-1234-123456789abc', 'tenant': 'abcdef12-1234-1234-1234-123456789abc'},
        }
        for name, menu in navigation.MENUS.items():
            provider = menu['provider']
            value = contexts.get(provider, 'saved-account')
            navigation.write_state({provider: {'selection': value, 'picks': {}}})
            with self.subTest(menu=name), patch.object(navigation, 'resource_rows', return_value=[('resource', 'resource-id')]) as resources, \
                    patch.object(providers, 'selection', return_value={'context': 'saved-context'}):
                rows = navigation.entries(name)
                expected = value['label'] if isinstance(value, dict) else value
                self.assertTrue(any(expected in row.get('Subtext', '') for row in rows))
                if menu.get('selector'):
                    self.assertEqual(resources.call_args.args[1]['selection'], value)

    def test_google_missing_project_routes_to_real_menu_before_any_cli(self):
        context = {'label': 'Saved Google', 'configuration': 'saved-config', 'account': 'saved@example.org', 'project': ''}
        navigation.write_state({'gcp': {'selection': context, 'picks': {}}})
        with patch.object(navigation.subprocess, 'run') as run, patch.object(navigation, 'show') as show:
            navigation.run('gcp-account', '\uf4b7  Compute Instances')
        run.assert_not_called()
        show.assert_called_once_with('gcp-projects')
        with patch.object(navigation, 'resource_rows', return_value=[('saved-project', 'saved-project')]), patch.object(navigation, 'show') as show:
            navigation.pick('gcp-projects', 'saved-project')
        show.assert_called_once_with('gcp-account')
        self.assertEqual(navigation.selected('gcp')['picks']['project'], 'saved-project')
        self.assertIn('saved-project', navigation.detail('gcp', navigation.selected('gcp')))

    def test_external_delete_uses_existing_walker_confirmation_and_returns_to_list(self):
        import providers
        navigation.write_state({'cloudflare': {'selection': 'saved-account', 'picks': {}}})
        with patch.object(providers, 'selection', return_value={}):
            rows = providers.account_entries('cloudflare', 'saved-account')
            command = next(row['Actions']['open'] for row in rows if row['Text'] == 'Delete Account')
            arguments = __import__('shlex').split(command)
            with patch.object(navigation.subprocess, 'run') as run, patch.object(providers, 'account_path', return_value=self.state.parent / 'deleted'), \
                    patch.object(navigation, 'show') as show:
                navigation.invoke('cloudflare-account', arguments)
        run.assert_called_once_with(arguments, check=True)
        self.assertNotIn('kitty', arguments)
        show.assert_called_once_with('cloudflare-contexts')

    def test_generated_menus_and_layouts_are_current(self):
        spec = importlib.util.spec_from_file_location('cloud_menu_build', ROOT / 'tools/cloud-menus-build.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        self.assertEqual(builder.build(check=True), [])

    def test_scoped_search_includes_descendant_actions_without_cloud_queries(self):
        self.select()
        with patch.object(navigation.subprocess, 'run') as run:
            rows = navigation.entries('aws-account', 'Instances')
        self.assertTrue(any(row['Text'] == 'Instances' for row in rows))
        self.assertTrue(any(row['Text'] == 'SSO Login' for row in rows))
        run.assert_not_called()

    def test_lua_menus_delegate_queries_to_generated_entries(self):
        for name, menu in navigation.MENUS.items():
            script = '''
local invoked = ''
io.popen = function(command)
    invoked = command
    return {read = function() return 'fixture' end, close = function() end}
end
jsonDecode = function(raw)
    assert(raw == 'fixture')
    return {{Text = 'Saved account', Subtext = 'Saved context', Actions = {open = 'mock'}}}
end
dofile(%s)
assert(Parent == %s)
local entries = GetEntries('needle')
assert(entries[1].Subtext == 'Saved context')
assert(invoked:find('navigation.py', 1, true))
assert(invoked:find(%s, 1, true))
assert(invoked:find('needle', 1, true))
''' % (json.dumps(str(ROOT / 'elephant/menus' / (name + '.lua'))), json.dumps(menu['parent']), json.dumps(name))
            result = subprocess.run(['lua', '-'], input=script, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, (name, result.stderr))

    def test_aws_resource_pipeline_runs_only_the_explicit_profile_with_a_mock_cli(self):
        self.select()
        directory = self.state.parent / 'bin'
        directory.mkdir()
        cli = directory / 'aws'
        log = self.state.parent / 'aws-arguments'
        cli.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$MOCK_ARGUMENTS"\nprintf \'%s\\n\' \'{"Vpcs":[{"VpcId":"vpc-123","Tags":[{"Key":"Name","Value":"Main"}]}]}\'\n')
        cli.chmod(0o755)
        with patch.dict(os.environ, HOME=str(self.state.parent), XDG_CONFIG_HOME=str(self.state.parent / 'config'),
                        PATH=str(directory) + os.pathsep + os.defpath, MOCK_ARGUMENTS=str(log)):
            rows = navigation.resource_rows(navigation.MENUS['aws-vpc-subnets-1'], navigation.selected('aws'))
        self.assertEqual(rows, [('Main  vpc-123', 'vpc-123')])
        self.assertEqual(log.read_text().splitlines(), ['--profile', 'test-profile', 'ec2', 'describe-vpcs'])

    def test_aws_action_retains_report_payload_with_a_mock_terminal(self):
        self.select()
        directory = self.state.parent / 'bin'
        directory.mkdir()
        terminal = directory / 'kitty'
        payload = self.state.parent / 'payload'
        temporary = self.state.parent / 'runtime'
        temporary.mkdir()
        terminal.write_text('#!/bin/bash\ncat "${@: -1}" > "$MOCK_PAYLOAD"\nrm -- "${@: -1}"\n')
        terminal.chmod(0o755)
        with patch.dict(os.environ, HOME=str(self.state.parent), XDG_CONFIG_HOME=str(self.state.parent / 'config'),
                        XDG_RUNTIME_DIR=str(temporary), PATH=str(directory) + os.pathsep + os.defpath, MOCK_PAYLOAD=str(payload)):
            navigation.run('aws-s3', '\U000f024b  List buckets')
        script = payload.read_text()
        self.assertIn('aws --profile test-profile', script)
        self.assertIn('s3 ls', script)
        self.assertIn('cloud_report', script)
        self.assertIn('navigation.py', script)
        self.assertIn('aws-s3', script)
        self.assertNotIn('walker-dmenu', script)
