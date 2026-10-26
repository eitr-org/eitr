import importlib.util
import json
import os
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

BAR = Path(__file__).resolve().parents[1]
REPO = BAR.parents[1]
spec = importlib.util.spec_from_file_location("display_settings", BAR / "scripts/display-settings.py")
display = importlib.util.module_from_spec(spec)
spec.loader.exec_module(display)

MONITORS = [
    {"name": "DP-3", "description": "LG 34GL750", "width": 2560, "height": 1080, "refreshRate": 144.0, "x": 0, "y": 0,
     "scale": 1.0, "transform": 0, "mirrorOf": "none", "availableModes": ["2560x1080@144.00Hz", "1920x1080@60.00Hz"]},
    {"name": "HDMI-A-1", "description": "Laptop panel", "width": 1920, "height": 1080, "refreshRate": 60.0,
     "x": 2560, "y": 0, "scale": 1.5, "transform": 0, "mirrorOf": "none", "availableModes": ["1920x1080@60.00Hz"]},
]


class DisplaySettingsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.base / "config"),
                                          "XDG_RUNTIME_DIR": str(self.base), "EITR_CODE_ROOT": str(REPO)})
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(display, "DRM_ROOT", self.base / "drm")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.commands = []

        def run(command, **kwargs):
            self.commands.append(command)
            stdout = json.dumps(MONITORS) if command[:3] == ["hyprctl", "monitors", "all"] else ""
            return display.subprocess.CompletedProcess(command, 0, stdout, "")
        patcher = patch.object(display.subprocess, "run", side_effect=run)
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def edid(eotf=4):
        base = bytearray(128)
        base[:8] = bytes.fromhex("00ffffffffffff00")
        base[8:18] = bytes.fromhex("16920001000000000122")
        base[18:25] = bytes([1, 4, 0xa5, 60, 34, 120, 2])
        base[38:54] = bytes([1, 1]) * 8
        base[54:72] = b"\x00\x00\x00\xfc\x00Eitr HDR test"
        base[126] = 1
        base[127] = -sum(base) % 256
        cta = bytearray(128)
        cta[:8] = bytes([2, 3, 8, 0, 0xe3, 6, eotf, 1])
        cta[127] = -sum(cta) % 256
        return bytes(base + cta)

    def hdr_connector(self, eotf=4, status="connected"):
        connector = self.base / "drm/card1-DP-3"
        connector.mkdir(parents=True, exist_ok=True)
        (connector / "edid").write_bytes(self.edid(eotf))
        (connector / "status").write_text(status)
        return connector

    def test_edid_hdr_eotfs_and_invalid_blocks(self):
        for eotf in (4, 8, 12):
            self.assertTrue(display.edid_hdr(self.edid(eotf)))
        self.assertFalse(display.edid_hdr(self.edid(1)))
        for invalid in (b"", self.edid()[:200], b"invalid" * 40, self.edid()[:-1] + b"x"):
            self.assertFalse(display.edid_hdr(invalid))
        malformed = bytearray(self.edid())
        malformed[132] = 0xff
        malformed[255] = -sum(malformed[128:255]) % 256
        self.assertFalse(display.edid_hdr(malformed))
        self.hdr_connector()
        self.assertTrue(display.hdr_capable("DP-3"))
        self.assertFalse(display.hdr_capable("DP-1"))

    def test_hdr_toggle_trials_keep_revert_and_brightness(self):
        self.hdr_connector()
        self.assertTrue(display.set_setting("DP-3", "hdr", "on")["trial"])
        self.assertIn('cm = "hdr", bitdepth = 10, sdrbrightness = 1', self.evaluated()[-1])
        self.assertTrue(display.revert())
        self.assertNotIn('cm =', self.evaluated()[-1])
        display.set_setting("DP-3", "hdr", "on")
        display.keep()
        self.assertTrue(display.saved()["DP-3"]["hdr"])
        hdr_live = [dict(MONITORS[0], colorManagementPreset="hdr", sdrBrightness=1.4), MONITORS[1]]
        with patch.object(display, "monitors", return_value=hdr_live):
            self.assertNotIn("trial", display.set_setting("DP-3", "sdr_brightness", "1.6"))
            self.assertIn('sdrbrightness = 1.6', self.evaluated()[-1])
            self.assertEqual(display.saved()["DP-3"]["sdr_brightness"], 1.6)
            self.assertTrue(display.set_setting("DP-3", "hdr", "off")["trial"])
            display.revert()
            self.assertIn('sdrbrightness = 1.4', self.evaluated()[-1])
            display.set_setting("DP-3", "hdr", "off")
            display.keep()
            self.assertFalse(display.saved()["DP-3"]["hdr"])

    def test_sdr_brightness_is_remembered_while_desktop_hdr_is_off(self):
        display.save({"DP-3": dict(display.current(MONITORS[0]), hdr=False, sdr_brightness=1.7)})
        self.assertEqual(display.current(MONITORS[0])["sdr_brightness"], 1.7)
        live = dict(MONITORS[0], colorManagementPreset="HDR", sdrBrightness=1.2)
        self.assertTrue(display.current(live)["hdr"])
        self.assertEqual(display.current(live)["sdr_brightness"], 1.2)
        self.assertNotIn("sdrbrightness", display.lua_call("DP-3", display.current(MONITORS[0])))

    def test_hdr_invalid_values_and_unsupported_monitor(self):
        for key, value in (("hdr", "on"), ("hdr", "yes"), ("sdr_brightness", "nan"),
                           ("sdr_brightness", "inf"), ("sdr_brightness", "0.9"), ("sdr_brightness", "2.1")):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                display.set_setting("DP-3", key, value)
        self.assertEqual(self.evaluated(), [])

    def test_generated_game_defaults_follow_connected_edid_and_list_reports_state(self):
        display.save({})
        generated = display.config_dir() / "displays.lua"
        self.assertNotIn('hl.env', generated.read_text())
        connector = self.hdr_connector()
        output = []
        with patch("builtins.print", side_effect=output.append):
            display.main(["list"])
        monitor = json.loads(output[0])["monitors"][0]
        self.assertTrue(monitor["hdr_capable"])
        self.assertFalse(monitor["hdr"])
        self.assertEqual(monitor["sdr_brightness"], 1)
        for variable in display.HDR_ENV:
            self.assertIn(f'hl.env("{variable}", "1", true)', generated.read_text())
        self.assertEqual(self.evaluated(), [], "listing never changes live monitors")
        (connector / "status").write_text("disconnected")
        display.main(["refresh-hdr"])
        self.assertNotIn('hl.env', generated.read_text())
        self.assertEqual(json.loads((display.config_dir() / "displays.json").read_text()), {})
        self.hdr_connector(eotf=1)
        display.save({})
        self.assertNotIn('hl.env', generated.read_text())

    def evaluated(self):
        return [command[2] for command in self.commands if command[:2] == ["hyprctl", "eval"]]

    def test_positions_beside_another_display_use_logical_sizes(self):
        main, side = (2560, 1080), (1280, 720)
        anchor = display.parse_anchor
        self.assertEqual(display.beside(anchor("left-of:DP-3"), side, (0, 0), main), (-1280, 0))
        self.assertEqual(display.beside(anchor("right-of:DP-3"), side, (0, 0), main), (2560, 0))
        self.assertEqual(display.beside(anchor("below:DP-3"), side, (0, 0), main), (0, 1080))
        self.assertEqual(display.beside(anchor("above:DP-3:center"), side, (0, 0), main), (640, -720))
        self.assertEqual(display.beside(anchor("right-of:DP-3:center"), side, (0, 0), main), (2560, 180))
        self.assertEqual(display.beside(anchor("left-of:DP-3:end"), side, (0, 0), main), (-1280, 360))
        self.assertIsNone(anchor("100x200"))
        for bad in ("beside:DP-3", "left-of:", "left-of:DP-3:diagonal"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                anchor(bad)

    def test_three_displays_arrange_in_a_chain_and_follow_their_target(self):
        live = [dict(monitor) for monitor in MONITORS] + [dict(MONITORS[1], name="DP-4", x=5000)]
        settings = {monitor["name"]: display.current(monitor) for monitor in live}
        anchors = {"HDMI-A-1": display.parse_anchor("right-of:DP-3:center"),
                   "DP-4": display.parse_anchor("right-of:HDMI-A-1")}
        display.arrange(settings, anchors, live)
        self.assertEqual(settings["HDMI-A-1"]["position"], "2560x180")
        self.assertEqual(settings["DP-4"]["position"], "3840x180")
        settings["DP-3"]["scale"] = "2"
        display.arrange(settings, anchors, live)
        self.assertEqual(settings["HDMI-A-1"]["position"], "1280x-90", "a scaled target moves what sits beside it")
        self.assertEqual(settings["DP-4"]["position"], "2560x-90")

    def test_overlapping_displays_are_refused(self):
        live = [dict(monitor) for monitor in MONITORS] + [dict(MONITORS[1], name="DP-4", x=5000)]
        settings = {monitor["name"]: display.current(monitor) for monitor in live}
        anchors = {"HDMI-A-1": display.parse_anchor("right-of:DP-3"), "DP-4": display.parse_anchor("right-of:DP-3")}
        with self.assertRaisesRegex(ValueError, "would overlap"):
            display.arrange(settings, anchors, live)
        settings["DP-4"]["mirror"] = "DP-3"
        display.arrange(settings, anchors, live)

    def test_placing_a_display_beside_its_own_dependant_keeps_that_one_in_place(self):
        (self.base / "config/hypr").mkdir(parents=True)
        (self.base / "config/hypr/primary-display").write_text("HDMI-A-1\n")
        (self.base / "config/hypr/displays.json").write_text(json.dumps(
            {"HDMI-A-1": {**display.current(MONITORS[1]), "anchor": display.parse_anchor("right-of:DP-3")}}))
        self.assertEqual(display.set_setting("DP-3", "position", "left-of:HDMI-A-1")["position"], "0x0")
        saved = json.loads((self.base / "config/hypr/displays.json").read_text())
        self.assertIn("anchor", saved["DP-3"])
        self.assertNotIn("anchor", saved["HDMI-A-1"], "HDMI-A-1 no longer follows DP-3")
        self.assertEqual(saved["HDMI-A-1"]["position"], "2560x0", "HDMI-A-1 stayed where it was")

    def test_the_main_display_stays_put_and_the_others_go_around_it(self):
        (self.base / "config/hypr").mkdir(parents=True)
        (self.base / "config/hypr/displays.json").write_text(json.dumps(
            {"DP-3": {**display.current(MONITORS[0]), "anchor": display.parse_anchor("right-of:HDMI-A-1")}}))
        with self.assertRaisesRegex(ValueError, "main display stays"):
            display.set_setting("DP-3", "position", "left-of:HDMI-A-1")
        listed = []
        with patch("builtins.print", side_effect=listed.append):
            display.main(["list"])
        result = json.loads(listed[0])
        self.assertEqual(result["main"], "DP-3", "the largest display is main until one is chosen")
        self.assertIsNone(next(item for item in result["monitors"] if item["name"] == "DP-3")["anchor"],
                          "a main display's old arrangement is ignored")
        (self.base / "config/hypr/primary-display").write_text("HDMI-A-1\n")
        display.set_setting("DP-3", "position", "left-of:HDMI-A-1")
        self.assertEqual(json.loads((self.base / "config/hypr/displays.json").read_text())["DP-3"]["anchor"],
                         {"side": "left-of", "of": "HDMI-A-1", "align": "start"})

    def test_every_display_gets_an_explicit_position_so_none_drifts(self):
        # A display still on Hyprland's automatic position moves whenever another one
        # changes; pinning all of them (unchanged ones first) keeps the target in place.
        display.set_setting("HDMI-A-1", "position", "below:DP-3:center")
        evaluated = self.evaluated()
        self.assertEqual(len(evaluated), 2)
        self.assertIn('output = "DP-3"', evaluated[0])
        self.assertIn('output = "HDMI-A-1", mode = "1920x1080@60.00", position = "640x1080"', evaluated[1])

    def test_moving_several_displays_never_overlaps_on_the_way(self):
        # Hyprland warns about an overlapping layout after any single rule, so each
        # intermediate state must be valid too, e.g. from "left of" to "below".
        sizes = {"DP-3": (2560, 1080), "HDMI-A-1": (1920, 1080)}
        previous = {"DP-3": {"mode": "2560x1080@144", "scale": "1", "position": "1920x0", "mirror": None},
                    "HDMI-A-1": {"mode": "1920x1080@144", "scale": "1", "position": "0x0", "mirror": None}}
        target = {"DP-3": dict(previous["DP-3"], position="0x0"),
                  "HDMI-A-1": dict(previous["HDMI-A-1"], position="320x1080")}
        display.apply_all(target, previous)
        placed = {name: display.pixels(values["position"]) for name, values in previous.items()}
        for call in self.evaluated():
            name = re.search(r'output = "([^"]+)"', call).group(1)
            placed[name] = display.pixels(re.search(r'position = "([^"]+)"', call).group(1))
            (ax, ay), (bx, by) = placed["DP-3"], placed["HDMI-A-1"]
            (aw, ah), (bw, bh) = sizes["DP-3"], sizes["HDMI-A-1"]
            self.assertFalse(ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah, f"overlap after {call}")
        self.assertEqual(placed, {"DP-3": (0, 0), "HDMI-A-1": (320, 1080)})

    def test_layouts_are_shifted_to_start_at_the_origin(self):
        settings = {"DP-3": {"mode": "2560x1080@144", "scale": "1", "position": "4480x0"},
                    "HDMI-A-1": {"mode": "1920x1080@60", "scale": "1", "position": "2560x-200"},
                    "eDP-1": {"mode": "1920x1080@60", "scale": "1", "position": "-9000x0", "mirror": "DP-3"}}
        display.normalize(settings)
        self.assertEqual([values["position"] for values in settings.values()], ["1920x200", "0x0", "-9000x0"])

    def test_an_arrangement_is_saved_at_once_with_its_target(self):
        display.set_setting("HDMI-A-1", "position", "below:DP-3:center")
        self.assertFalse(display.trial_file().exists(), "positions are not tried with a countdown")
        saved = json.loads((self.base / "config/hypr/displays.json").read_text())
        self.assertEqual(saved["HDMI-A-1"]["anchor"], {"side": "below", "of": "DP-3", "align": "center"})
        self.assertEqual(saved["HDMI-A-1"]["position"], "640x1080")
        self.assertIn("DP-3", saved, "the target is saved too, so a reboot restores the same layout")
        self.assertNotIn("anchor", (self.base / "config/hypr/displays.lua").read_text())
        listed = []
        with patch("builtins.print", side_effect=listed.append):
            display.main(["list"])
        anchors = {monitor["name"]: monitor["anchor"] for monitor in json.loads(listed[0])["monitors"]}
        self.assertEqual(anchors, {"DP-3": None, "HDMI-A-1": saved["HDMI-A-1"]["anchor"]})
        display.set_setting("HDMI-A-1", "position", "0x2000")
        self.assertNotIn("anchor", json.loads((self.base / "config/hypr/displays.json").read_text())["HDMI-A-1"])

    def test_hand_editing_seeds_local_lua_once_and_never_overwrites_it(self):
        with patch.object(display.subprocess, "Popen") as start, patch.object(display.shutil, "which", return_value=None):
            display.edit()
            local = self.base / "config/hypr/local.lua"
            self.assertEqual(local.read_text(), (REPO / "hypr/local.lua.template").read_text())
            local.write_text("-- mine\n")
            display.edit()
        self.assertEqual(local.read_text(), "-- mine\n")
        self.assertEqual(start.call_args.args[0][-2:], ["nvim", str(local)])

    def test_the_local_lua_template_only_suggests(self):
        template = (REPO / "hypr/local.lua.template").read_text()
        lines = [line for line in template.splitlines() if line.strip()]
        self.assertTrue(all(line.startswith("--") for line in lines), "seeding the file must change nothing")
        fields = set(re.findall(r"(\w+) = ", "\n".join(line for line in lines if "hl.monitor(" in line)))
        # Field names Hyprland 0.56's hl.monitor accepts (an unknown field is an error).
        self.assertLessEqual(fields, {"output", "mode", "position", "scale", "transform", "mirror", "disabled"})

    def test_a_new_mode_is_live_but_reverts_unless_kept(self):
        # A mode the screen cannot show leaves it black, so the change is tried.
        self.assertTrue(display.set_setting("DP-3", "mode", "1920x1080@60.00")["trial"])
        self.assertIn('hl.monitor({ output = "DP-3", mode = "1920x1080@60.00", position = "0x0", scale = 1 })',
                      self.evaluated())
        timer = next(command for command in self.commands if command[0] == "systemd-run")
        self.assertIn("--on-active=15s", timer)
        self.assertEqual(timer[-1], "revert")
        self.assertFalse((self.base / "config/hypr/displays.json").exists(), "nothing is saved while trying")
        self.assertEqual(sum(command[-1] == "refresh-walker" for command in self.commands), 1)
        evaluated = len(self.evaluated())
        display.revert()
        self.assertEqual(sum(command[-1] == "refresh-walker" for command in self.commands), 2)
        self.assertIn('hl.monitor({ output = "DP-3", mode = "2560x1080@144.00", position = "0x0", scale = 1 })',
                      self.evaluated()[evaluated:])
        self.assertFalse(display.trial_file().exists())
        display.set_setting("DP-3", "mode", "1920x1080@60.00")
        self.assertTrue(display.keep())
        self.assertEqual(json.loads((self.base / "config/hypr/displays.json").read_text())["DP-3"]["mode"], "1920x1080@60.00")

    def test_scale_applies_and_is_saved_at_once(self):
        self.assertNotIn("trial", display.set_setting("DP-3", "scale", "1.25"))
        self.assertEqual(self.commands[-1][-1], "refresh-walker")
        self.assertFalse(any(command[0] == "systemd-run" for command in self.commands))
        self.assertEqual(json.loads((self.base / "config/hypr/displays.json").read_text())["DP-3"]["scale"], "1.25")

    def test_keeping_saves_settings_and_the_lua_loaded_before_local_lua(self):
        display.set_setting("HDMI-A-1", "mirror", "DP-3")
        saved = json.loads((self.base / "config/hypr/displays.json").read_text())
        self.assertEqual(saved["HDMI-A-1"]["mirror"], "DP-3")
        lua = (self.base / "config/hypr/displays.lua").read_text()
        self.assertIn('mirror = "DP-3"', lua)
        self.assertFalse(display.keep(), "a mirror is saved at once; nothing is left to keep")

    def test_bad_values_change_nothing(self):
        for key, value, message in (("mirror", "DP-9", "No other display"), ("scale", "big", "could not convert"),
                                    ("position", "left-of:DP-9", "No other display"), ("position", "left-of:HDMI-A-1", "No other display"),
                                    ("position", "somewhere", "Unknown position"), ("brightness", "1", "Unknown")):
            # DP-3 is the main display, which has no position of its own; HDMI-A-1 does.
            name = "HDMI-A-1" if key == "position" else "DP-3"
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, message):
                display.set_setting(name, key, value)
        self.assertEqual(self.evaluated(), [])

    def test_hand_written_monitors_in_local_lua_still_win(self):
        loader = (REPO / "hypr/local-loader.lua").read_text()
        self.assertLess(loader.index('"/hypr/displays.lua")'), loader.index('"/hypr/local.lua")'))

    def test_the_display_panel_offers_it(self):
        panel = (BAR / "BrightnessMenu.qml").read_text()
        self.assertIn('trialOperation.command = ["python3", settingsHelper, "set", name, key, value]', panel)
        self.assertIn("if (result.trial)", panel, "the countdown appears for settings being tried")
        self.assertIn('menu.finishTrial("keep")', panel)
        self.assertIn('menu.finishTrial("revert")', panel)
        self.assertIn("readonly property int trialLength: 15", panel)
        self.assertEqual(display.REVERT_SECONDS, 15, "the panel's countdown matches the revert timer")
        self.assertIn("DisplaySettingsEditor DisplaySettingsEditor.qml", (BAR / "qmldir").read_text())
        rows = json.loads((REPO / "elephant/menu-rows/system-devices.json").read_text())
        names = [row["text"] for row in rows]
        self.assertNotIn("Display Settings", names, "the Display panel holds them")
        self.assertIn("resolution", next(row for row in rows if row["text"] == "Display")["keywords"])


if __name__ == "__main__":
    unittest.main()
