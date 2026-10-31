import importlib.util
from pathlib import Path
import unittest
from unittest import mock
import tempfile
import json
import subprocess
import io
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ai_usage", ROOT / "scripts/ai-usage.py")
USAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(USAGE)


class ClaudeLimitsTests(unittest.TestCase):
    def test_fable_scoped_weekly_limit_and_legacy_deduplication(self):
        result = USAGE.claude_windows({
            "five_hour": {"utilization": 20, "resets_at": None},
            "seven_day": {"utilization": 30},
            "limits": [
                {"kind": "session", "percent": 20},
                {"kind": "weekly_all", "percent": 30},
                {"kind": "weekly_scoped", "percent": 10, "is_active": False,
                 "scope": {"model": {"display_name": "Fable"}},
                 "resets_at": "2026-10-14T12:00:00Z"},
            ],
        })
        self.assertEqual([row["label"] for row in result], ["5h window", "Weekly", "Fable weekly"])
        self.assertEqual(result[-1]["used"], 10)
        self.assertIsInstance(result[-1]["reset"], float)

    def test_missing_and_future_limits_do_not_invent_usage(self):
        self.assertEqual(USAGE.claude_windows({"limits": [{"kind": "unknown", "percent": 9},
                                                      {"kind": "weekly_scoped", "percent": None}]}), [])

    def test_the_panel_shows_only_limits(self):
        qml = (ROOT / "panels/AiUsageMenu.qml").read_text()
        for removed in ("TOKEN", "ai-local-stats", "detailsExpanded"):
            self.assertNotIn(removed, qml)
        self.assertFalse((ROOT / "scripts/ai-local-stats.py").exists())


class ProviderDetectionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.home = Path(self.directory.name)
        self.home_patch = mock.patch.object(USAGE.Path, "home", return_value=self.home)
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)
        self.env_patch = mock.patch.dict(USAGE.os.environ, {}, clear=True)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def credentials(self, path, data):
        target = self.home / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data))

    def detect(self, installed):
        with mock.patch.object(USAGE, "cli_binary", side_effect=lambda name: "/mock/bin/" + name if name in installed else None), \
             mock.patch.object(USAGE.subprocess, "run", return_value=mock.Mock(returncode=1)):
            return USAGE.available_providers()

    def test_installed_but_unsigned_clients_are_hidden(self):
        self.assertEqual(self.detect(["claude", "codex", "grok"]), [])

    def test_only_claude_then_only_codex(self):
        self.credentials(".claude/.credentials.json", {"claudeAiOauth": {"accessToken": "test-only"}})
        self.assertEqual(self.detect(["claude", "codex"]), ["Claude"])
        self.credentials(".codex/auth.json", {"tokens": {"access_token": "test-only"}})
        self.assertEqual(self.detect(["codex"]), ["Codex"])
        self.assertEqual(self.detect(["claude", "codex"]), ["Claude", "Codex"])

    def test_grok_is_optional_and_discovered_without_installing_it(self):
        self.credentials(".grok/auth.json", {"https://auth.x.ai::test": {"key": "test-only"}})
        self.assertEqual(self.detect([]), [])
        self.assertEqual(self.detect(["grok"]), ["Grok"])

    def test_provider_is_removed_after_signout(self):
        self.credentials(".claude/.credentials.json", {"claudeAiOauth": {"accessToken": "test-only"}})
        self.assertEqual(self.detect(["claude"]), ["Claude"])
        (self.home / ".claude/.credentials.json").unlink()
        self.assertEqual(self.detect(["claude"]), [])

    def test_codex_keyring_login_and_bounded_status_failure(self):
        with mock.patch.object(USAGE, "cli_binary", side_effect=lambda name: "/mock/codex" if name == "codex" else None), \
             mock.patch.object(USAGE.subprocess, "run", return_value=mock.Mock(returncode=0)):
            self.assertEqual(USAGE.available_providers(), ["Codex"])
        with mock.patch.object(USAGE, "cli_binary", side_effect=lambda name: "/mock/codex" if name == "codex" else None), \
             mock.patch.object(USAGE.subprocess, "run", side_effect=subprocess.TimeoutExpired("status", 3)):
            self.assertEqual(USAGE.available_providers(), [])

    def test_outage_hides_provider_without_leaking_errors(self):
        with mock.patch.object(USAGE, "usage_accounts", return_value=[("grok", {"id": "default", "label": "Default"})]), \
             mock.patch.object(USAGE, "grok_usage", side_effect=ValueError("secret-token")):
            data = USAGE.collect()
        self.assertEqual(data["providers"], [])
        self.assertNotIn("secret-token", json.dumps(data))

    def test_empty_and_unsupported_accounts_are_hidden(self):
        accounts = [("claude", {"id": "empty", "label": "Empty"}),
                    ("claude", {"id": "readable", "label": "Readable"}),
                    ("gemini", {"id": "default", "label": "Default"})]
        with mock.patch.object(USAGE, "usage_accounts", return_value=accounts), \
             mock.patch.object(USAGE, "account_environment", side_effect=lambda identifier, account: account), \
             mock.patch.object(USAGE, "claude_usage", side_effect=lambda account: {
                 "windows": [{"used": 0}] if account == "readable" else []}):
            self.assertEqual(USAGE.collect()["providers"], [{"name": "Claude", "accounts": [
                {"id": "readable", "label": "Readable", "windows": [{"used": 0}]}]}])

    def test_grok_quota_parser(self):
        rows = USAGE.grok_windows({"config": {"creditUsagePercent": 12.5,
            "currentPeriod": {"type": "USAGE_PERIOD_TYPE_WEEKLY", "end": "2026-10-14T12:00:00Z"}}})
        self.assertEqual(rows[0]["label"], "Weekly")
        self.assertEqual(rows[0]["used"], 12.5)
        self.assertIsInstance(rows[0]["reset"], float)
        self.assertEqual(USAGE.grok_windows({}), [])
        self.assertEqual(USAGE.grok_windows({"config": {"monthlyLimit": {"val": 200}, "used": {"val": 50}}})[0]["used"], 25)

    def test_enterprise_grok_credentials_are_never_sent_to_consumer_service(self):
        self.credentials(".grok/auth.json", {"enterprise": {"key": "test-only", "oidc_issuer": "https://enterprise.example"}})
        with mock.patch.object(USAGE.urllib.request, "urlopen") as request:
            with self.assertRaises(RuntimeError):
                USAGE.grok_usage()
            request.assert_not_called()

    def test_personal_grok_billing_request_is_read_only_and_mocked(self):
        self.credentials(".grok/auth.json", {"personal": {"key": "test-only",
            "oidc_issuer": "https://auth.x.ai", "user_id": "mock-user"}})
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "config": {"creditUsagePercent": 15, "currentPeriod": {"type": "WEEKLY"}}
        }).encode()
        with mock.patch.object(USAGE.urllib.request, "build_opener") as opener:
            opener.return_value.open.return_value = response
            data = USAGE.grok_usage()
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, "https://cli-chat-proxy.grok.com/v1/billing?format=credits")
        self.assertEqual(data["windows"][0]["used"], 15)

    def test_all_detected_providers_have_foldable_sections(self):
        qml = (ROOT / "panels/AiUsageMenu.qml").read_text()
        self.assertIn("model: menu.shownProviders", qml)
        self.assertIn("model: section.folded ? [] : (section.modelData.accounts || [])", qml)
        self.assertIn("onClicked: menu.toggleProvider(section.modelData.name)", qml)
        self.assertNotIn("id: tabs", qml)
        self.assertIn('text: Eitr.I18n.tr("AI Usage")', qml)


