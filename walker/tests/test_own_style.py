"""The user's own wallpapers, themes and lockscreens (distro/lib/eitr_own_style.py, own.py)."""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from PIL import Image

from home_isolation import setUpModule, tearDownModule  # noqa: F401
from test_theme_schema import COLOR_KEYS, KVANTUM_THEME, REQUIRED

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "distro/lib"))
import eitr_own_style as own_style  # noqa: E402
import eitr_paths  # noqa: E402


def picture(path, color=(30, 90, 160), size=(160, 100), kind="PNG"):
    image = Image.new("RGB", size, color)
    for x in range(size[0] // 2):
        for y in range(size[1]):
            image.putpixel((x, y), (200, 60, 40))
    image.save(path, kind)
    return path


def encoded(**arguments):
    with tempfile.TemporaryDirectory() as directory:
        return picture(Path(directory) / "image", **arguments).read_bytes()


class FakeResponse(io.BytesIO):
    def __init__(self, data, length=None):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data) if length is None else length)}

    def __enter__(self):
        return self

    def __exit__(self, *arguments):
        self.close()


class FakeOpener:
    def __init__(self, data, length=None):
        self.data, self.length, self.requests = data, length, []

    def open(self, request, timeout):
        self.requests.append((request.full_url, timeout))
        return FakeResponse(self.data, self.length)


class SandboxTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        environment = {"HOME": str(self.home), "EITR_CODE_ROOT": str(ROOT), "EITR_LIBRARY_ROOT": str(ROOT / "distro/lib")}
        for name, relative in (("XDG_CONFIG_HOME", ".config"), ("XDG_DATA_HOME", ".local/share"),
                               ("XDG_CACHE_HOME", ".cache"), ("XDG_STATE_HOME", ".local/state")):
            environment[name] = str(self.home / relative)
        patcher = patch.dict(os.environ, environment)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.pictures = self.home / "Pictures"
        self.pictures.mkdir()


class PaletteTests(SandboxTest):
    def test_palette_is_deterministic_complete_and_readable(self):
        source = picture(self.pictures / "dark.png")
        tools = own_style.palette_tools()
        colors, mode = own_style.generate_palette(source)
        self.assertEqual((colors, mode), own_style.generate_palette(source))
        self.assertEqual(set(colors), COLOR_KEYS)
        self.assertEqual(mode, "dark")
        self.assertGreaterEqual(tools.contrast(colors["foreground"], colors["background"]), 7)
        self.assertGreaterEqual(tools.contrast(colors["accent"], colors["background"]), 3)
        for index in (*range(1, 8), *range(9, 16)):
            self.assertGreaterEqual(tools.contrast(colors[f"color{index}"], colors["background"]), 4.5, index)

    def test_bright_pictures_suggest_light_and_either_mode_can_be_forced(self):
        source = picture(self.pictures / "bright.png", color=(240, 236, 220), size=(400, 100))
        tools = own_style.palette_tools()
        self.assertEqual(own_style.suggested_mode(source), "light")
        for mode in ("light", "dark"):
            colors, chosen = own_style.generate_palette(source, mode)
            self.assertEqual(chosen, mode)
            self.assertEqual(tools.luminance(colors["background"]) > tools.luminance(colors["foreground"]), mode == "light")
            self.assertGreaterEqual(tools.contrast(colors["foreground"], colors["background"]), 7)

    def test_grey_pictures_still_get_a_coloured_accent(self):
        colors, _ = own_style.generate_palette(picture(self.pictures / "grey.png", color=(90, 90, 90)))
        self.assertGreater(own_style.to_hls(colors["accent"])[2], 0.1)


