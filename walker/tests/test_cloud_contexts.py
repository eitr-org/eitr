import importlib.util
import contextlib
import io
import json
import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("contexts", ROOT / "walker/scripts/menus/cloud/contexts.py")
cloud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cloud)


class ContextTests(unittest.TestCase):
    def test_google_selection_is_process_local(self):
        context = {"label": "Production", "configuration": "prod", "account": "dev@example.org", "project": "prod-project"}
        before = dict(os.environ)
        values = cloud.environment("gcp", context)
        self.assertEqual(values["CLOUDSDK_ACTIVE_CONFIG_NAME"], "prod")
        self.assertEqual(values["CLOUDSDK_CORE_PROJECT"], "prod-project")
        self.assertIn("dev@example.org", values["EITR_CLOUD_CONTEXT"])
        self.assertEqual(dict(os.environ), before)

    def test_context_menu_opens_before_login_or_project_discovery(self):
        with patch.object(cloud, "query") as query:
            values = cloud.environment("gcp", {"label": "Detected", "configuration": "detected", "account": "a", "project": ""})
        query.assert_not_called()
        self.assertEqual(values["CLOUDSDK_ACTIVE_CONFIG_NAME"], "detected")

    def gcloud_config(self, files):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        configurations = Path(directory.name) / "configurations"
        configurations.mkdir()
        for name, text in files.items():
            (configurations / ("config_" + name)).write_text(text)
        return patch.dict(os.environ, {"CLOUDSDK_CONFIG": directory.name})

    def test_google_configurations_are_read_without_starting_gcloud(self):
        files = {"prod": "[core]\naccount = person@example.org\nproject = prod-project\n",
                 "signed-out": "[core]\nproject = other-project\n", "broken": "[core\n"}
        with self.gcloud_config(files), patch.object(cloud, "query") as query, \
                patch.object(cloud.CONFIG.__class__, "exists", return_value=False):
            rows = cloud.contexts("gcp")
        query.assert_not_called()
        self.assertEqual(rows, [{"configuration": "prod", "account": "person@example.org",
                                 "project": "prod-project", "label": "prod"}])

    def test_google_missing_project_is_not_overridden_with_an_empty_value(self):
        with self.gcloud_config({"default": "[core]\naccount = person@example.org\n"}), \
                patch.object(cloud.CONFIG.__class__, "exists", return_value=False):
            context = cloud.contexts("gcp")[0]
        self.assertEqual(context["project"], "")
        values = cloud.environment("gcp", context)
        self.assertTrue(all(isinstance(value, str) for value in values.values()))
        self.assertNotIn("CLOUDSDK_CORE_PROJECT", values)

    def azure_profile(self, subscriptions, config=""):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        # The Azure CLI writes its profile with a byte order mark.
        (Path(directory.name) / "azureProfile.json").write_text(
            "\ufeff" + json.dumps({"subscriptions": subscriptions}), encoding="utf-8")
        (Path(directory.name) / "config").write_text(config)
        return patch.dict(os.environ, {"AZURE_CONFIG_DIR": directory.name})

    def test_azure_only_lists_enabled_subscriptions_of_the_active_cloud_without_starting_az(self):
        subscriptions = [
            {"id": "one", "tenantId": "tenant", "name": "Dev", "state": "Enabled", "environmentName": "AzureCloud"},
            {"id": "two", "tenantId": "tenant", "name": "Old", "state": "Disabled", "environmentName": "AzureCloud"},
            {"id": "three", "tenantId": "tenant", "name": "Gov", "state": "Enabled", "environmentName": "AzureUSGovernment"}]
        with self.azure_profile(subscriptions), patch.object(cloud, "query") as query, \
                patch.object(cloud.CONFIG.__class__, "exists", return_value=False):
            rows = cloud.contexts("azure")
        query.assert_not_called()
        self.assertEqual([row["subscription"] for row in rows], ["one"])
        self.assertEqual(rows[0]["tenant"], "tenant")
        with self.azure_profile(subscriptions, "[cloud]\nname = AzureUSGovernment\n"), \
                patch.object(cloud.CONFIG.__class__, "exists", return_value=False):
            self.assertEqual([row["subscription"] for row in cloud.contexts("azure")], ["three"])

    def test_azure_without_a_profile_has_no_contexts(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with patch.dict(os.environ, {"AZURE_CONFIG_DIR": directory.name}), \
                patch.object(cloud.CONFIG.__class__, "exists", return_value=False):
            self.assertEqual(cloud.contexts("azure"), [])

    def test_identifiers_cannot_inject_generated_shell_commands(self):
        with self.assertRaises(ValueError):
            cloud.environment("azure", {"label": "Bad", "subscription": "'; exit; #", "tenant": "t"})
        with self.assertRaises(ValueError):
            cloud.environment("gcp", {"label": "Bad", "configuration": "dev", "account": "a", "project": "'; exit; #"})
