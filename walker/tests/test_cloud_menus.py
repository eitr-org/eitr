from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CLOUD = ROOT / "walker/scripts/menus/cloud"


class CloudMenuTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name)
        bin_dir = self.home / ".config/walker/bin"
        bin_dir.mkdir(parents=True)
        # walker-dmenu prints MOCK_CHOICE, or nothing to simulate Escape.
        dmenu = bin_dir / "walker-dmenu"
        dmenu.write_text('#!/usr/bin/env bash\ncat >/dev/null\nprintf "%s" "${MOCK_CHOICE:-}"\n')
        dmenu.chmod(0o755)
        self.mocks = self.home / "mock-bin"
        self.mocks.mkdir()
        for name in ("notify-send", "kitty"):
            mock = self.mocks / name
            # kitty records the script it was asked to run.
            mock.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "${@: -1}" >> "$HOME/launched"\n')
            mock.chmod(0o755)
        self.runtime = self.home / "runtime"
        self.runtime.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def bash(self, provider, body, **env):
        script = f'source {CLOUD / provider / "common.sh"}\n{body}'
        environment = {"HOME": str(self.home), "XDG_RUNTIME_DIR": str(self.runtime),
                       "EITR_CODE_ROOT": str(self.home / '.config'),
                       "XDG_CONFIG_HOME": str(self.home / ".config"),
                       "PATH": f"{self.mocks}:/usr/bin:/bin", **env}
        return subprocess.run(["bash", "-c", script], capture_output=True, text=True, env=environment)

    def test_cancelled_time_range_stops_instead_of_using_default(self):
        result = self.bash("aws", 'minutes="$(choose_time_range_minutes)" || { echo cancelled; exit 0; }; echo "ran $minutes"')
        self.assertEqual(result.stdout.strip(), "cancelled")

    def test_time_range_choice_and_invalid_fallback(self):
        result = self.bash("gcp", "choose_time_range_minutes", MOCK_CHOICE="60")
        self.assertEqual(result.stdout.strip(), "60")
        result = self.bash("gcp", "choose_time_range_minutes", MOCK_CHOICE="soon")
        self.assertEqual(result.stdout.strip(), "30")

    def test_missing_cli_stops_project_choice(self):
        result = self.bash("gcp", 'project="$(choose_gcp_project)" || { echo stopped; exit 0; }; echo "ran $project"')
        self.assertEqual(result.stdout.strip(), "stopped")
        result = self.bash("azure", 'sub="$(choose_azure_subscription)" || { echo stopped; exit 0; }; echo "ran $sub"')
        self.assertEqual(result.stdout.strip(), "stopped")

    def test_aws_profiles_come_from_local_config(self):
        config = self.home / ".config/eitr/cloud.env"
        config.parent.mkdir(parents=True)
        config.write_text('EITR_AWS_PROFILES="Development=team-dev Production=team-prod Storage=storage Orphan=eitr-r2"\n')
        aws_config = self.home / ".aws/config"
        aws_config.parent.mkdir(parents=True)
        aws_config.write_text('[profile team-dev]\nregion = us-east-1\n[profile team-prod]\nregion = us-east-1\n'
                              '[profile storage]\nendpoint_url = https://storage.example\n')
        result = self.bash("aws", "aws_profile_choices", AWS_CONFIG_FILE=str(aws_config))
        self.assertEqual(result.stdout.splitlines(), ["Development\tteam-dev", "Production\tteam-prod"])

    def test_selected_context_skips_repeat_pickers_and_reaches_terminal(self):
        result = self.bash("gcp", 'choose_gcp_project; run_in_kitty Title true close-on-success toggle true',
                           EITR_CLOUD_CONTEXT="Production", CLOUDSDK_ACTIVE_CONFIG_NAME="prod",
                           CLOUDSDK_CORE_ACCOUNT="dev@example.org", CLOUDSDK_CORE_PROJECT="prod-project")
        self.assertEqual(result.stdout.strip(), "prod-project")
        script = Path((self.home / "launched").read_text().strip()).read_text()
        self.assertIn("export CLOUDSDK_ACTIVE_CONFIG_NAME=prod", script)
        self.bash("gcp", 'run_in_kitty Title true close-on-success toggle true',
                  EITR_CLOUD_CONTEXT="Detected", CLOUDSDK_ACTIVE_CONFIG_NAME="detected", CLOUDSDK_CORE_ACCOUNT="a@example.org")
        script = Path((self.home / "launched").read_text().splitlines()[-1]).read_text()
        self.assertNotIn("CLOUDSDK_CORE_PROJECT", script)

    def test_google_login_targets_the_detected_account_without_activation(self):
        result = self.bash("gcp", f'source {CLOUD / "context-auth.sh"}; gcloud() {{ printf "%s\\n" "$@"; }}; cloud_context_login',
                           EITR_CLOUD_PROVIDER="gcp", CLOUDSDK_ACTIVE_CONFIG_NAME="detected",
                           CLOUDSDK_CORE_ACCOUNT="person@example.org")
        self.assertEqual(result.stdout.splitlines(), ["auth", "login", "person@example.org", "--no-activate"])

    def test_azure_login_targets_tenant_and_restores_default(self):
        body = f'''source {CLOUD / "context-auth.sh"}
az() {{
  if [[ "$*" == "account show --query id -o tsv" ]]; then echo previous; return; fi
  printf '%s\\n' "$*"
}}
cloud_context_login'''
        result = self.bash("azure", body, EITR_CLOUD_PROVIDER="azure",
                           EITR_AZURE_TENANT="detected-tenant", EITR_AZURE_SUBSCRIPTION="selected")
        self.assertEqual(result.stdout.splitlines(), ["login --tenant detected-tenant",
                         "account set --subscription previous", "account show --subscription selected -o json"])

    def test_generated_terminal_script_is_private_and_self_deleting(self):
        result = self.bash("aws", 'AWS_PROFILE=dev; run_in_kitty Title "cloud_kv Profile \\"$AWS_PROFILE\\"" close-on-success toggle true')
        self.assertEqual(result.returncode, 0, result.stderr)
        launched = Path((self.home / "launched").read_text().strip())
        self.assertEqual(launched.parent, self.runtime)
        self.assertEqual(launched.stat().st_mode & 0o777, 0o700)
        source = launched.read_text()
        self.assertIn("export AWS_PROFILE=dev", source)
        self.assertNotIn("AWS_REGION", source)
        self.assertIn("terminal-helpers.sh", source)
        run = subprocess.run(["bash", str(launched)], capture_output=True, text=True,
                             env={"HOME": str(self.home), "PATH": f"{self.mocks}:/usr/bin:/bin", "TERM": "dumb"})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Profile:", run.stdout)
        self.assertFalse(launched.exists())

    def test_choose_helpers_never_exit_inside_command_substitution(self):
        for script in sorted(CLOUD.glob("**/*.sh")):
            body = script.read_text()
            for function in re.findall(r"^choose_\w+\(\) \{\n(.*?)^\}", body, re.M | re.S):
                with self.subTest(script=script.relative_to(CLOUD)):
                    self.assertNotRegex(function, r"\bexit [0-9]")
            for line in body.splitlines():
                if re.match(r'^\s*\w+="\$\(choose_\w+', line):
                    with self.subTest(script=script.relative_to(CLOUD), line=line.strip()):
                        self.assertRegex(line, r"\|\|")

    def test_no_work_specific_defaults(self):
        tracked = [*CLOUD.glob("**/*.sh"), *(ROOT / "elephant/menus").glob("*")]
        for path in tracked:
            with self.subTest(path=path.relative_to(ROOT)):
                # No hard-coded cloud region or 12-digit account number.
                self.assertNotRegex(path.read_text(), r"\b(?:us|eu|ap|sa|ca|me|af)-(?:east|west|north|south|central|northeast|southeast)-\d\b|\b\d{12}\b")


if __name__ == "__main__":
    unittest.main()
