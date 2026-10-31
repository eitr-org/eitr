import contextlib
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "walker/scripts/actions/tools/dictate.sh"


class DictationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.log = self.base / "log"
        (self.base / "runtime").mkdir()
        # Only the stand-ins below and basic tools: a real whisper-cli or wtype must not be found.
        tools = self.base / "tools"
        tools.mkdir()
        for name in ("flock", "timeout", "bash", "cat", "cp", "cut", "date", "mkdir", "mv", "rm", "sed", "sha256sum", "sleep", "tr"):
            (tools / name).symlink_to(shutil.which(name))
        self.env = {"PATH": f"{self.bin}:{tools}", "HOME": str(self.base / "home"),
                    "XDG_DATA_HOME": str(self.base / "data"), "XDG_RUNTIME_DIR": str(self.base / "runtime"),
                    "EITR_CODE_ROOT": str(ROOT)}
        self.fake("notify-send", 'echo "notify $*" >> "$LOG"')
        self.fake("wtype", 'echo "typed $*" >> "$LOG"')
        # Records until stopped, but never outlives the test: a stray copy ends by itself.
        self.fake("pw-record", 'echo audio > "${@: -1}"; exec /usr/bin/sleep 5')
        self.addCleanup(self.stop_recorder)
        # Runs before the folder is removed: start leaves a supervisor behind that
        # still writes into the runtime folder after the test's last assertion.
        self.groups = []
        self.addCleanup(self.end_background_work)
        self.fake("whisper-cli", 'echo "model $2" >> "$LOG"; printf " Hello there.\\n"')
        self.fake("curl", 'echo "download" >> "$LOG"; exit 22')
        self.fake("eitr-shell", 'echo "bar $*" >> "$LOG"')

    def stop_recorder(self):
        pidfile = self.base / "runtime/eitr-dictation.pid"
        if pidfile.exists():
            subprocess.run(["kill", pidfile.read_text().strip()], capture_output=True)

    def end_background_work(self):
        for group in self.groups:
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                try:
                    os.killpg(group, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
            else:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(group, signal.SIGKILL)

    def fake(self, name, body):
        path = self.bin / name
        path.write_text(f'#!/usr/bin/env bash\nLOG="{self.log}"\n{body}\n')
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def wait_for_recording(self):
        """start returns while its supervisor publishes the recorder's pid."""
        pid = self.base / "runtime/eitr-dictation.pid"
        deadline = time.monotonic() + 2
        while not pid.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        return pid.exists()

    def run_script(self, *arguments, tap=False):
        # A release ends a hold unless the test asks for a tap (released at once).
        if arguments[:1] == ("stop",) and not tap:
            mode = arguments[1] if len(arguments) > 1 else "dictation"
            press = self.base / f"runtime/eitr-{mode}.pressed"
            if press.exists():
                press.write_text(str(time.time_ns() - 2_000_000_000))
        process = subprocess.Popen(["bash", str(SCRIPT), *arguments], env=self.env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, start_new_session=True)
        self.groups.append(process.pid)
        stdout, stderr = process.communicate(timeout=20)
        return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)

    def logged(self):
        return self.log.read_text() if self.log.exists() else ""

    def test_hold_and_release_types_the_words(self):
        model = self.base / "data/eitr/whisper/ggml-base.bin"
        model.parent.mkdir(parents=True)
        model.write_text("model")
        self.assertEqual(self.run_script("start").returncode, 0)
        self.assertEqual(self.run_script("stop").returncode, 0)
        self.assertIn(f"model {model}", self.logged())
        self.assertIn("typed -- Hello there.", self.logged())
        self.assertNotIn("notify", self.logged(), "a successful dictation shows no notification")
        bar = [line for line in self.logged().splitlines() if line.startswith("bar ")]
        self.assertEqual(bar, ["bar desktop-bar ipc call dictation start", "bar desktop-bar ipc call dictation transcribe",
                               "bar desktop-bar ipc call dictation stop"],
                         "a waveform while listening, a pulse while transcribing")
        lines = self.logged().splitlines()
        self.assertLess(lines.index("typed -- Hello there."), lines.index("bar desktop-bar ipc call dictation stop"),
                        "the indicator stays until the words are typed")
        self.assertFalse(any(path.suffix != ".lock" for path in (self.base / "runtime").iterdir()), "the recording is deleted")

    def ready_model(self):
        model = self.base / "data/eitr/whisper/ggml-base.bin"
        model.parent.mkdir(parents=True)
        model.write_text("model")

    def wait_for_log(self, message):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if message in self.logged():
                return
            time.sleep(0.01)
        self.fail(f"Timed out waiting for {message}: {self.logged()}")

    def test_release_waits_for_start_indicator(self):
        self.ready_model()
        self.fake("eitr-shell", 'if [[ "${@: -1}" == start ]]; then echo starting >> "$LOG"; sleep 0.3; fi; echo "bar $*" >> "$LOG"')
        self.assertEqual(self.run_script("start").returncode, 0)
        self.wait_for_log("starting")
        self.assertEqual(self.run_script("stop").returncode, 0)
        states = [line.rsplit(" ", 1)[-1] for line in self.logged().splitlines() if line.startswith("bar ")]
        self.assertEqual(states, ["start", "transcribe", "stop"])
        self.assertIn("typed -- Hello there.", self.logged())

    def test_a_tap_keeps_recording_and_the_next_press_stops_and_types(self):
        self.ready_model()
        self.assertEqual(self.run_script("start").returncode, 0)
        self.assertTrue(self.wait_for_recording())
        # Released right after the press: a tap, so the recording goes on.
        self.assertEqual(self.run_script("stop", tap=True).returncode, 0)
        self.assertTrue((self.base / "runtime/eitr-dictation.pid").exists())
        self.assertNotIn("typed", self.logged())
        # The next press stops it and types; that press's own release does nothing.
        self.assertEqual(self.run_script("start").returncode, 0)
        self.assertIn("typed -- Hello there.", self.logged())
        self.assertFalse((self.base / "runtime/eitr-dictation.pid").exists())
        self.assertEqual(self.run_script("stop", tap=True).returncode, 0)
        self.assertEqual(self.logged().count("typed --"), 1)

    def test_a_release_that_wins_the_race_is_a_tap_not_a_stuck_recording(self):
        self.ready_model()
        # Release first (nothing recording yet), then the press: it simply records,
        # and a second press stops it.
        self.assertEqual(self.run_script("stop", tap=True).returncode, 0)
        self.assertEqual(self.run_script("start").returncode, 0)
        self.assertTrue(self.wait_for_recording())
        self.assertEqual(self.run_script("start").returncode, 0)
        self.assertFalse((self.base / "runtime/eitr-dictation.pid").exists())

    def test_release_waits_for_pid_publication(self):
        self.ready_model()
        self.fake("flock", '/usr/bin/flock "$@"; if [[ "$*" == 9 ]] && mkdir "$XDG_RUNTIME_DIR/gate" 2>/dev/null; then echo locked >> "$LOG"; sleep 0.3; fi')
        start = subprocess.Popen(["bash", str(SCRIPT), "start"], env=self.env,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        self.groups.append(start.pid)
        self.addCleanup(start.wait)
        self.wait_for_log("locked")
        self.assertFalse((self.base / "runtime/eitr-dictation.pid").exists())
        self.assertEqual(self.run_script("stop").returncode, 0)
        self.assertEqual(start.wait(timeout=5), 0)
        start.communicate()
        states = [line.rsplit(" ", 1)[-1] for line in self.logged().splitlines() if line.startswith("bar ")]
        self.assertEqual(states, ["start", "transcribe", "stop"])
        self.assertFalse((self.base / "runtime/eitr-dictation.pid").exists())

    def test_recording_limit_transcribes_and_ends_indicator(self):
        self.ready_model()
        # Exercise the real timeout with a short clock, checking the production limit.
        self.fake("timeout", 'echo "timeout $*" >> "$LOG"; shift 3; exec /usr/bin/timeout --signal=INT --kill-after=0.1 0.1 "$@"')
        self.assertEqual(self.run_script("start").returncode, 0)
        self.wait_for_log("bar desktop-bar ipc call dictation stop")
        self.assertIn("timeout --signal=INT --kill-after=2 120 pw-record", self.logged())
        self.assertIn("typed -- Hello there.", self.logged())
        self.assertFalse((self.base / "runtime/eitr-dictation.pid").exists())
        self.assertFalse((self.base / "runtime/eitr-dictation.wav").exists())

    def test_recorder_exit_ends_indicator_without_release(self):
        self.ready_model()
        self.fake("pw-record", 'echo audio > "${@: -1}"; sleep 0.1; exit 1')
        self.assertEqual(self.run_script("start").returncode, 0)
        self.wait_for_log("bar desktop-bar ipc call dictation stop")
        self.assertFalse((self.base / "runtime/eitr-dictation.pid").exists())

    def test_nothing_heard_still_ends_the_indicator(self):
        model = self.base / "data/eitr/whisper/ggml-base.bin"
        model.parent.mkdir(parents=True)
        model.write_text("model")
        self.fake("whisper-cli", 'printf "[BLANK_AUDIO]\\n"')
        self.run_script("start")
        self.assertEqual(self.run_script("stop").returncode, 0)
        self.assertIn("Nothing heard", self.logged())
        bar = [line for line in self.logged().splitlines() if line.startswith("bar ")]
        self.assertEqual(bar[-1], "bar desktop-bar ipc call dictation stop")

    def test_a_failed_download_explains_and_records_nothing(self):
        self.assertEqual(self.run_script("start").returncode, 0)
        self.assertIn("download", self.logged())
        self.assertIn("could not be downloaded", self.logged())
        self.assertFalse((self.base / "data/eitr/whisper/ggml-base.bin").exists())
        self.assertFalse((self.base / "runtime/eitr-dictation.pid").exists())

    def test_missing_packages_point_to_the_install_menu(self):
        (self.bin / "whisper-cli").unlink()
        self.run_script("start")
        self.assertIn("System Update", self.logged())

    def test_release_without_a_recording_does_nothing(self):
        self.assertEqual(self.run_script("stop").returncode, 0)
        self.assertEqual(self.logged(), "")

    def test_voice_mode_uses_the_same_model_without_typing(self):
        model = self.base / "data/eitr/whisper/ggml-base.bin"
        model.parent.mkdir(parents=True)
        model.write_text("model")
        self.fake("python3", 'echo "voice $*" >> "$LOG"; cat >> "$LOG"')
        for action in ("start", "stop"):
            result = self.run_script(action, "voice")
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"model {model}", self.logged())
        self.assertIn("voice-command.py stdin", self.logged())
        self.assertIn("Hello there.", self.logged())
        self.assertNotIn("typed --", self.logged())
        self.assertFalse(any(path.suffix != ".lock" for path in (self.base / "runtime").iterdir()))

    def test_transcription_failure_cleans_audio_and_indicator(self):
        model = self.base / "data/eitr/whisper/ggml-base.bin"
        model.parent.mkdir(parents=True)
        model.write_text("model")
        self.fake("whisper-cli", 'exit 1')
        self.run_script("start")
        self.assertEqual(self.run_script("stop").returncode, 1)
        self.assertIn("dictation stop", self.logged())
        self.assertFalse(any(path.suffix != ".lock" for path in (self.base / "runtime").iterdir()))

    def test_the_bar_shows_the_recording_dot_while_listening(self):
        bar = ROOT / "quickshell/desktop-bar"
        shell = (bar / "shell.qml").read_text() + (bar / "CaptureIndicator.qml").read_text() + (bar / "DictationState.qml").read_text()
        self.assertIn('target: "dictation"', shell)
        sections = [(bar / name).read_text() for name in ("BarHorizontalCenter.qml", "BarVerticalCenter.qml")]
        for source, owner in zip(sections, ("centerSection", "verticalMiddle")):
            for field in ("dictating", "transcribing", "dictationLevels"):
                self.assertIn(f"{field}: {owner}.host.{field}", source)
        self.assertIn('text: capture.dictating ? Eitr.I18n.tr("Dictating") : capture.transcribing ? Eitr.I18n.tr("Transcribing")', shell)
        # The indicator sits just before the clock on both bar orientations.
        self.assertTrue((bar / "CaptureIndicator.qml").read_text().startswith("import QtQuick"))
        self.assertRegex(sections[0], r"id: barCapture\s+anchors.right: centerInfo.left")
        self.assertRegex(sections[1], r"id: verticalCapture\s+anchors.bottom: verticalCalendarIcon.top")
        self.assertIn("node: Pipewire.defaultAudioSource", shell, "the waveform follows the microphone dictation records")
        self.assertIn("enabled: dictation.dictating && node !== null", shell, "the microphone is only metered while listening")
        self.assertIn("Behavior on height { enabled: !capture.transcribing;", shell,
                      "a per-frame pulse under a restarting Behavior stays flat")

    def test_the_model_is_pinned_and_the_key_installed(self):
        source = SCRIPT.read_text()
        self.assertIn('model_sha256="60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe"', source)
        hypr = (ROOT / "hypr/hyprland.lua").read_text()
        self.assertIn('hl.bind("D",', hypr)
        self.assertIn('{ release = true, ignore_mods = true, non_consuming = true }', hypr)
        self.assertIn('" stop voice"', hypr)
        self.assertNotIn('" stop"), { release = true })', hypr)
        packages = (ROOT / "distro/packages.txt").read_text().split()
        self.assertTrue({"whisper-cpp", "wtype"} <= set(packages), "dictation is part of every installation")
        self.assertIn("SUPER + D (hold)", (ROOT / "elephant/shortcut-reference.json").read_text())


if __name__ == "__main__":
    unittest.main()
