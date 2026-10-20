from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = "walker/scripts/menus/capture/screenrecord.sh"


class ScreenRecordingMenuTests(unittest.TestCase):
    def run_mode(self, mode, fail=False):
        with tempfile.TemporaryDirectory() as directory:
            code = Path(directory)
            (code / SCRIPT).parent.mkdir(parents=True)
            shutil.copy2(ROOT / SCRIPT, code / SCRIPT)
            control = code / "quickshell/desktop-bar/scripts/obs-control.py"
            control.parent.mkdir(parents=True)
            # A stand-in for the OBS helper: it records each call and can refuse.
            control.write_text("import os, sys\nopen(os.environ['LOG'], 'a').write(' '.join(sys.argv[1:]) + '\\n')\n"
                               "sys.exit(1 if os.environ.get('FAIL') else 0)\n")
            stubs = code / "bin"
            stubs.mkdir()
            (stubs / "notify-send").write_text('#!/bin/sh\necho "notify $*" >> "$LOG"\n')
            (stubs / "notify-send").chmod(0o755)
            log = code / "log"
            result = subprocess.run(["bash", str(code / SCRIPT), mode], capture_output=True, text=True,
                                    env={**os.environ, "EITR_CODE_ROOT": str(code), "LOG": str(log),
                                         "PATH": f"{stubs}:/usr/bin:/bin", **({"FAIL": "1"} if fail else {})})
            return result, log.read_text().splitlines() if log.exists() else []

    def test_modes_set_the_panel_options_then_record(self):
        result, calls = self.run_mode("audio-webcam")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ["set-option audio true", "set-option mic true", "set-option webcam true",
                                 "prepare", "record"])
        _, calls = self.run_mode("record")
        self.assertEqual(calls[:3], ["set-option audio false", "set-option mic false", "set-option webcam false"])

    def test_stop_and_errors_go_through_the_helper(self):
        _, calls = self.run_mode("stop")
        self.assertEqual(calls, ["stop"])
        result, calls = self.run_mode("webcam", fail=True)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(calls[-1].startswith("notify OBS"), "a refusal is shown, not swallowed")

    def test_no_obs_websocket_address_is_committed(self):
        # obs-control.py reads the password from OBS's own settings; it never belongs in the repository.
        tracked = subprocess.run(["git", "-C", str(ROOT), "grep", "-l", "obsws://localhost"], capture_output=True, text=True)
        self.assertEqual([name for name in tracked.stdout.split() if not name.endswith("obs-control.py")
                          and "/tests/" not in name], [])


if __name__ == "__main__":
    unittest.main()