class CachedUsageTests(unittest.TestCase):
    def test_cache_hides_errors_empty_and_removed_accounts(self):
        with tempfile.TemporaryDirectory() as home:
            cache = Path(home) / '.cache/desktop-ai-usage.json'
            cache.parent.mkdir()
            cache.write_text(json.dumps({"providers": [
                {"name": "Claude", "accounts": [
                    {"id": "good", "label": "Old label", "windows": [{"used": 0}]},
                    {"id": "offline", "error": "No data", "windows": [{"used": 5}]},
                    {"id": "empty", "windows": []},
                    {"id": "removed", "windows": [{"used": 20}]}]},
                {"name": "Codex", "accounts": [{"id": "empty", "windows": []}]}]}))
            accounts = [("claude", {"id": identifier, "label": "Current label"})
                        for identifier in ("good", "offline", "empty", "new")]
            accounts.append(("codex", {"id": "empty", "label": "Default"}))
            backend = mock.Mock()
            backend.usage_accounts.return_value = accounts
            specification = importlib.util.spec_from_file_location('ai_domain', ROOT / 'scripts/ai-domain.py')
            module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(module)
            adapter = module.AiDomain.__new__(module.AiDomain)
            adapter.backend = backend
            backend.LABELS = USAGE.LABELS
            adapter.cache = cache
            output = io.StringIO()
            with redirect_stdout(output):
                print(json.dumps(adapter.cached()))
            self.assertEqual(json.loads(output.getvalue())["providers"], [
                {"name": "Claude", "accounts": [
                    {"id": "good", "label": "Current label", "windows": [{"used": 0}]}]}])


class LauncherTests(unittest.TestCase):
    def test_first_use_launchers_do_not_count_as_installed_tools(self):
        launchers = ROOT.parents[1] / "walker/assistants"
        with tempfile.TemporaryDirectory() as home, \
                mock.patch.dict("os.environ", {"PATH": str(launchers)}), \
                mock.patch.object(Path, "home", return_value=Path(home)):
            for name in ("claude", "codex", "grok"):
                self.assertIsNone(USAGE.cli_binary(name), name)
            real = Path(home) / ".local/bin/claude"
            real.parent.mkdir(parents=True)
            real.write_text("#!/bin/sh\n")
            real.chmod(0o755)
            self.assertEqual(USAGE.cli_binary("claude"), str(real))


class RateLimitTests(unittest.TestCase):
    def test_account_cooldown_and_errors_never_expose_payloads(self):
        account = dict(id='fixture', label='Private label')
        error = USAGE.UsageRateLimit('private provider payload', {'Retry-After': '1000'})
        with mock.patch.object(USAGE, 'COOLDOWNS', {}), \
                mock.patch.object(USAGE, 'account_environment', return_value={}), \
                mock.patch.object(USAGE, 'claude_usage', side_effect=error) as reader:
            self.assertIsNone(USAGE.collect_account('claude', account))
            self.assertIsNone(USAGE.collect_account('claude', account))
            reader.assert_called_once()
            self.assertGreater(USAGE.COOLDOWNS[('claude', 'fixture')], USAGE.time.monotonic() + 900)
