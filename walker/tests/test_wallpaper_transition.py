import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlparse

from home_isolation import setUpModule, tearDownModule  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("transition", ROOT / "walker/scripts/actions/wallpaper/transition.py")
transition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transition)


class WallpaperTests(unittest.TestCase):
    def setUp(self):
        hooks = patch.object(transition, "dispatch_hooks")
        self.hooks = hooks.start()
        self.addCleanup(hooks.stop)
        # commit() refreshes the login copy in the background; tests never start it.
        refresh = patch.object(transition.subprocess, "Popen")
        self.refresh_login = refresh.start()
        self.addCleanup(refresh.stop)
        # No test reads the real monitors; tests that need some patch this again.
        monitors = patch.object(transition.subprocess, "check_output", return_value="[]")
        monitors.start()
        self.addCleanup(monitors.stop)

    def test_success_does_not_reapply_after_transition(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "wallpaper.png"
            image.write_bytes(b"mock")
            with patch.object(transition, "runtime", return_value=Path(directory)), \
                    patch.object(transition, "snapshot", return_value=""), \
                    patch.object(transition.subprocess, "run"), patch.object(transition, "commit") as commit:
                transition.apply(str(image))
                commit.assert_not_called()
                self.hooks.assert_called_once_with("wallpaper-changed", EITR_WALLPAPER=str(image.resolve()))

    def test_backing_wallpaper_changes_only_under_completed_reveal(self):
        qml = (ROOT / "quickshell/wallpaper-transition/shell.qml").read_text()
        self.assertNotIn("commit.running = true", qml.split("NumberAnimation")[0])
        self.assertIn("if (exitCode === 0) handoff.start()", qml)
        self.assertIn("onFinished: commit.running = true", qml)
        self.assertIn("prepare.start()", qml)
        self.assertIn("onTriggered: Qt.exit(1)", qml)

    def test_transition_does_not_capture_input(self):
        qml = (ROOT / "quickshell/wallpaper-transition/shell.qml").read_text()
        self.assertIn("WlrLayer.Bottom", qml)
        self.assertIn("mask: Region {}", qml)
        self.assertIn("duration: 650", qml)
        self.assertIn("anchors.centerIn", qml)
        self.assertIn("maskSource: circleMask", qml)
        self.assertIn("Math.sqrt(window.width * window.width + window.height * window.height)", qml)

    def test_failure_still_commits_static_wallpaper(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "wallpaper.png"
            image.write_bytes(b"mock")
            with patch.object(transition, "runtime", return_value=Path(directory)), \
                    patch.object(transition, "snapshot", return_value=""), \
                    patch.object(transition.subprocess, "run", side_effect=OSError("missing quickshell")), \
                    patch.object(transition, "commit") as commit:
                transition.apply(str(image))
                commit.assert_called_once_with(str(image.resolve()))

    def test_one_failing_monitor_still_persists_wallpaper(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            image = home / "wallpaper.png"
            image.write_bytes(b"mock")
            monitors = '[{"name": "DP-1"}, {"name": "HDMI-A-1"}]'
            calls = []

            def run(command, check):
                calls.append(command[-1])
                if command[-1].startswith("DP-1,"):
                    raise subprocess.CalledProcessError(1, command)

            with patch.object(transition.Path, "home", return_value=home), \
                    patch.object(transition.subprocess, "check_output", return_value=monitors), \
                    patch.object(transition.subprocess, "run", side_effect=run):
                with self.assertRaisesRegex(transition.CommitError, "DP-1"):
                    transition.commit(str(image))
            self.assertEqual(len(calls), 2, "every monitor is attempted")
            self.assertEqual((home / ".cache/current-wallpaper-image").resolve(), image.resolve())
            self.assertEqual((home / ".cache/current-wallpaper").read_text().strip(), str(image.resolve()))

    def test_ultrawide_monitors_get_the_21_9_version(self):
        with tempfile.TemporaryDirectory() as directory:
            theme = Path(directory) / "theme"
            (theme / "backgrounds").mkdir(parents=True)
            (theme / "backgrounds-ultrawide").mkdir()
            image = theme / "backgrounds/01-first.png"
            image.write_bytes(b"mock")
            (theme / "backgrounds-ultrawide/01-first.jpg").write_bytes(b"mock")
            (theme / "backgrounds/02-second.png").write_bytes(b"mock")
            ultrawide = {"width": 3440, "height": 1440, "transform": 0}
            self.assertEqual(transition.for_monitor(image, ultrawide), str(theme / "backgrounds-ultrawide/01-first.jpg"))
            self.assertEqual(transition.for_monitor(image, {"width": 3840, "height": 2160}), str(image))
            self.assertEqual(transition.for_monitor(image, {**ultrawide, "transform": 1}), str(image), "rotated is tall")
            second = theme / "backgrounds/02-second.png"
            self.assertEqual(transition.for_monitor(second, ultrawide), str(second), "no version: the 16:9 file")

            calls = []
            monitors = '[{"name": "DP-3", "width": 2560, "height": 1080}, {"name": "HDMI-A-1", "width": 1920, "height": 1080}]'
            with patch.object(transition.Path, "home", return_value=Path(directory)), \
                    patch.object(transition.subprocess, "check_output", return_value=monitors), \
                    patch.object(transition.subprocess, "run", side_effect=lambda command, check: calls.append(command[-1])):
                transition.commit(str(image))
            self.assertEqual(calls, [f"DP-3,{theme}/backgrounds-ultrawide/01-first.jpg", f"HDMI-A-1,{image}"])
            self.assertEqual((Path(directory) / ".cache/current-wallpaper").read_text().strip(), str(image),
                             "the saved choice stays the theme's wallpaper")
            self.assertEqual((Path(directory) / ".cache/eitr/hyprpaper-monitors.conf").read_text(),
                             f"wallpaper {{\n    monitor = DP-3\n    path = {theme}/backgrounds-ultrawide/01-first.jpg\n"
                             "    fit_mode = cover\n}\n", "Hyprpaper starts the ultrawide on its version")
            config = (ROOT / "hypr/hyprpaper.conf").read_text()
            self.assertIn("source = ~/.cache/eitr/hyprpaper-monitors.conf", config)
            refresh = self.refresh_login.call_args.args[0]
            self.assertEqual(refresh[-2:], [str(transition.code("quickshell/lockscreen/scripts/settings.py")),
                                            "refresh-login"], "the login copy follows the wallpaper")

    def test_each_monitor_reveals_from_what_it_shows_to_what_commit_gives_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "run"
            run_dir.mkdir()
            theme = root / "theme"
            (theme / "backgrounds").mkdir(parents=True)
            (theme / "backgrounds-ultrawide").mkdir()
            old, old_wide = theme / "backgrounds/01-old.png", theme / "backgrounds-ultrawide/01-old.jpg"
            new, new_wide = theme / "backgrounds/02-new.png", theme / "backgrounds-ultrawide/02-new.jpg"
            for image in (old, old_wide, new, new_wide):
                image.write_bytes(image.name.encode())
            (root / ".cache").mkdir()
            (root / ".cache/current-wallpaper-image").symlink_to(old)
            listing = f"DP-3: {old_wide}\nHDMI-A-1: {old}"
            monitors = '[{"name": "DP-3", "width": 2560, "height": 1080}, {"name": "HDMI-A-1", "width": 1920, "height": 1080}]'
            seen = {}

            def run(command, **options):
                if command[:3] == ["hyprctl", "hyprpaper", "listactive"]:
                    return subprocess.CompletedProcess(command, 0, listing, "")
                if "wallpaper-transition" in command:
                    seen.update(options["env"])
                    copies = json.loads(seen["EITR_PREVIOUS_WALLPAPERS"])
                    seen["previous bytes"] = {name: Path(unquote(urlparse(uri).path)).read_bytes()
                                              for name, uri in copies.items()}
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch.object(transition, "runtime", return_value=run_dir), \
                    patch.object(transition.Path, "home", return_value=root), \
                    patch.object(transition.subprocess, "check_output", return_value=monitors), \
                    patch.object(transition.subprocess, "run", side_effect=run):
                transition.apply(str(new))
            self.assertEqual(seen["previous bytes"], {"*": b"01-old.png", "DP-3": b"01-old.jpg", "HDMI-A-1": b"01-old.png"},
                             "the ultrawide starts from its 21:9 image")
            following = json.loads(seen["EITR_NEXT_WALLPAPERS"])
            self.assertEqual(following, {"DP-3": new_wide.as_uri(), "HDMI-A-1": new.as_uri(), "*": new.as_uri()})
            self.assertEqual(list(run_dir.glob("previous-*")), [], "the copies and the manifest are removed")

    def test_transition_picks_each_screens_image(self):
        qml = (ROOT / "quickshell/wallpaper-transition/shell.qml").read_text()
        self.assertIn('source: window.previousImage', qml)
        self.assertIn('source: root.imageFor(root.nextImages, window.modelData.name, root.next)', qml)
        self.assertIn('Quickshell.env("EITR_NEXT_WALLPAPERS")', qml)

    def restore_in(self, home, saved, active):
        theme = home / "theme/backgrounds"
        theme.mkdir(parents=True)
        for name in ("02-second.png", "01-first.png"):
            (theme / name).write_bytes(b"mock")
        cache = home / "cache"
        cache.mkdir()
        (cache / "current-wallpaper").write_text(str(saved) + "\n")
        listing = "\n".join(f"{monitor}: {path}" for monitor, path in active.items())
        with patch.object(transition, "cache_dir", return_value=cache), \
                patch.object(transition, "user_config", return_value=theme), \
                patch.object(transition.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, listing, "")), \
                patch.object(transition.subprocess, "check_output", return_value='[{"name": "DP-1"}]'), \
                patch.object(transition, "commit") as commit:
            restored = transition.restore(attempts=1, delay=0)
        return theme, restored, commit

    def test_restore_falls_back_to_the_first_wallpaper_when_the_saved_one_is_gone(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            theme, restored, commit = self.restore_in(home, home / "theme/backgrounds/07-renamed.png", {})
            first = str((theme / "01-first.png").resolve())
            self.assertEqual(restored, first)
            commit.assert_called_once_with(first)

    def test_restore_follows_a_wallpaper_that_changed_format(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            theme, restored, commit = self.restore_in(home, home / "theme/backgrounds/02-second.jpg", {})
            # restore_in creates PNGs; the saved .jpg name finds the .png of the same wallpaper.
            second = str((theme / "02-second.png").resolve())
            self.assertEqual(restored, second)
            commit.assert_called_once_with(second)

    def test_restore_leaves_a_correct_wallpaper_alone(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            saved = home / "theme/backgrounds/02-second.png"
            (home / "theme/backgrounds").mkdir(parents=True)
            saved.write_bytes(b"mock")
            cache = home / "cache"
            cache.mkdir()
            (cache / "current-wallpaper").write_text(str(saved) + "\n")
            (cache / "current-wallpaper-image").symlink_to(saved)
            with patch.object(transition, "cache_dir", return_value=cache), \
                    patch.object(transition.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, f"DP-1: {saved}", "")), \
                    patch.object(transition.subprocess, "check_output", return_value='[{"name": "DP-1"}]'), \
                    patch.object(transition, "commit") as commit:
                transition.restore(attempts=1, delay=0)
            commit.assert_not_called()

    def test_session_checks_the_wallpaper_without_blocking(self):
        session = (ROOT / "distro/bin/eitr-session").read_text()
        self.assertIn("wallpaper/transition.py')), 'restore']", session)
        self.assertIn("subprocess.Popen(", session)

    def test_apply_fallback_commit_failure_is_not_fatal(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "wallpaper.png"
            image.write_bytes(b"mock")
            with patch.object(transition, "runtime", return_value=Path(directory)), \
                    patch.object(transition, "snapshot", return_value=""), \
                    patch.object(transition.subprocess, "run", side_effect=OSError("missing quickshell")), \
                    patch.object(transition, "commit", side_effect=transition.CommitError("hyprpaper failed on: DP-1")), \
                    patch("sys.stderr"):
                transition.apply(str(image))

    def test_image_errors_fail_immediately(self):
        qml = (ROOT / "quickshell/wallpaper-transition/shell.qml").read_text()
        self.assertIn("status === Image.Error", qml)
        self.assertEqual(qml.count("onStatusChanged: root.failOnError(status)"), 2)

    def test_wallpapers_are_listed_in_natural_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("10.png", "2.JPG", "1.webp", "notes.txt"):
                (root / name).write_bytes(b"mock")
            names = [path.name for path in transition.wallpapers(root)]
            self.assertEqual(names, ["1.webp", "2.JPG", "10.png"])
            self.assertEqual(transition.wallpapers(root / "missing"), [])

    def test_every_existing_wallpaper_entrypoint_uses_shared_helper(self):
        for filename in ("walker/scripts/actions/wallpaper/apply.sh", "walker/scripts/actions/style/apply.sh"):
            self.assertIn("transition.py", (ROOT / filename).read_text())
        for filename in ("walker/scripts/actions/wallpaper/next.sh",):
            self.assertIn("/wallpaper/apply.sh", (ROOT / filename).read_text())