class PictureTests(SandboxTest):
    def test_sources_are_local_files_or_https_only(self):
        good = picture(self.pictures / "lake.png")
        self.assertEqual(own_style.check_source(str(good)), str(good))
        self.assertEqual(own_style.check_source("https://example.com/a.jpg"), "https://example.com/a.jpg")
        for bad in ("http://example.com/a.jpg", "ftp://example.com/a.jpg", "file:///etc/passwd",
                    "https://user:secret@example.com/a.jpg", str(self.pictures / "missing.png")):
            with self.subTest(source=bad), self.assertRaises(ValueError):
                own_style.check_source(bad)

    def test_download_checks_size_and_content_without_network(self):
        data = encoded()
        opener = FakeOpener(data)
        stored = own_style.add_wallpaper("https://example.com/photos/Lake%20View.png", opener=opener)
        self.assertEqual(opener.requests, [("https://example.com/photos/Lake%20View.png", own_style.TIMEOUT)])
        self.assertEqual(stored.read_bytes(), data)
        self.assertEqual(stored.parent, eitr_paths.data("eitr/wallpapers"))
        with self.assertRaisesRegex(ValueError, "50 MB"):
            own_style.download("https://example.com/a.png", FakeOpener(data, length=own_style.MAX_BYTES + 1))
        with patch.object(own_style, "MAX_BYTES", 10), self.assertRaisesRegex(ValueError, "50 MB"):
            own_style.download("https://example.com/a.png", FakeOpener(data, length=0))
        with self.assertRaises(ValueError):
            own_style.add_wallpaper("https://example.com/a.png", opener=FakeOpener(b"<html>not a picture</html>"))
        with self.assertRaises(ValueError):
            own_style.download("http://example.com/a.png", opener)
        self.assertEqual(len(own_style.wallpapers()), 1)

    def test_page_links_use_the_page_picture_or_explain_what_to_copy(self):
        data = encoded()
        page = b'<!DOCTYPE html><html><head><meta property="og:image" content="/media/lake.png?size=full&amp;x=1"></head></html>'
        responses = iter([page, data])
        opener = FakeOpener(b"")
        opener.open = lambda request, timeout: (opener.requests.append(request.full_url), FakeResponse(next(responses)))[1]
        stored = own_style.add_wallpaper("https://example.com/posts/42", opener=opener)
        self.assertEqual(opener.requests, ["https://example.com/posts/42", "https://example.com/media/lake.png?size=full&x=1"])
        self.assertEqual(stored.read_bytes(), data)
        with self.assertRaisesRegex(ValueError, "web page.*Copy image address"):
            own_style.add_wallpaper("https://example.com/b", opener=FakeOpener(b"<html><body>no picture</body></html>"))
        plain = b'<html><head><meta property="og:image" content="http://example.com/a.png"></head></html>'
        with self.assertRaisesRegex(ValueError, "web page"):
            own_style.add_wallpaper("https://example.com/c", opener=FakeOpener(plain))

        class Refusing:
            def open(self, request, timeout):
                raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, None)
        with self.assertRaisesRegex(ValueError, "HTTP 403.*Copy image address"):
            own_style.add_wallpaper("https://example.com/d", opener=Refusing())

    def test_redirects_away_from_https_are_refused(self):
        handler = own_style._HttpsOnly()
        with self.assertRaises(ValueError):
            handler.redirect_request(None, None, 302, "Found", {}, "http://example.com/a.png")

    def test_only_whole_jpeg_png_or_webp_pictures_are_kept(self):
        self.assertEqual(own_style.picture_format(encoded(kind="JPEG")), ".jpg")
        self.assertEqual(own_style.picture_format(encoded(kind="WEBP")), ".webp")
        for data in (encoded(kind="GIF"), encoded(size=(32, 32)), encoded()[:200], b"\x89PNG broken"):
            with self.assertRaises(ValueError):
                own_style.picture_format(data)

    def test_wallpapers_get_unique_names_and_only_own_ones_count(self):
        source = picture(self.pictures / "lake.png")
        first, again = own_style.add_wallpaper(str(source)), own_style.add_wallpaper(str(source))
        self.assertEqual(again, first, "the same picture is not stored twice")
        (self.pictures / "other").mkdir()
        other = own_style.add_wallpaper(str(picture(self.pictures / "other" / "lake.png", color=(10, 200, 90))))
        self.assertEqual((first.name, other.name), ("lake.png", "lake-2.png"))
        self.assertEqual(own_style.wallpapers(), [first, other])
        self.assertEqual(own_style.own_wallpaper(first), first)
        with self.assertRaises(ValueError):
            own_style.own_wallpaper(source)


