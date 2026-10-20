import importlib.util
import json
import os
from pathlib import Path
import subprocess
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
                self.assertEqual(self.module.entries(provider)[1][0], 'production')

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
                self.assertIn('production', self.module.entries(provider)[1][1])
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
                patch.object(self.module, 'ask_value', side_effect=['replacement', 'us-south']), \
                patch.object(self.module.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'ibmcloud')):
            with self.assertRaises(subprocess.CalledProcessError):
                self.module.run_account('ibm', 'development', 'switch')
        self.assertEqual(self.module.selection('ibm', 'development'), {'context': 'original', 'region': 'eu-de'})

    def test_tool_picker_refreshes_selected_context_after_terminal_returns(self):
        self.run_action('hetzner', 'switch', ('original',))
        prompts = []

        def respond(arguments, **options):
            if '--prompt' in arguments:
                prompts.append(arguments[-1])
                return subprocess.CompletedProcess(arguments, 0 if len(prompts) == 1 else 1,
                                                    stdout='Switch Account' if len(prompts) == 1 else '')
            path = self.module.account_path('hetzner', 'development') / 'selection.json'
            path.write_text(json.dumps({'context': 'replacement'}))
            return subprocess.CompletedProcess(arguments, 0)

        with patch.object(self.module.subprocess, 'run', side_effect=respond):
            self.module.open_account('hetzner', 'development')
        self.assertEqual(prompts, ['Hetzner Cloud / development / original',
                                   'Hetzner Cloud / development / replacement'])

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
