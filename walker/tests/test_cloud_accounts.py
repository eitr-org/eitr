import importlib.util
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from home_isolation import setUpModule, tearDownModule
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/menus/cloud/accounts.py"


def load():
    spec = importlib.util.spec_from_file_location("cloud_accounts", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Completed:
    def __init__(self, stdout=""):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = 0


class CloudAccountTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.config = Path(directory.name)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.config),
            "AWS_CONFIG_FILE": str(self.config / '.aws/config'),
            "AWS_SHARED_CREDENTIALS_FILE": str(self.config / '.aws/credentials'),
            "CLOUDSDK_CONFIG": str(self.config / 'gcloud'),
            "AZURE_CONFIG_DIR": str(self.config / '.azure')})
        patcher.start()
        self.addCleanup(patcher.stop)
        home_patch = patch('pathlib.Path.home', return_value=self.config)
        home_patch.start()
        self.addCleanup(home_patch.stop)
        self.accounts = load()

    def answer(self, *values):
        answers = iter(values)
        return patch("builtins.input", side_effect=lambda prompt="": next(answers))

    def test_staged_signin_rolls_back_on_failure_or_interrupt(self):
        for provider, variable, filename in (
                ('aws', 'AWS_CONFIG_FILE', None),
                ('gcp', 'CLOUDSDK_CONFIG', 'configurations/config_new'),
                ('azure', 'AZURE_CONFIG_DIR', 'azureProfile.json')):
            for failure in (KeyboardInterrupt, RuntimeError):
                with self.subTest(provider=provider, failure=failure):
                    before = dict(os.environ)
                    with self.assertRaises(failure):
                        with self.accounts.staged_provider(provider):
                            staged = Path(os.environ[variable])
                            staged = staged / filename if filename else staged
                            staged.parent.mkdir(parents=True, exist_ok=True)
                            staged.write_text('new sign-in')
                            raise failure()
                    self.assertEqual(dict(os.environ), before)
                    self.assertFalse(Path(before[variable]).exists())

    def test_staged_signin_publishes_only_after_success(self):
        target = Path(os.environ['CLOUDSDK_CONFIG'])
        target.mkdir()
        (target / 'existing').write_text('keep')
        with self.accounts.staged_provider('gcp'):
            staged = Path(os.environ['CLOUDSDK_CONFIG'])
            (staged / 'new').write_text('signed in')
            self.assertFalse((target / 'new').exists())
        self.assertEqual((target / 'existing').read_text(), 'keep')
        self.assertEqual((target / 'new').read_text(), 'signed in')
        self.assertEqual((target / 'new').stat().st_mode & 0o777, 0o600)

    def test_names_are_stored_per_provider_without_losing_others(self):
        self.accounts.set_name("aws", "acme-production", "Acme Production")
        self.accounts.set_name("gcp", "acme-dev", "Acme Development")
        saved = json.loads((self.config / "eitr/cloud-contexts.json").read_text())
        self.assertEqual(saved["aws"], {"acme-production": "Acme Production"})
        self.assertEqual(saved["gcp"], {"acme-dev": "Acme Development"})

    def test_aws_profiles_come_from_the_cli_files_without_starting_the_cli(self):
        config, credentials = self.config / "aws-config", self.config / "aws-credentials"
        config.write_text("[default]\nregion = us-east-1\n[profile acme-dev]\nsso_session = acme\n"
                          "[sso-session acme]\nsso_region = us-east-1\n[services local]\n")
        credentials.write_text("[default]\naws_access_key_id = x\n[legacy]\naws_access_key_id = y\n")
        with patch.dict(os.environ, {"AWS_CONFIG_FILE": str(config), "AWS_SHARED_CREDENTIALS_FILE": str(credentials)}), \
                patch.object(self.accounts.subprocess, "run") as run:
            self.assertEqual(self.accounts.aws_profiles(), ["default", "acme-dev"])
        run.assert_not_called()

    def test_aws_accounts_exclude_credentials_only_and_custom_endpoints(self):
        config = Path(os.environ['AWS_CONFIG_FILE'])
        credentials = Path(os.environ['AWS_SHARED_CREDENTIALS_FILE'])
        config.parent.mkdir(parents=True)
        config.write_text('[default]\nendpoint_url = https://storage.example\n'
                          '[profile aws-work]\nregion = eu-west-1\n'
                          '[profile r2]\nendpoint_url = https://r2.example\n'
                          '[profile empty-endpoint]\nendpoint_url =\n'
                          '[profile nested]\ns3 =\n  endpoint_url = https://storage.example\n'
                          '[profile linked]\nservices = storage\n'
                          '[services storage]\ns3 =\n  endpoint_url = https://storage.example\n'
                          '[sso-session company]\nsso_region = eu-west-1\n')
        credentials.write_text('[eitr-r2]\naws_access_key_id = fixture\n'
                               '[aws-work]\naws_access_key_id = fixture\n')
        before = (config.read_bytes(), credentials.read_bytes())
        with patch.object(self.accounts.subprocess, 'run') as run:
            self.assertEqual(self.accounts.aws_profiles(), ['aws-work'])
            with patch.dict(os.environ, EITR_AWS_PROFILES='Storage=eitr-r2 R2=r2 Work=aws-work'):
                self.assertEqual(self.accounts.aws_choices(), ['Work\taws-work'])
        run.assert_not_called()
        self.assertEqual((config.read_bytes(), credentials.read_bytes()), before)

    def test_aws_menu_lists_named_and_unnamed_profiles(self):
        self.accounts.set_name("aws", "acme-production", "Acme Production")
        with patch.object(self.accounts, "aws_profiles", return_value=["acme-production", "sandbox"]):
            self.assertEqual(self.accounts.aws_choices(),
                             ["Acme Production\tacme-production", "sandbox\tsandbox"])

    def test_add_aws_creates_a_named_sso_profile(self):
        profiles = [["default"], ["default", "acme-development"]]
        with patch.object(self.accounts, "collect_setup", return_value={"label": "Acme Development", "profile": "acme-development", "method": 0}), \
                patch.object(self.accounts, "aws_profiles", side_effect=lambda: profiles.pop(0)), \
                patch.object(self.accounts.subprocess, "run") as run:
            self.accounts.add_aws()
        run.assert_called_once_with(["aws", "configure", "sso", "--profile", "acme-development"], check=True)
        self.assertEqual(self.accounts.names("aws"), {"acme-development": "Acme Development"})

    def test_add_aws_with_access_keys_and_a_custom_profile_id(self):
        profiles = [[], ["prod"]]
        with patch.object(self.accounts, "collect_setup", return_value={"label": "Acme Production", "profile": "prod", "method": 1}), \
                patch.object(self.accounts, "aws_profiles", side_effect=lambda: profiles.pop(0)), \
                patch.object(self.accounts.subprocess, "run") as run:
            self.accounts.add_aws()
        run.assert_called_once_with(["aws", "configure", "--profile", "prod"], check=True)

    def test_add_aws_refuses_an_existing_profile_and_bad_ids(self):
        with patch.object(self.accounts, "collect_setup", return_value={"label": "Prod", "profile": "prod", "method": 0}), patch.object(self.accounts, "aws_profiles", return_value=["prod"]), \
                self.assertRaises(ValueError):
            self.accounts.add_aws()
        for value in ("Bad ID", "-x", "a/b", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.accounts.identifier(value)

    def test_add_gcp_uses_its_own_configuration_without_activating_it(self):
        calls = []

        def run(command, **options):
            calls.append((command, options.get("env", {}).get("CLOUDSDK_ACTIVE_CONFIG_NAME")))
            if command[:4] == ["gcloud", "config", "configurations", "list"]:
                return Completed("default\n")
            if command[1:3] == ["projects", "list"]:
                return Completed(json.dumps([{"projectId": "acme-dev-123", "name": "Dev"}]))
            return Completed()

        with patch.object(self.accounts, "collect_setup", return_value={"label": "Acme Development", "configuration": "acme-development", "project": "acme-dev-123"}), patch.object(self.accounts.subprocess, "run", side_effect=run):
            self.accounts.add_gcp()
        commands = [command for command, _ in calls]
        self.assertIn(["gcloud", "config", "configurations", "create", "acme-development", "--no-activate"], commands)
        self.assertIn((["gcloud", "auth", "login"], "acme-development"), calls)
        self.assertIn((["gcloud", "config", "set", "project", "acme-dev-123"], "acme-development"), calls)
        self.assertNotIn("activate", [command[3] for command in commands if command[1:3] == ["config", "configurations"]])
        self.assertEqual(self.accounts.names("gcp"), {"acme-development": "Acme Development"})

    def test_add_azure_restores_the_default_subscription_and_names_each(self):
        previous, new = "1" * 8 + "-1111-1111-1111-" + "1" * 12, "2" * 8 + "-2222-2222-2222-" + "2" * 12
        commands = []

        def run(command, **options):
            commands.append(command)
            if command[:3] == ["az", "account", "show"]:
                return Completed(json.dumps({"id": previous}))
            if command[:3] == ["az", "account", "list"]:
                return Completed(json.dumps([{"id": new, "name": "Pay-As-You-Go", "state": "Enabled"},
                                             {"id": previous, "name": "Old", "state": "Disabled"}]))
            return Completed()

        with patch.object(self.accounts, "collect_setup", return_value={"tenant": "", "label": "Acme Azure"}), patch.object(self.accounts.subprocess, "run", side_effect=run):
            self.accounts.add_azure()
        self.assertIn(["az", "account", "set", "--subscription", previous], commands)
        self.assertEqual(self.accounts.names("azure"), {new: "Acme Azure"})

    def test_missing_cli_is_installed_only_after_confirmation(self):
        with patch.object(self.accounts.shutil, "which", return_value=None), self.answer("n"):
            self.assertFalse(self.accounts.ensure_cli("gcp"))

    def test_aws_cli_version_one_is_replaced_before_sso(self):
        version = Completed("aws-cli/1.46.1 Python/3.14.8 Linux/7.2.9 botocore/1.43.62\n")
        with patch.object(self.accounts.shutil, "which", return_value="/usr/bin/aws"), \
                patch.object(self.accounts.subprocess, "run", return_value=version), self.answer("n"):
            self.assertFalse(self.accounts.ensure_cli("aws"))
        version = Completed("aws-cli/2.37.9 Python/3.13 Linux/7.2.9\n")
        with patch.object(self.accounts.shutil, "which", return_value="/usr/bin/aws"), \
                patch.object(self.accounts.subprocess, "run", return_value=version):
            self.assertTrue(self.accounts.ensure_cli("aws"))
        self.assertIn("aws-cli-v2", (ROOT / "distro/packages.txt").read_text().split())

    def test_rename_keeps_unknown_aws_profiles_out(self):
        with patch.object(self.accounts, "aws_profiles", return_value=["prod"]):
            with self.answer("Acme Production"):
                self.accounts.rename("aws", "prod")
            with self.assertRaises(ValueError):
                self.accounts.rename("aws", "missing")
        self.assertEqual(self.accounts.names("aws"), {"prod": "Acme Production"})

    def test_menus_offer_add_and_rename(self):
        aws = (ROOT / "elephant/aws-profile-entries.lua").read_text()
        self.assertIn('"Add AWS Account"', aws)
        self.assertIn("cloud_rename = manage and", aws)
        self.assertIn(", true)", (ROOT / "elephant/menus/aws-profiles.lua").read_text())
        contexts = (ROOT / "elephant/cloud-context-entries.lua").read_text()
        self.assertIn('i18n.tr("Add {provider} Account", {provider = names[provider]})', contexts)
        self.assertIn("cloud_rename", contexts)
        actions = tomllib.loads((ROOT / "walker/config.toml").read_text())["providers"]["actions"]
        for menu in ("aws-profiles", "gcp-contexts", "azure-contexts"):
            binds = {action["action"]: action["bind"] for action in actions["menus:" + menu]}
            self.assertEqual(binds["cloud_rename"], "ctrl r")
            self.assertEqual(binds["menus:parent"], "shift BackSpace")
        common = (ROOT / "walker/scripts/menus/cloud/aws/common.sh").read_text()
        self.assertIn('accounts.py" aws-choices', common)


if __name__ == "__main__":
    unittest.main()


class CredentialsOnlyProfileTests(unittest.TestCase):
    def test_aws_keys_are_listed_and_other_providers_are_not(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config"
            credentials = Path(directory) / "credentials"
            config.write_text("[profile work]\nregion = us-east-1\n[profile r2-config]\nendpoint_url = https://example.r2.cloudflarestorage.com\n")
            credentials.write_text("[keys-only]\naws_access_key_id = AKIAABCDEFGHIJKLMNOP\naws_secret_access_key = secret\n"
                                   "[eitr-r2]\naws_access_key_id = 0123456789abcdef0123456789abcdef\naws_secret_access_key = secret\n")
            with patch.dict(os.environ, {"AWS_CONFIG_FILE": str(config), "AWS_SHARED_CREDENTIALS_FILE": str(credentials)}):
                profiles = load().aws_profiles()
        self.assertIn("work", profiles)
        self.assertIn("keys-only", profiles)
        self.assertNotIn("eitr-r2", profiles)
        self.assertNotIn("r2-config", profiles)
