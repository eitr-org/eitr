import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "walker/tests"))
from home_isolation import setUpModule, tearDownModule
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("obs_control", Path(__file__).parents[1] / "scripts/obs-control.py")
obs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(obs)


class ObsControlTests(unittest.TestCase):
    def setUp(self):
        seeded = patch.object(obs, "default_scene_collection")
        seeded.start()
        self.addCleanup(seeded.stop)

    def test_prepare_does_not_start_capture(self):
        with patch.object(obs.subprocess, "run", side_effect=[SimpleNamespace(returncode=1), SimpleNamespace(returncode=0)]) as run, \
                patch.object(obs, "websocket_command", return_value=["obs-cmd"]), \
                patch.object(obs, "launch_background"), patch.object(obs, "apply_capture_options") as apply, \
                patch.object(obs, "default_recording_folder") as default_folder:
            self.assertEqual(obs.control("prepare"), "OBS ready")
            default_folder.assert_called_once_with()
            apply.assert_called_once_with(["obs-cmd"])
            self.assertEqual(run.call_args.args[0], ["obs-cmd", "info"])

    def recording_profile(self, directory, text=None):
        profile = Path(directory) / "config/obs-studio/basic/profiles/Untitled/basic.ini"
        if text is not None:
            profile.parent.mkdir(parents=True)
            profile.write_text(text)
        home = Path(directory) / "home"
        with patch.object(obs, "user_config", side_effect=lambda relative: Path(directory) / "config" / relative), \
                patch.object(obs.Path, "home", return_value=home):
            changed = obs.default_recording_folder()
        self.assertTrue((home / "Videos/Records").is_dir())
        return changed, profile.read_text() if profile.exists() else None, home

    def test_a_new_obs_profile_records_into_videos_records(self):
        with tempfile.TemporaryDirectory() as directory:
            changed, text, home = self.recording_profile(directory)
            self.assertTrue(changed)
            self.assertIn(f"[SimpleOutput]\nFilePath={home}/Videos/Records", text)
            self.assertIn(f"[AdvOut]\nRecFilePath={home}/Videos/Records\nFFFilePath={home}/Videos/Records", text)

    def test_obs_home_folder_default_is_replaced_but_a_chosen_folder_is_kept(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            original = (f"[General]\nName=Untitled\n\n[SimpleOutput]\nFilePath={home}\nRecFormat2=hybrid_mp4\n\n"
                        "[AdvOut]\nRecFilePath=/mnt/clips\nRecFormat2=mkv\n")
            changed, text, _ = self.recording_profile(directory, original)
            self.assertTrue(changed)
            self.assertEqual(text, original.replace(f"FilePath={home}\n", f"FilePath={home}/Videos/Records\n")
                             .replace("RecFormat2=mkv\n", f"RecFormat2=mkv\nFFFilePath={home}/Videos/Records\n"))
            changed, unchanged, _ = self.recording_profile(Path(directory), None)
            self.assertFalse(changed)
            self.assertEqual(unchanged, text)

    def test_records_follow_the_localized_videos_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory)
            with patch.object(obs, "user_config", side_effect=lambda relative: config / relative), \
                    patch.object(obs.Path, "home", return_value=Path("/home/ana")):
                self.assertEqual(obs.records_folder(), Path("/home/ana/Videos/Records"))
                (config / "user-dirs.dirs").write_text('XDG_DESKTOP_DIR="$HOME/Área de trabalho"\nXDG_VIDEOS_DIR="$HOME/Vídeos"\n')
                self.assertEqual(obs.records_folder(), Path("/home/ana/Vídeos/Records"))

    def test_new_installs_set_the_recording_folder(self):
        install = (Path(__file__).parents[3] / "distro/install.sh").read_text()
        self.assertIn('obs-control.py" default-folder', install)

    def test_capture_options_persist_without_launching_obs(self):
        options = {key: {"enabled": False, "available": True, "sources": []} for key in ("audio", "mic", "webcam")}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(obs, "OPTIONS_FILE", Path(directory) / "options.json"), \
                patch.object(obs, "capture_options", return_value=options), patch.object(obs.subprocess, "Popen") as launch:
            obs.save_capture_option("mic", "true")
            self.assertIn('"mic": true', obs.OPTIONS_FILE.read_text())
            launch.assert_not_called()

    def test_missing_camera_cannot_be_enabled(self):
        with patch.object(obs, "capture_options", return_value={"webcam": {"available": False}}):
            with self.assertRaisesRegex(RuntimeError, "Configure"):
                obs.save_capture_option("webcam", "true")

    def test_audio_choices_apply_to_obs_not_system_volume(self):
        options = {"audio": {"enabled": False, "sources": ["Desktop Audio"]},
                   "mic": {"enabled": True, "sources": ["Mic/Aux"]}, "webcam": {"sources": []}}
        scene = {"current_scene": "Scene", "sources": [
            {"name": "Screen", "id": "pipewire-screen-capture-source"},
            {"name": "Scene", "settings": {"items": [{"name": "Screen", "visible": True}]}}]}
        with patch.object(obs, "capture_options", return_value=options), patch.object(obs, "scene_collection", return_value=scene), \
                patch.object(obs.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            obs.apply_capture_options(["obs-cmd"])
            self.assertEqual(run.call_args_list[0].args[0], ["obs-cmd", "audio", "mute", "Desktop Audio"])
            self.assertEqual(run.call_args_list[1].args[0], ["obs-cmd", "audio", "unmute", "Mic/Aux"])

    def test_audio_and_mic_choices_are_independent(self):
        scene = {"current_scene": "Scene", "sources": [
            {"name": "Screen", "id": "pipewire-screen-capture-source"},
            {"name": "Scene", "settings": {"items": [{"name": "Screen"}]}}]}
        for audio in (False, True):
            for mic in (False, True):
                with self.subTest(audio=audio, mic=mic):
                    options = {"audio": {"enabled": audio, "sources": ["Desktop Audio"]},
                               "mic": {"enabled": mic, "sources": ["Mic/Aux"]},
                               "webcam": {"sources": []}}
                    with patch.object(obs, "capture_options", return_value=options), \
                            patch.object(obs, "scene_collection", return_value=scene), \
                            patch.object(obs.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
                        obs.apply_capture_options(["obs-cmd"])
                        self.assertEqual([call.args[0] for call in run.call_args_list], [
                            ["obs-cmd", "audio", "unmute" if audio else "mute", "Desktop Audio"],
                            ["obs-cmd", "audio", "unmute" if mic else "mute", "Mic/Aux"]])

    def test_window_only_scene_is_not_recorded(self):
        scene = {"current_scene": "Scene", "sources": [
            {"name": "Window", "id": "pipewire-window-capture-source"},
            {"name": "Scene", "settings": {"items": [{"name": "Window", "visible": True}]}}]}
        with patch.object(obs, "scene_collection", return_value=scene), patch.object(obs.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "full-screen"):
                obs.apply_capture_options(["obs-cmd"])
            run.assert_not_called()

    def test_camera_uses_scene_name_without_cli_preamble(self):
        options = {"audio": {"sources": []}, "mic": {"sources": []},
                   "webcam": {"enabled": True, "sources": ["Camera"]}}
        scene = {"current_scene": "Scene", "sources": [
            {"name": "Screen", "id": "pipewire-screen-capture-source"},
            {"name": "Scene", "settings": {"items": [{"name": "Screen"}]}}]}
        with patch.object(obs, "capture_options", return_value=options), \
                patch.object(obs, "scene_collection", return_value=scene), \
                patch.object(obs.subprocess, "run", side_effect=[
                    SimpleNamespace(returncode=0, stdout="Executing: Get current scene\nCurrent scene: Scene\n"),
                    SimpleNamespace(returncode=0)]) as run:
            obs.apply_capture_options(["obs-cmd"])
            self.assertEqual(run.call_args.args[0], ["obs-cmd", "scene-item", "enable", "Scene", "Camera"])

    def test_idle_obs_exits_after_successful_stop(self):
        with patch.object(obs, "status", return_value={"ready": True, "running": True, "recording": False, "streaming": False}), \
                patch.object(obs.subprocess, "run", side_effect=[SimpleNamespace(returncode=0, stdout="42\n"), SimpleNamespace(returncode=0, stdout="[]")]), \
                patch.object(obs.os, "kill") as stop:
            self.assertTrue(obs.close_if_idle())
            stop.assert_called_once_with(42, obs.signal.SIGTERM)

    def test_active_or_unknown_obs_is_not_closed(self):
        for changes in ({"streaming": True}, {"recording": True}, {"ready": False}):
            state = {"ready": True, "running": True, "recording": False, "streaming": False, **changes}
            with patch.object(obs, "status", return_value=state), patch.object(obs.os, "kill") as stop, patch.object(obs.time, "sleep"):
                self.assertFalse(obs.close_if_idle())
                stop.assert_not_called()

    def test_idle_window_closes_through_hyprland(self):
        state = {"ready": True, "running": True, "recording": False, "streaming": False}
        with patch.object(obs, "status", return_value=state), \
                patch.object(obs.subprocess, "run", side_effect=[
                    SimpleNamespace(returncode=0, stdout="42\n"),
                    SimpleNamespace(returncode=0, stdout='[{"pid":42,"class":"com.obsproject.Studio","address":"0x123"}]'),
                    SimpleNamespace(returncode=0)]) as run, patch.object(obs.os, "kill") as stop:
            self.assertTrue(obs.close_if_idle())
            self.assertIn("hl.dsp.window.close", run.call_args.args[0][-1])
            self.assertIn("address:0x123", run.call_args.args[0][-1])
            stop.assert_not_called()

    def test_multiple_obs_instances_are_not_closed(self):
        with patch.object(obs, "status", return_value={"ready": True, "running": True, "recording": False, "streaming": False}), \
                patch.object(obs.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="42\n43\n")), \
                patch.object(obs.os, "kill") as stop:
            self.assertFalse(obs.close_if_idle())
            stop.assert_not_called()

    def test_stop_waits_for_success_before_exiting(self):
        with patch.object(obs.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
                patch.object(obs, "websocket_command", return_value=["obs-cmd"]), \
                patch.object(obs, "announce_saved") as announce, \
                patch.object(obs, "close_if_idle") as close:
            obs.control("stop")
            close.assert_called_once()
            announce.assert_called_once()

    def test_obs_timecodes_parse_in_both_forms(self):
        self.assertEqual(obs.parse_duration("1h2m3s500ms"), 3723.5)
        self.assertEqual(obs.parse_duration("45s"), 45)
        self.assertEqual(obs.parse_duration("00:01:30.250"), 90.25)
        with self.assertRaises(ValueError):
            obs.parse_duration("soon")

    def test_details_read_times_size_scene_and_microphone(self):
        outputs = {
            ("recording", "status"): "Recording Status:\n  Active: true\n  Paused: false\n  Timecode: 1m5s\n  Bytes: 2048\n",
            ("streaming", "status"): "Streaming Status:\n  Active: true\n  Duration: 4000ms\n",
            ("scene", "list"): "Available scenes:\n  - Desk\n  - Screen: Main\n",
            ("scene", "current"): "Current scene: Screen: Main\n",
            ("audio", "status"): "Audio device 'Mic' is: unmuted\n",
        }

        def run(command, **options):
            return SimpleNamespace(returncode=0, stdout=outputs[tuple(command[1:3])])

        options = {"mic": {"sources": ["Mic"], "available": True, "enabled": True},
                   "webcam": {"sources": [], "available": False, "enabled": False}}
        state = {"running": True, "ready": True, "recording": True, "paused": False, "streaming": True}
        with patch.object(obs, "status", return_value=dict(state)), patch.object(obs, "capture_options", return_value=options), \
                patch.object(obs, "websocket_command", return_value=["obs-cmd"]), patch.object(obs.subprocess, "run", side_effect=run):
            details = obs.details()
        self.assertEqual((details["recordingSeconds"], details["recordingBytes"], details["streamingSeconds"]), (65, 2048, 4))
        self.assertEqual((details["scenes"], details["scene"]), (["Desk", "Screen: Main"], "Screen: Main"))
        self.assertEqual(details["mic"], {"available": True, "muted": False})
        self.assertNotIn("detailsError", details)

    def test_live_actions_reach_obs(self):
        calls = []

        def run(command, **options):
            calls.append(command[1:])
            return SimpleNamespace(returncode=0, stdout={"current": "Current scene: Desk\n",
                                                        "list": "Available scenes:\n  - Desk\n  - Game\n"}.get(command[2], ""))

        options = {"mic": {"sources": ["Mic"]}, "webcam": {"sources": ["Cam"]}}
        with patch.object(obs, "capture_options", return_value=options), patch.object(obs, "save_capture_option") as save, \
                patch.object(obs.subprocess, "run", side_effect=run):
            obs.live_control(["obs-cmd"], "mic-mute", None)
            obs.live_control(["obs-cmd"], "camera-off", None)
            obs.live_control(["obs-cmd"], "scene", "Game")
            with self.assertRaisesRegex(RuntimeError, "no longer exists"):
                obs.live_control(["obs-cmd"], "scene", "Gone")
        self.assertIn(["audio", "mute", "Mic"], calls)
        self.assertIn(["scene-item", "disable", "Desk", "Cam"], calls)
        self.assertIn(["scene", "switch", "Game"], calls)
        save.assert_called_once_with("webcam", "false")

    def test_saved_recording_offers_folder_and_path(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "2026-10-18 10-30-00.mkv"
            video.write_bytes(b"video")
            with patch.object(obs, "record_directory", return_value=Path(directory)), \
                    patch.object(obs.subprocess, "Popen") as launch:
                obs.announce_saved(["obs-cmd"], video.stat().st_mtime)
            self.assertEqual(launch.call_args.args[0][-2:], ["notify-saved", str(video)])
            with patch.object(obs.subprocess, "run", return_value=SimpleNamespace(stdout="copy\n")) as run:
                obs.notify_saved(str(video))
            self.assertEqual(run.call_args_list[-1].args[0], ["wl-copy", "--", str(video)])

    def test_saved_screenshot_actions_open_image_and_folder(self):
        for action, destination in (("open", "/images/test.png"), ("folder", "/images")):
            with self.subTest(action=action), \
                    patch.object(obs.subprocess, "run", return_value=SimpleNamespace(stdout=action)) as run, \
                    patch.object(obs.subprocess, "Popen") as launch:
                obs.notify_saved("/images/test.png", screenshot=True)
                self.assertIn("--action=open=Open image", run.call_args.args[0])
                self.assertIn("--action=folder=Open folder", run.call_args.args[0])
                self.assertEqual(launch.call_args.args[0], ["xdg-open", destination])

    def test_failed_stop_does_not_exit(self):
        with patch.object(obs.subprocess, "run", side_effect=[SimpleNamespace(returncode=0), SimpleNamespace(returncode=1)]), \
                patch.object(obs, "websocket_command", return_value=["obs-cmd"]), \
                patch.object(obs, "close_if_idle") as close:
            with self.assertRaises(RuntimeError):
                obs.control("stop")
            close.assert_not_called()

    def test_background_launch_uses_lua_workspace_rule(self):
        with patch.object(obs.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            obs.launch_background()
            self.assertEqual(run.call_args.args[0][:2], ["hyprctl", "eval"])
            self.assertIn("special:obs-background silent", run.call_args.args[0][2])
            self.assertIn("obs --minimize-to-tray", run.call_args.args[0][2])

    def test_open_restores_background_obs_to_current_workspace(self):
        clients = '[{"class":"com.obsproject.Studio","address":"0x123","workspace":{"name":"special:obs-background"}}]'
        with patch.object(obs.subprocess, "run", side_effect=[
                SimpleNamespace(returncode=0, stdout=clients),
                SimpleNamespace(returncode=0, stdout='{"id":3}'),
                SimpleNamespace(returncode=0), SimpleNamespace(returncode=0)]) as run:
            obs.reveal_window()
            self.assertIn("workspace = 3", run.call_args_list[2].args[0][-1])
            self.assertIn("address:0x123", run.call_args_list[2].args[0][-1])
            self.assertIn("hl.dsp.focus", run.call_args.args[0][-1])

    def test_recording_states(self):
        self.assertEqual(obs.parse_status("Recording Status:\n Active: false"), {"active": False, "paused": False})
        self.assertEqual(obs.parse_status("Recording Status:\n Active: true\n Paused: true"), {"active": True, "paused": True})
        self.assertEqual(obs.parse_status("Recording Status:\n Active: true\n Paused: false"), {"active": True, "paused": False})
        with self.assertRaises(RuntimeError):
            obs.parse_status("Connection failed")

    def test_status_without_obs_does_not_launch_it(self):
        with patch.object(obs.subprocess, "run", return_value=SimpleNamespace(returncode=1)), \
                patch.object(obs.subprocess, "Popen") as launch:
            state = obs.status()
            self.assertTrue(state["ready"])
            self.assertFalse(state["recording"])
            self.assertFalse(state["streaming"])
            launch.assert_not_called()

    def test_status_reads_recording_pause_and_streaming(self):
        with patch.object(obs.subprocess, "run", side_effect=[
                SimpleNamespace(returncode=0),
                SimpleNamespace(returncode=0, stdout="Active: true\nPaused: true"),
                SimpleNamespace(returncode=0, stdout="Active: true")]), \
                patch.object(obs, "websocket_command", return_value=["obs-cmd"]):
            state = obs.status()
            self.assertTrue(state["ready"])
            self.assertTrue(state["recording"])
            self.assertTrue(state["paused"])
            self.assertTrue(state["streaming"])

    def test_failed_status_disables_controls(self):
        with patch.object(obs.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
                patch.object(obs, "websocket_command", side_effect=RuntimeError("Close OBS once so Eitr can turn on its WebSocket, then try again")):
            state = obs.status()
            self.assertFalse(state["ready"])
            self.assertIn("WebSocket", state["error"])

    def test_folder_opens_records_without_launching_obs(self):
        with patch.object(Path, "mkdir") as mkdir, patch.object(obs.subprocess, "Popen") as launch:
            obs.control("folder")
            mkdir.assert_called_once_with(parents=True, exist_ok=True)
            self.assertEqual(launch.call_args.args[0], ["xdg-open", str(Path.home() / "Videos/Records")])

    def test_start_launches_minimized_and_waits_before_recording(self):
        with patch.object(obs.subprocess, "run", side_effect=[SimpleNamespace(returncode=1), SimpleNamespace(returncode=0), SimpleNamespace(returncode=0)]) as run, \
                patch.object(obs, "launch_background") as launch, patch.object(obs, "default_recording_folder"), \
                patch.object(Path, "read_text", return_value='{"server_enabled":true,"auth_required":false}'):
            self.assertEqual(obs.control("record"), "Command applied")
            launch.assert_called_once_with()
            self.assertEqual(run.call_args_list[-1].args[0][-2:], ["recording", "start"])

    def test_stop_does_not_launch_obs(self):
        with patch.object(obs.subprocess, "run", return_value=SimpleNamespace(returncode=1)), \
                patch.object(obs.subprocess, "Popen") as launch:
            with self.assertRaisesRegex(RuntimeError, "not running"):
                obs.control("stop")
            launch.assert_not_called()

    def websocket_file(self, directory, content=None):
        path = Path(directory) / "obs-studio/plugin_config/obs-websocket/config.json"
        if content is not None:
            path.parent.mkdir(parents=True)
            path.write_text(content)
        return path

    def test_websocket_is_turned_on_while_obs_is_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.websocket_file(directory, '{"server_enabled": false, "auth_required": true, '
                                                  '"server_password": "kept", "server_port": 4460}')
            with patch.object(obs, "user_config", side_effect=lambda relative: Path(directory) / relative), \
                    patch.object(obs, "obs_running", return_value=False):
                obs.websocket_command()
            config = json.loads(path.read_text())
            self.assertEqual((config["server_enabled"], config["auth_required"], config["server_password"],
                              config["server_port"]), (True, True, "kept", 4460))
            self.assertEqual(path.stat().st_mode & 0o777, 0o600, "the file holds the password")

    def test_missing_websocket_settings_get_a_new_password(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.websocket_file(directory)
            with patch.object(obs, "user_config", side_effect=lambda relative: Path(directory) / relative), \
                    patch.object(obs, "obs_running", return_value=False):
                obs.websocket_command()
            config = json.loads(path.read_text())
            self.assertTrue(config["server_enabled"] and config["auth_required"])
            self.assertGreaterEqual(len(config["server_password"]), 24)

    def test_websocket_is_not_changed_while_obs_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            original = '{"server_enabled": false}'
            path = self.websocket_file(directory, original)
            with patch.object(obs, "user_config", side_effect=lambda relative: Path(directory) / relative), \
                    patch.object(obs, "obs_running", return_value=True), \
                    self.assertRaisesRegex(RuntimeError, "Close OBS once"):
                obs.websocket_command()
            self.assertEqual(path.read_text(), original, "OBS would overwrite the change when it exits")

    def test_websocket_password_is_not_passed_in_argv(self):
        config = '{"server_enabled":true,"auth_required":true,"server_password":"p@ss/word","server_port":4460}'
        with patch.dict(obs.os.environ, {}, clear=False), patch.object(Path, "read_text", return_value=config):
            command = obs.websocket_command()
            self.assertEqual(command, ["obs-cmd"])
            self.assertNotIn("p@ss", " ".join(command))
            self.assertEqual(obs.os.environ[obs.WEBSOCKET_ENV], "obsws://localhost:4460/p%40ss%2Fword")

    def test_status_commands_carry_no_secret(self):
        config = '{"server_enabled":true,"auth_required":true,"server_password":"hunter2"}'
        output = SimpleNamespace(returncode=0, stdout="Active: false\n")
        with patch.dict(obs.os.environ, {}, clear=False), patch.object(Path, "read_text", return_value=config), \
                patch.object(obs.subprocess, "run", return_value=output) as run:
            obs.status()
            commands = [call.args[0] for call in run.call_args_list]
            self.assertIn(["obs-cmd", "recording", "status"], commands)
            self.assertFalse(any("hunter2" in part for command in commands for part in command))

    def test_invalid_action_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "Unknown"):
            obs.control("quit")


class DefaultCollectionTests(unittest.TestCase):
    def test_seed_and_preserve_existing_collection(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(obs, "user_config", side_effect=lambda relative: Path(directory) / relative), \
                patch.object(obs, "obs_running", return_value=False), \
                patch.object(obs, "first_capture_device", return_value="/dev/video2"), \
                patch.object(obs, "OPTIONS_FILE", Path(directory) / "options.json"):
            self.assertTrue(obs.default_scene_collection())
            collection = obs.scene_collection()
            sources = collection["sources"]
            camera = next(source for source in sources if source["id"] == "v4l2_input")
            self.assertEqual(camera["settings"]["device_id"], "/dev/video2")
            scene = sources[-1]
            self.assertEqual(collection["current_program_scene"], scene["name"])
            for item, source in zip(scene["settings"]["items"], sources):
                self.assertEqual(item["source_uuid"], source["uuid"])
            self.assertFalse(scene["settings"]["items"][1]["visible"])
            self.assertEqual(sources[0]["settings"], {})
            identifiers = [source["uuid"] for source in sources]
            identifiers += [collection[key]["uuid"] for key in ("DesktopAudioDevice1", "AuxAudioDevice1")]
            identifiers += [item["uuid"] for item in scene["settings"]["items"]]
            self.assertEqual(len(identifiers), len(set(identifiers)))
            for key in ("DesktopAudioDevice1", "AuxAudioDevice1"):
                self.assertEqual(collection[key]["settings"], {"device_id": "default"})
            self.assertTrue(obs.capture_options()["mic"]["available"])
            self.assertTrue(obs.capture_options()["webcam"]["available"])
            files = {path: path.read_bytes() for path in Path(directory).rglob("*") if path.is_file()}
            self.assertFalse(obs.default_scene_collection())
            self.assertEqual(files, {path: path.read_bytes() for path in files})

    def test_running_obs_and_other_collections_are_untouched(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(obs, "user_config", side_effect=lambda relative: Path(directory) / relative), \
                patch.object(obs, "obs_running", return_value=True):
            self.assertFalse(obs.default_scene_collection())
            self.assertEqual(list(Path(directory).iterdir()), [])
            scenes = Path(directory) / "obs-studio/basic/scenes"
            scenes.mkdir(parents=True)
            existing = scenes / "Personal.json"
            existing.write_bytes(b"user collection")
            with patch.object(obs, "obs_running", return_value=False):
                self.assertFalse(obs.default_scene_collection())
            self.assertEqual(existing.read_bytes(), b"user collection")
            self.assertEqual(list(scenes.iterdir()), [existing])

    def test_missing_camera_and_explicit_collection_settings(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(obs, "user_config", side_effect=lambda relative: Path(directory) / relative), \
                patch.object(obs, "obs_running", return_value=False), \
                patch.object(obs, "first_capture_device", return_value=None):
            settings = Path(directory) / "obs-studio/user.ini"
            settings.parent.mkdir()
            original = "[Basic]\nSceneCollection=Personal\nSceneCollectionFile=Personal\n[Other]\nKey=value\n"
            settings.write_text(original)
            self.assertTrue(obs.default_scene_collection())
            self.assertEqual(settings.read_text(), original)
            collection = json.loads((settings.parent / "basic/scenes/Untitled.json").read_text())
            self.assertEqual(collection["sources"][1]["settings"], {})

    def test_camera_detection_skips_metadata_devices(self):
        import fcntl
        import struct
        with tempfile.TemporaryDirectory() as directory:
            metadata = Path(directory) / 'video1'
            camera = Path(directory) / 'video2'
            metadata.touch()
            camera.touch()
            def capabilities(descriptor, request, buffer):
                self.assertEqual(request, 0x80685600)
                flags = 0x00800000 if capabilities.calls == 0 else 0x80000000
                struct.pack_into('II', buffer, 84, flags, 1)
                capabilities.calls += 1
            capabilities.calls = 0
            with patch.object(Path, 'glob', return_value=[metadata, camera]), patch.object(fcntl, 'ioctl', side_effect=capabilities):
                self.assertEqual(obs.first_capture_device(), str(camera))