class ThemeTests(SandboxTest):
    def create(self, name="Lake at Dawn", **arguments):
        return own_style.create_theme(name, str(picture(self.pictures / "lake.png")), **arguments)

    def test_created_theme_is_complete_and_listed_beside_shipped_ones(self):
        directory = self.create(previous="norse")
        self.assertEqual(directory, eitr_paths.data("eitr/themes/lake-at-dawn"))
        names = {path.name for path in directory.iterdir()}
        self.assertEqual(REQUIRED - names, set())
        self.assertIn(own_style.MARKER, names)
        self.assertEqual(set(own_style.palette_tools().load(directory)), COLOR_KEYS)
        self.assertRegex((directory / "dolphin.theme").read_text().strip(), KVANTUM_THEME)
        self.assertIn('"aether"', (directory / "neovim.lua").read_text())
        paths = eitr_paths.theme_paths()
        self.assertEqual(paths["lake-at-dawn"], directory)
        self.assertEqual(paths["norse"], ROOT / "themes/norse")
        self.assertEqual(own_style.fallback_theme("lake-at-dawn"), "norse")

    def test_names_of_shipped_or_existing_themes_are_refused(self):
        self.create()
        for name in ("Norse", "Lake at Dawn", "!!!"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.create(name)
        self.assertEqual(list(own_style.own_themes()), ["lake-at-dawn"])
        self.assertEqual([path.name for path in eitr_paths.data("eitr/themes").iterdir()], ["lake-at-dawn"])

    def test_color_changes_rewrite_derived_files_and_keep_text_readable(self):
        directory = self.create(mode="dark")
        colors = own_style.set_theme_color("lake-at-dawn", "accent", "E0559B")
        self.assertEqual((colors["accent"], colors["cursor"]), ("#e0559b", "#e0559b"))
        self.assertEqual((directory / "rgb.color").read_text(), "E0559B\n")
        self.assertIn("#e0559b", (directory / "btop.theme").read_text())
        colors = own_style.set_theme_color("lake-at-dawn", "color2", "#22aa44")
        self.assertNotEqual(colors["color10"], "#22aa44")
        with self.assertRaisesRegex(ValueError, "contrast"):
            own_style.set_theme_color("lake-at-dawn", "foreground", "#111111")
        with self.assertRaises(ValueError):
            own_style.set_theme_color("lake-at-dawn", "accent", "red")
        with self.assertRaises(ValueError):
            own_style.set_theme_color("lake-at-dawn", "selection_background", "#000000")
        colors = own_style.set_theme_color("lake-at-dawn", "background", "#f4f4f4")
        self.assertGreaterEqual(own_style.palette_tools().contrast(colors["foreground"], "#f4f4f4"), 7)
        self.assertTrue((directory / "light.mode").is_file())
        self.assertRegex((directory / "dolphin.theme").read_text().strip(), "latte")


class CommandTests(SandboxTest):
    def setUp(self):
        super().setUp()
        specification = importlib.util.spec_from_file_location("own_cli", ROOT / "walker/scripts/actions/style/own.py")
        self.cli = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(self.cli)
        self.cache = eitr_paths.cache()
        self.cache.mkdir(parents=True)
        self.backgrounds = eitr_paths.config("theme/current/backgrounds")
        self.backgrounds.mkdir(parents=True)
        picture(self.backgrounds / "01-first.png")

    def test_an_added_wallpaper_is_applied_right_away(self):
        with patch.object(self.cli.subprocess, "run") as run, patch.object(self.cli, "notify"):
            self.assertEqual(self.cli.add_wallpaper(str(picture(self.pictures / "lake.png"))), 0)
        self.assertEqual(run.call_args.args[0][-2:], ["apply", str(own_style.wallpapers()[0])])

    def test_deleting_the_current_wallpaper_falls_back_to_the_theme_first(self):
        path = own_style.add_wallpaper(str(picture(self.pictures / "lake.png")))
        (self.cache / "current-wallpaper").write_text(f"{path}\n")
        self.assertEqual(self.cli.delete_wallpaper(str(path), ask_first=lambda *arguments: False), 0)
        self.assertTrue(path.exists())
        with patch.object(self.cli.subprocess, "run") as run:
            self.cli.delete_wallpaper(str(path), ask_first=lambda *arguments: True)
        self.assertFalse(path.exists())
        self.assertEqual(run.call_args.args[0][-2:], ["apply", str(self.backgrounds / "01-first.png")])
        with self.assertRaises(ValueError):
            self.cli.delete_wallpaper(str(self.backgrounds / "01-first.png"), ask_first=lambda *arguments: True)

    def test_deleting_the_current_theme_switches_to_a_shipped_one_first(self):
        directory = own_style.create_theme("Mine", str(picture(self.pictures / "lake.png")), previous="jade")
        (self.cache / "current-theme").write_text("mine\n")
        applied = []
        with patch.object(self.cli, "apply_theme", side_effect=applied.append):
            self.cli.delete_theme("mine", ask_first=lambda *arguments: True)
        self.assertEqual(applied, ["jade"])
        self.assertFalse(directory.exists())
        with self.assertRaises(ValueError):
            self.cli.delete_theme("norse", ask_first=lambda *arguments: True)

    def test_lockscreens_are_listed_configured_and_deleted(self):
        value = own_style.create_lockscreen("Rune Lock", "material-you-dark", str(picture(self.pictures / "lake.png")),
                                            accent="2BB87A", greeting="  Welcome   home ")
        self.assertEqual(value, "user:rune-lock")
        settings = ROOT / "quickshell/lockscreen/scripts/settings.py"

        def run(*arguments):
            return subprocess.run([sys.executable, str(settings), *arguments], capture_output=True, text=True,
                                  check=True).stdout
        self.assertIn("user:rune-lock\tRune Lock", run("list").splitlines())
        self.assertEqual(run("design", value).strip(), "material-you-dark")
        config = json.loads(run("config", value))
        self.assertEqual((config["accent"], config["greeting"], config["themeMode"]), ("#2bb87a", "Welcome home", "dark"))
        self.assertTrue(config["background"].startswith("file://") and config["background"].endswith("picture.png"))
        self.assertTrue(run("preview", value).strip().endswith("picture.png"))
        with self.assertRaises(ValueError):
            own_style.create_lockscreen("Bad", "nothing", str(self.pictures / "lake.png"))
        selected = eitr_paths.config("lockscreen/selected")
        selected.parent.mkdir(parents=True)
        selected.write_text(value + "\n")
        self.assertEqual(run("current").strip(), value)
        real_run = subprocess.run
        with patch.object(self.cli.subprocess, "run") as calls:
            calls.side_effect = lambda command, **options: (
                subprocess.CompletedProcess(command, 0, "") if "select" in command else real_run(command, **options))
            self.cli.delete_lockscreen(value, ask_first=lambda *arguments: True)
        self.assertEqual(calls.call_args.args[0][-2:], ["select", "material-you-dark"])
        self.assertEqual(own_style.own_lockscreens(), {})


class MenuTests(SandboxTest):
    def lua(self, script):
        environment = dict(os.environ, LC_ALL="C", LANG="C")
        return subprocess.run(["lua", "-e", script], cwd=ROOT, env=environment, capture_output=True, text=True,
                              check=True).stdout.splitlines()

    def test_wallpaper_menu_lists_own_pictures_with_delete(self):
        backgrounds = eitr_paths.config("theme/current/backgrounds")
        backgrounds.mkdir(parents=True)
        picture(backgrounds / "01-shipped.png")
        mine = own_style.add_wallpaper(str(picture(self.pictures / "lake.png")))
        rows = self.lua('dofile("elephant/menus/wallpaper.lua") for _, entry in ipairs(GetEntries()) do '
                        'print(entry.Text .. "|" .. (entry.Subtext or "") .. "|" .. tostring(entry.Actions.wallpaper_delete)) end')
        self.assertIn("Add My Own Wallpaper|A picture file or an https address, kept on this computer|nil", rows)
        self.assertIn("01-shipped.png||nil", rows)
        own_row = next(row for row in rows if row.startswith("lake.png|"))
        self.assertIn("|Yours|", own_row)
        self.assertIn(f"wallpaper delete '{mine}'", own_row)
        # A theme made from that picture keeps a copy: while it is current, the picture is listed once.
        shutil.copy(mine, backgrounds / mine.name)
        rows = self.lua('dofile("elephant/menus/wallpaper.lua") for _, entry in ipairs(GetEntries()) do print(entry.Text) end')
        self.assertEqual(rows.count("lake.png"), 1)
        self.assertEqual(own_style.wallpapers(beside=backgrounds), [])
        self.assertEqual(own_style.wallpapers(), [mine])

    def test_lockscreen_menu_offers_creation_and_deleting_own_designs(self):
        own_style.create_lockscreen("Rune Lock", "theme-wallpaper", str(picture(self.pictures / "lake.png")))
        rows = self.lua('dofile("elephant/menus/lockscreen.lua") for _, entry in ipairs(GetEntries()) do '
                        'print(entry.Text .. "|" .. (entry.Subtext or "") .. "|" .. tostring(entry.Actions.lockscreen_delete)) end')
        self.assertTrue(any(row.startswith("Create Lockscreen|") for row in rows))
        self.assertIn("Nothing||nil", rows)
        own_row = next(row for row in rows if row.startswith("Rune Lock|"))
        self.assertIn("lockscreen delete 'user:rune-lock'", own_row)

    def test_theme_lists_mark_own_themes(self):
        own_style.create_theme("Lake", str(picture(self.pictures / "lake.png")), mode="dark")
        lines = "\n".join(f"{name}\t{path}" for name, path in eitr_paths.theme_paths().items())
        rows = self.lua(f'''
            io.popen = function() local lines = {{}} for line in ([[{lines}]]):gmatch("[^\\n]+") do table.insert(lines, line) end
                local index = 0 return {{lines = function() return function() index = index + 1 return lines[index] end end,
                close = function() end}} end
            dofile("elephant/menus/theme-dark.lua")
            for _, entry in ipairs(GetEntries()) do
                print(entry.Value .. "|" .. (entry.Subtext or "") .. "|" .. tostring(entry.Actions.theme_delete) .. "|" .. tostring(entry.Actions.theme_colors))
            end''')
        own_row = next(row for row in rows if row.startswith("lake|"))
        self.assertIn("|Yours|", own_row)
        self.assertIn("theme delete 'lake'", own_row)
        self.assertIn("theme colors 'lake'", own_row)
        self.assertIn("norse||nil|nil", rows)

    def test_theme_rows_offer_creation(self):
        rows = json.loads((ROOT / "elephant/menu-rows/theme.json").read_text())
        self.assertIn("own.py theme create", rows[-1]["actions"]["open"])

    def test_shell_resolver_prefers_overrides_then_own_then_shipped(self):
        own_style.create_theme("Lake", str(picture(self.pictures / "lake.png")))
        script = 'source distro/lib/paths.sh; eitr_theme_dir lake; eitr_theme_dir norse; eitr_theme_dir missing || echo none'
        output = subprocess.run(["bash", "-c", script], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        self.assertEqual(output.splitlines(), [str(eitr_paths.data("eitr/themes/lake")), str(ROOT / "themes/norse"), "none"])


if __name__ == "__main__":
    unittest.main()
