import importlib.util
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("monitoring", ROOT / "walker/scripts/actions/development/monitoring.py")
monitoring = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitoring)


class MonitoringTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = Path(directory.name) / "eitr/monitoring.json"
        for target, value in ((monitoring, "STORE"), (monitoring, "code")):
            replacement = self.store if value == "STORE" else (lambda relative: ROOT / relative)
            patcher = patch.object(target, value, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_dashboards_are_saved_listed_opened_and_removed(self):
        monitoring.add("grafana", "Production", "ops.grafana.net")
        monitoring.add("sentry", "Errors", "https://example.sentry.io/issues/")
        rows = monitoring.dashboards()
        self.assertEqual([row["name"] for row in rows], ["Errors", "Production"])
        self.assertEqual(rows[1]["url"], "https://ops.grafana.net")
        self.assertEqual(rows[1]["label"], "Grafana")
        with patch.object(monitoring.subprocess, "Popen") as start:
            monitoring.open_dashboard("grafana-production")
        self.assertEqual(start.call_args.args[0], ["xdg-open", "https://ops.grafana.net"])
        monitoring.remove("grafana-production")
        self.assertEqual([row["name"] for row in monitoring.dashboards()], ["Errors"])

    def test_unsafe_or_duplicate_dashboards_are_refused(self):
        for service, name, url, message in (
                ("grafana", "Prod", "https://user:secret@ops.grafana.net", "credentials"),
                ("grafana", "Prod", "javascript:alert(1)", "http or https"),
                ("splunk", "Prod", "splunk.example.com", "Unknown monitoring service")):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, message):
                monitoring.add(service, name, url)
        monitoring.add("datadog", "Prod", "app.datadoghq.eu")
        with self.assertRaisesRegex(ValueError, "already exists"):
            monitoring.add("datadog", "prod", "app.datadoghq.com")
        with self.assertRaisesRegex(ValueError, "no longer saved"):
            monitoring.remove("datadog-staging")
        self.assertFalse(self.store.with_suffix(".tmp").exists())

    def test_hand_edited_rows_that_are_not_dashboards_are_ignored(self):
        self.store.parent.mkdir(parents=True)
        self.store.write_text(json.dumps([{"service": "grafana", "name": "Ok", "url": "https://a.example"},
                                          {"service": "unknown", "name": "X", "url": "https://b.example"}, "junk"]))
        self.assertEqual([row["id"] for row in monitoring.dashboards()], ["grafana-ok"])

    def test_development_menu_offers_monitoring(self):
        rows = json.loads((ROOT / "elephant/menu-rows/development.json").read_text())
        row = next(row for row in rows if row.get("submenu") == "monitoring")
        self.assertEqual(row["text"], "Monitoring")
        self.assertIn("datadog", row["keywords"])
        self.assertFalse(any(row.get("submenu") == "grafana-logs" for row in rows))
        menu = (ROOT / "elephant/menus/monitoring.lua").read_text()
        self.assertNotIn("aws-grafana", menu, "Amazon Managed Grafana lives with the AWS tools")
        cloud = json.loads((ROOT / 'walker/scripts/menus/cloud/navigation-menus.json').read_text())
        self.assertTrue(any(row.get('submenu') == 'aws-grafana' for row in cloud['aws-account']['actions']))
        self.assertIn('SubMenu = "monitoring-tools"', menu)
        self.assertIn("dashboard_remove", menu)
        self.assertLess(menu.index('"Monitoring Tools"'), menu.index('"Add Dashboard"'), "submenus come first")
        self.assertIn('SoftwareGroup = "monitoring"', (ROOT / "elephant/menus/monitoring-tools.lua").read_text())
        for name in ("monitoring", "monitoring-tools"):
            self.assertTrue((ROOT / f"walker/themes/current/item_menus-{name}.xml").is_file(), name)

    def test_delete_removes_a_dashboard_and_the_tools_are_packaged(self):
        actions = tomllib.loads((ROOT / "walker/config.toml").read_text())["providers"]["actions"]["menus:monitoring"]
        self.assertIn({"action": "dashboard_remove", "label": "Remove", "bind": "Delete", "after": "AsyncReload"}, actions)
        group = json.loads((ROOT / "distro/software.json").read_text())["monitoring"]
        self.assertEqual({recipe["packages"][0] for recipe in group.values()}, {"prometheus", "sentry-cli"})

    def test_service_icons_are_neutral_nerd_font_glyphs(self):
        # The Nerd Font's devicons for these services are their logos; EITR ships no brand icons.
        logos = {"", "", "", "", ""}
        for service in monitoring.SERVICES.values():
            self.assertEqual(len(service["icon"]), 1)
            self.assertNotIn(service["icon"], logos)


if __name__ == "__main__":
    unittest.main()
