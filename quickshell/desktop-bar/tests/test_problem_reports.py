from bar_frame_source import frame_source
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


BAR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("problem_reports", BAR / "scripts/problem-reports.py")
reports = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reports)



class ProblemReportTests(unittest.TestCase):
    def test_welcome_and_control_center_share_the_preference(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"XDG_CONFIG_HOME": directory, "XDG_STATE_HOME": directory}):
            self.assertEqual(reports.status(), {"offer": True, "asked": False})
            self.assertEqual(reports.choose("off"), {"offer": False, "asked": True})
            self.assertEqual(reports.choose("on"), {"offer": True, "asked": True})
            self.assertTrue(json.loads((Path(directory) / "eitr/crash-help.json").read_text())["enabled"])

    def test_bar_does_not_start_a_second_crash_watcher(self):
        shell = ((BAR / "shell.qml").read_text() + frame_source(BAR))
        self.assertNotIn('id: problemCheck', shell)
        self.assertNotIn('problem-notify.sh', shell)
