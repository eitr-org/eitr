import importlib.util
import json
import os
from pathlib import Path
import subprocess
import shlex
import tomllib
import tempfile
import unittest
from unittest.mock import patch
from home_isolation import setUpModule, tearDownModule

ROOT = Path(__file__).resolve().parents[2]
CLOUD = ROOT / 'walker/scripts/menus/cloud'


class ExtraCloudProviderTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('extra_cloud', CLOUD / 'providers.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        patcher = patch.dict(os.environ, {'HOME': str(self.home), 'XDG_CONFIG_HOME': str(self.home / '.config')})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_exact_providers_and_menu_layouts(self):
        self.assertEqual(set(self.module.PROVIDERS),
                         {'cloudflare', 'digitalocean', 'oracle', 'hetzner', 'vercel', 'netlify', 'ibm'})
        rows = json.loads((ROOT / 'elephant/menu-rows/cloud.json').read_text())
        self.assertEqual(len(rows), 10)
        self.assertEqual([row['text'] for row in rows], sorted((row['text'] for row in rows), key=str.casefold))
        for provider in self.module.PROVIDERS:
            self.assertIn('Parent = "cloud"', (ROOT / f'elephant/menus/{provider}-contexts.lua').read_text())
            self.assertEqual((ROOT / f'walker/themes/current/item_menus-{provider}-contexts.xml').read_bytes(),
                             (ROOT / 'walker/themes/current/item_menus-main.xml').read_bytes())

    def test_listing_never_runs_cli_or_reads_existing_provider_configs(self):
        with patch.object(self.module.subprocess, 'run', side_effect=AssertionError('Unexpected subprocess')):
            for provider in self.module.PROVIDERS:
                self.assertEqual(len(self.module.entries(provider)), 1)
                directory = self.module.account_path(provider, 'production')
                directory.mkdir(parents=True)
                self.assertEqual(self.module.entries(provider)[0][0], 'production')

    def test_delete_actions_run_directly_and_close_walker(self):
        settings = tomllib.loads((ROOT / 'walker/config.toml').read_text())
        actions = settings['providers']['actions']
        for provider in self.module.PROVIDERS:
            directory = self.module.account_path(provider, 'review')
            directory.mkdir(parents=True)
            command = shlex.split(self.module.entries(provider)[0][3])
            self.assertEqual(command, ['python3', str(self.module.SCRIPT), provider, 'delete', 'review'])
            rows = actions['menus:' + provider + '-contexts']
            deletion = next(row for row in rows if row['action'] == 'cloud_delete')
            self.assertEqual(deletion['after'], 'Close')

    def test_invalid_and_symlink_accounts_are_rejected(self):
        for name in ('../owner', '/tmp/account', 'bad\tname', '-option', 'UPPER'):
            with self.assertRaises(ValueError):
                self.module.account_path('cloudflare', name)
        directory = self.module.account_root('cloudflare')
        directory.mkdir(parents=True)
        (directory / 'owner').symlink_to(self.home, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.module.account_path('cloudflare', 'owner')
        self.assertEqual(self.module.accounts('cloudflare'), [])

    def test_credentials_and_provider_overrides_are_not_inherited(self):
        with patch.dict(os.environ, {'AWS_PROFILE': 'owner', 'CLOUDFLARE_API_TOKEN': 'secret',
                                     'DOCTL_CONFIG': '/owner', 'BASH_ENV': '/owner/startup',
                                     'NETLIFY_AUTH_TOKEN': 'secret'}):
            values = self.module.environment(self.home)
        self.assertEqual(values['HOME'], str(self.home))
        self.assertEqual(values['XDG_CONFIG_HOME'], str(self.home / '.config'))
        for key in ('AWS_PROFILE', 'CLOUDFLARE_API_TOKEN', 'DOCTL_CONFIG', 'BASH_ENV', 'NETLIFY_AUTH_TOKEN'):
            self.assertNotIn(key, values)

    def test_login_runs_only_in_selected_private_workspace(self):
        directory = self.module.account_path('cloudflare', 'production')
        directory.mkdir(parents=True)
        with patch.object(self.module, 'ensure_cli', return_value=True), \
                patch.object(self.module.shutil, 'which', return_value='/usr/bin/wrangler'), \
                patch.object(self.module.subprocess, 'run') as run, patch('builtins.input', return_value=''):
            self.module.run_account('cloudflare', 'production', 'login')
        arguments, options = run.call_args
        self.assertEqual(arguments[0], ['/usr/bin/wrangler', 'login'])
        self.assertEqual(options['cwd'], directory)
        self.assertEqual(options['env']['HOME'], str(directory))

    def run_action(self, provider, action, answers=()):
        directory = self.module.account_path(provider, 'development')
        directory.mkdir(parents=True, exist_ok=True)
        with patch.object(self.module, 'ensure_cli', return_value=True), \
                patch.object(self.module, 'cli_path', return_value='/mock/bin/' + self.module.PROVIDERS[provider]['cli']), \
                patch.object(self.module, 'ask_value', side_effect=answers), \
                patch.object(self.module, 'collect_setup', return_value=dict(zip(('account', 'region'), answers))), \
                patch.object(self.module.subprocess, 'run') as run, patch('builtins.input', return_value=''):
            self.module.run_account(provider, 'development', action)
        for call in run.call_args_list:
            self.assertEqual(call.kwargs['cwd'], directory)
            self.assertEqual(call.kwargs['env']['HOME'], str(directory))
            self.assertTrue(call.kwargs['check'])
        return [call.args[0][1:] for call in run.call_args_list]

    def test_vendor_logins(self):
        cases = {
            'digitalocean': (['auth', 'init', '--context', 'development'], ()),
            'hetzner': (['context', 'create', 'development'], ()),
            'oracle': (['session', 'authenticate', '--profile-name', 'development', '--region', 'eu-frankfurt-1'], ('eu-frankfurt-1',)),
            'vercel': (['login'], ('my-team',)),
            'netlify': (['login'], ()),
            'ibm': (['login', '--sso'], ()),
        }
        for provider, (expected, answers) in cases.items():
            with self.subTest(provider=provider):
                self.assertEqual(self.run_action(provider, 'login', answers), [expected])
        self.assertEqual(self.run_action('ibm', 'apikey'), [['login', '--apikey']])

    def test_lists_and_explicit_native_switches(self):
        self.assertEqual(self.run_action('digitalocean', 'list'), [['auth', 'list']])
        self.assertEqual(self.run_action('hetzner', 'list'), [['context', 'list']])
        self.assertEqual(self.run_action('ibm', 'list'), [['target']])
        for provider in ('vercel', 'netlify'):
            self.assertEqual(self.run_action(provider, 'switch', ('selected-team',)), [['switch']])
            self.assertEqual(self.module.selection(provider, 'development')['context'], 'selected-team')
        self.assertEqual(self.run_action('ibm', 'switch', ('account-id', 'eu-de')),
                         [['target', '-c', 'account-id', '-r', 'eu-de']])
        self.assertEqual(self.module.selection('ibm', 'development')['region'], 'eu-de')

    def test_context_navigation_uses_per_command_flags(self):
        for provider, flags in (
                ('digitalocean', ['--context', 'production']),
                ('hetzner', ['--context', 'production']),
                ('oracle', ['--profile', 'production', '--auth', 'security_token'])):
            with self.subTest(provider=provider):
                self.assertEqual(self.run_action(provider, 'switch', ('production',)), [])
                self.assertEqual(self.run_action(provider, 'help'), [[*flags, '--help']])
                self.assertIn('production', self.module.entries(provider)[0][1])
        self.run_action('vercel', 'switch', ('selected-team',))
        self.assertEqual(self.run_action('vercel', 'help'), [['--scope', 'selected-team', '--help']])

    def test_oracle_lists_only_private_profiles(self):
        directory = self.module.account_path('oracle', 'development') / '.oci'
        directory.mkdir(parents=True)
        (directory / 'config').write_text('[DEFAULT]\nregion=eu-frankfurt-1\n[production]\nregion=us-ashburn-1\n')
        with patch('builtins.print') as output:
            self.assertEqual(self.run_action('oracle', 'list'), [])
        output.assert_any_call('DEFAULT\nproduction')

    def test_selection_validation_and_permissions(self):
        for value in ('--option', 'bad\nname', '../bad value', ''):
            with self.assertRaises(ValueError):
                self.module.validate_value(value)
        self.run_action('hetzner', 'switch', ('production',))
        directory = self.module.account_path('hetzner', 'development')
        self.assertEqual((directory / 'selection.json').stat().st_mode & 0o777, 0o600)
        (directory / 'selection.json').unlink()
        (directory / 'selection.json').symlink_to(self.home / 'owner-config')
        with self.assertRaises(ValueError):
            self.module.selection('hetzner', 'development')

    def test_failed_native_switch_preserves_saved_selection(self):
        self.run_action('ibm', 'switch', ('original', 'eu-de'))
        with patch.object(self.module, 'ensure_cli', return_value=True), \
                patch.object(self.module, 'cli_path', return_value='/mock/ibmcloud'), \
                patch.object(self.module, 'collect_setup', return_value={'account': 'replacement', 'region': 'us-south'}), \
                patch.object(self.module.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'ibmcloud')):
            with self.assertRaises(subprocess.CalledProcessError):
                self.module.run_account('ibm', 'development', 'switch')
        self.assertEqual(self.module.selection('ibm', 'development'), {'context': 'original', 'region': 'eu-de'})

    def test_generated_account_entries_refresh_saved_context(self):
        self.run_action('hetzner', 'switch', ('original',))
        rows = self.module.account_entries('hetzner', 'development')
        self.assertTrue(all('original' in row['Subtext'] for row in rows))
        self.run_action('hetzner', 'switch', ('replacement',))
        rows = self.module.account_entries('hetzner', 'development')
        self.assertTrue(all('replacement' in row['Subtext'] for row in rows))

    def test_account_entries_preserve_icons_descriptions_and_commands(self):
        for provider in self.module.PROVIDERS:
            self.module.account_path(provider, 'menu').mkdir(parents=True)
            rows = self.module.account_entries(provider, 'menu')
            labels = [row['Text'] for row in rows]
            self.assertEqual(labels, sorted(labels, key=str.casefold))
            for title, (label, description, arguments) in self.module.VIEWS[provider].items():
                row = next(row for row in rows if row['Text'] == label)
                self.assertEqual(row['Icon'], self.module.VIEW_ICONS[title])
                self.assertIn(description, row['Subtext'])
                self.assertEqual(shlex.split(row['Actions']['open']),
                                 shlex.split(self.module.terminal(provider, 'view', 'menu')) + [title])

    def test_elephant_consumes_account_and_add_icons(self):
        for provider in self.module.PROVIDERS:
            self.module.account_path(provider, 'fixture').mkdir(parents=True)
            rows = self.module.entries(provider)
            fixture = '\n'.join('\t'.join(row) for row in rows)
            script = """
local fixture = %s
io.popen = function(command)
    return {
        lines = function() return fixture:gmatch('[^\\n]+') end,
        close = function() end
    }
end
dofile(%s)
local entries = GetEntries()
assert(#entries == 2)
assert(entries[1].Text == 'fixture')
assert(entries[1].Icon == %s)
assert(entries[1].Actions.cloud_delete)
assert(entries[2].Icon == %s)
assert(not entries[2].Actions.cloud_delete)
""" % (json.dumps(fixture, ensure_ascii=False),
       json.dumps(str(ROOT / f'elephant/menus/{provider}-contexts.lua')),
       json.dumps(self.module.ACCOUNT_ICON, ensure_ascii=False),
       json.dumps(self.module.ADD_ICON, ensure_ascii=False))
            result = subprocess.run(['lua', '-'], input=script, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_delete_confirmation_cancellation_and_scope(self):
        for provider in self.module.PROVIDERS:
            directory = self.module.account_path(provider, 'delete-me')
            directory.mkdir(parents=True)
            (directory / 'token').write_text('fixture')
            sibling = self.module.account_path(provider, 'keep-me')
            sibling.mkdir()
            with patch.object(self.module, 'confirm') as confirmation:
                confirmation.return_value = False
                self.assertFalse(self.module.delete_account(provider, 'delete-me'))
                self.assertEqual((directory / 'token').read_text(), 'fixture')
                message = confirmation.call_args.args[0]
                self.assertIn(self.module.PROVIDERS[provider]['name'], message)
                self.assertIn('delete-me', message)
                confirmation.return_value = True
                self.assertTrue(self.module.delete_account(provider, 'delete-me'))
            self.assertFalse(directory.exists())
            self.assertTrue(sibling.is_dir())
        for provider in ('aws', 'azure', 'gcp', '../cloudflare'):
            with self.assertRaises(ValueError):
                self.module.delete_account(provider, 'keep-me')

    def test_delete_refuses_symlinks_and_active_actions(self):
        directory = self.module.account_path('cloudflare', 'active')
        directory.mkdir(parents=True)
        with self.module.account_lock(directory), patch.object(self.module, 'confirm') as confirmation:
            with self.assertRaises(ValueError):
                self.module.delete_account('cloudflare', 'active')
            confirmation.assert_not_called()
        with patch.object(self.module.Path, 'cwd', return_value=directory):
            with self.assertRaises(ValueError):
                self.module.delete_account('cloudflare', 'active')
        (directory / 'linked').symlink_to(self.home)
        with patch.object(self.module, 'confirm') as confirmation:
            confirmation.return_value = True
            with self.assertRaises(ValueError):
                self.module.delete_account('cloudflare', 'active')
        self.assertTrue(directory.exists())

    def test_all_reports_use_private_environment_and_explicit_flags(self):
        for provider, views in self.module.VIEWS.items():
            directory = self.module.account_path(provider, 'reports')
            directory.mkdir(parents=True)
            (directory / 'selection.json').write_text(json.dumps({'context': 'selected'}))
            if provider == 'oracle':
                (directory / '.oci').mkdir()
                (directory / '.oci/config').write_text('[selected]\ntenancy=ocid1.tenancy.oc1.fixture\n')
            for view, (_, _, arguments) in views.items():
                with self.subTest(provider=provider, view=view), \
                        patch.object(self.module, 'cli_path', return_value='/mock/cli'), \
                        patch.object(self.module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout='{"data":"namespace"}', stderr='')) as run:
                    self.module.report(provider, 'reports', view)
                calls = run.call_args_list
                for call in calls[:-1]:
                    self.assertEqual(call.kwargs['cwd'], directory)
                    self.assertEqual(call.kwargs['env']['HOME'], str(directory))
                    self.assertFalse(call.kwargs['check'])
                    flags = self.module.scoped_arguments(provider, 'selected')
                    if flags:
                        self.assertEqual(call.args[0][-len(flags):], flags)
                self.assertEqual(calls[-2].args[0][1:1 + len(arguments)], arguments)
                self.assertIn('cloud_report', calls[-1].args[0][2])
                self.assertTrue(calls[-1].kwargs['input'].endswith('{"data":"namespace"}'))
                self.assertIn('Context: ' + self.module.PROVIDERS[provider]['name'] + ' / reports / selected', calls[-1].kwargs['input'])

    def test_oracle_uses_selected_profile_tenancy_and_namespace(self):
        directory = self.module.account_path('oracle', 'scoped')
        (directory / '.oci').mkdir(parents=True)
        (directory / '.oci/config').write_text(
            '[DEFAULT]\ntenancy=ocid1.tenancy.oc1.wrong\n'
            '[selected]\ntenancy=ocid1.tenancy.oc1.selected\n')
        (directory / 'selection.json').write_text('{"context":"selected"}')
        with patch.object(self.module, 'cli_path', return_value='/mock/oci'), \
                patch.object(self.module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout='{"data":"private-ns"}', stderr='')) as run:
            self.module.report('oracle', 'scoped', 'Buckets')
        self.assertEqual(run.call_args_list[0].args[0],
                         ['/mock/oci', 'os', 'ns', 'get', '--profile', 'selected', '--auth', 'security_token'])
        self.assertEqual(run.call_args_list[1].args[0],
                         ['/mock/oci', 'os', 'bucket', 'list', '--compartment-id', 'ocid1.tenancy.oc1.selected',
                          '--namespace', 'private-ns', '--profile', 'selected', '--auth', 'security_token'])
        (directory / '.oci/config').unlink()
        (directory / '.oci/config').symlink_to(self.home / 'outside-profile')
        with patch.object(self.module, 'cli_path', return_value='/mock/oci'), \
                patch.object(self.module.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                self.module.report('oracle', 'scoped', 'Instances')
            run.assert_not_called()

    def test_vercel_without_selected_team_does_not_invent_scope(self):
        self.module.account_path('vercel', 'personal').mkdir(parents=True)
        with patch.object(self.module, 'cli_path', return_value='/mock/vercel'), \
                patch.object(self.module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout='report', stderr='')) as run:
            self.module.report('vercel', 'personal', 'Projects')
        self.assertEqual(run.call_args_list[0].args[0], ['/mock/vercel', 'project', 'ls'])

    def test_delete_refuses_folder_replaced_during_confirmation(self):
        directory = self.module.account_path('cloudflare', 'replace')
        directory.mkdir(parents=True)
        original = directory.with_name('original')

        def replace_folder(*arguments, **options):
            directory.rename(original)
            directory.mkdir()
            (directory / 'keep').write_text('replacement')
            return True

        with patch.object(self.module, 'confirm') as confirmation:
            confirmation.side_effect = replace_folder
            with self.assertRaises(ValueError):
                self.module.delete_account('cloudflare', 'replace')
        self.assertTrue(original.is_dir())
        self.assertEqual((directory / 'keep').read_text(), 'replacement')

    def test_report_failure_is_displayed_without_retry(self):
        for provider, view in (('cloudflare', 'Account'), ('oracle', 'Buckets')):
            directory = self.module.account_path(provider, 'failed')
            directory.mkdir(parents=True)
            if provider == 'oracle':
                (directory / '.oci').mkdir()
                (directory / '.oci/config').write_text('[failed]\ntenancy=ocid1.tenancy.oc1.fixture\n')
            with patch.object(self.module, 'cli_path', return_value='/mock/cli'), \
                    patch.object(self.module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, stdout='', stderr='Permission denied')) as run:
                self.module.report(provider, 'failed', view)
            self.assertEqual(run.call_count, 2)
            self.assertIn('Permission denied', run.call_args.kwargs['input'])
            self.assertIn('exit 1', run.call_args.kwargs['input'])

    def test_install_recipes_and_https_sources(self):
        installers = json.loads((ROOT / 'distro/installers.json').read_text())
        self.assertEqual(installers['oracle'], 'https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh')
        self.assertEqual(installers['ibm'], 'https://clis.cloud.ibm.com/install/linux')
        recipes = (ROOT / 'walker/scripts/actions/install/development.sh').read_text()
        self.assertIn('oracle) download_run "$(installer_url oracle)" --accept-all-defaults', recipes)
        self.assertIn('ibm) download_run "$(installer_url ibm)"', recipes)
        self.assertIn("--proto-redir '=https'", recipes)
        self.assertIn('yarn|pnpm|bun|vercel) node_setup; npm install --global "$kind"', recipes)
        self.assertIn('netlify) node_setup; npm install --global netlify-cli', recipes)
        catalog = json.loads((ROOT / 'distro/software.json').read_text())['cloud']
        for provider in ('oracle', 'ibm', 'vercel', 'netlify'):
            self.assertEqual(catalog[provider]['source'], 'managed')
        for provider, package in (('digitalocean', 'doctl'), ('hetzner', 'hcloud')):
            self.assertEqual(catalog[provider]['packages'], [package])
            self.assertEqual(catalog[provider]['source'], 'pacman')

    def test_missing_cli_uses_existing_recipe_after_confirmation(self):
        for provider in ('oracle', 'ibm', 'vercel', 'netlify'):
            with self.subTest(provider=provider), \
                    patch.object(self.module, 'cli_path', side_effect=[None, '/mock/cli']), \
                    patch.object(self.module, 'Terminal') as terminal, \
                    patch.object(self.module.subprocess, 'run') as run:
                terminal.return_value.confirm.return_value = True
                self.assertTrue(self.module.ensure_cli(provider))
                run.assert_called_once_with(['bash', str(ROOT / 'walker/scripts/actions/install/development.sh'), provider], check=True)
        with patch.object(self.module, 'cli_path', return_value=None), \
                patch.object(self.module, 'Terminal') as terminal, \
                patch.object(self.module.subprocess, 'run') as run:
            terminal.return_value.confirm.return_value = False
            self.assertFalse(self.module.ensure_cli('oracle'))
            run.assert_not_called()

    def test_report_pager_fallback_keeps_output_readable(self):
        script = f'''source {CLOUD / 'terminal-helpers.sh'}
command() {{ return 1; }}
cloud_wait_for_key() {{ printf '\\nWAITED\\n'; }}
printf 'first\\nsecond\\n' | cloud_report
'''
        result = subprocess.run(['bash', '-c', script], capture_output=True, text=True,
                                env={**os.environ, 'EITR_CODE_ROOT': str(ROOT),
                                     'EITR_LIBRARY_ROOT': str(ROOT / 'distro/lib')}, check=True)
        self.assertEqual(result.stdout, 'first\nsecond\n\nWAITED\n')

    def test_resource_reports_use_pager_and_logs_keep_search(self):
        for provider in ('aws', 'azure', 'gcp'):
            for path in (CLOUD / provider).glob('*.sh'):
                self.assertNotRegex(path.read_text(), r'\| cloud_fzf [^\n]+ plain')
        self.assertIn('cloud_fzf', (CLOUD / 'gcp/logs.sh').read_text())
        self.assertIn('cloud_report', (CLOUD / 'gcp/compute.sh').read_text())

    def test_add_cancellation_and_failed_signin_leave_no_workspace(self):
        for provider in self.module.PROVIDERS:
            for failure in (KeyboardInterrupt(), subprocess.CalledProcessError(1, 'mock-login')):
                with self.subTest(provider=provider, failure=type(failure)):
                    answers = {'name': 'cancelled', 'region': 'test-region', 'scope': 'test-scope'}
                    with patch.object(self.module, 'collect_setup', return_value=answers), \
                            patch.object(self.module, 'ensure_cli', return_value=True), \
                            patch.object(self.module, 'run_account', side_effect=failure), \
                            patch('sys.argv', ['providers.py', provider, 'add']):
                        with self.assertRaises(type(failure)):
                            self.module.main()
                    self.assertFalse(self.module.account_path(provider, 'cancelled').exists())
                    self.assertEqual(list(self.home.iterdir()), [])
            with patch.object(self.module, 'collect_setup', side_effect=KeyboardInterrupt), \
                    patch.object(self.module, 'ensure_cli') as install, \
                    patch('sys.argv', ['providers.py', provider, 'add']):
                with self.assertRaises(KeyboardInterrupt):
                    self.module.main()
                install.assert_not_called()
                self.assertEqual(list(self.home.iterdir()), [])
