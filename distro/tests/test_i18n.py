import importlib.util
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import eitr_i18n
import gettext
import io

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("i18n_build", ROOT / "tools/i18n-build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class LocaleTests(unittest.TestCase):
    def test_all_registered_interface_messages_have_complete_catalogs(self):
        sources = builder.extract()
        for locale in ("pt_BR", "es", "de", "fr"):
            for layer in ("helpers", "menus", "qml"):
                path = ROOT / "i18n/catalogs" / locale / (layer + ".json")
                with self.subTest(locale=locale, layer=layer):
                    catalog = json.loads(path.read_text())
                    self.assertEqual(builder.validate(catalog, sources[layer]), [])

    def test_named_placeholders_cannot_be_removed_or_renamed(self):
        source = "{current} of {total} entries"
        self.assertTrue(builder.validate({}, {source: []}))
        for translation in ("{current} entrées", "{position} sur {total} entrées"):
            with self.subTest(translation=translation):
                self.assertTrue(builder.validate({source: translation}, {source: []}))

    def test_shell_named_values_are_literal_data(self):
        result = subprocess.run(["bash", "-c",
            'source "$1"; eitr_gettext "{label} was removed" "label=literal {other}"',
            "test", str(ROOT / "distro/lib/i18n.sh")],
            env=dict(os.environ, LC_ALL="", LC_MESSAGES="pt_BR"), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("literal {other}", result.stdout)

    def test_extraction_is_the_same_inside_a_package_build(self):
        # makepkg runs check() under .../src/eitr; folder filters must not see that "src".
        with tempfile.TemporaryDirectory() as directory:
            nested = Path(directory) / "src" / "eitr"
            nested.parent.mkdir()
            nested.symlink_to(ROOT)
            self.assertEqual(builder.extract(nested), builder.extract(ROOT))

    def test_precedence_and_normalization(self):
        supported = {"en": {}, "pt_BR": {}, "de": {}, "fr": {}, "es": {}}
        cases = [({"LANG": "pt.UTF-8"}, "pt_BR"),
                 ({"LANG": "pt_PT.UTF-8"}, "pt_BR"),
                 ({"LANG": "pt_BR.UTF-8"}, "pt_BR"),
                 ({"LANG": "es_ES.UTF-8"}, "es"),
                 ({"LANG": "de-DE"}, "de"),
                 ({"LANG": "pt_BR", "LC_MESSAGES": "fr_FR.UTF-8"}, "fr"),
                 ({"LANG": "pt_BR", "LC_MESSAGES": "fr", "LC_ALL": "C.UTF-8"}, "en"),
                 ({"LANG": "fr", "LC_MESSAGES": ""}, "fr"),
                 ({"LANG": "../../fr"}, "en"), ({"LANG": "POSIX"}, "en"),
                 ({"LANG": "ja_JP.UTF-8"}, "en"), ({}, "en")]
        for environment, expected in cases:
            with self.subTest(environment=environment):
                self.assertEqual(eitr_i18n.select_locale(environment, supported), expected)

    def test_sort_keys_ignore_accents(self):
        self.assertEqual(builder.sort_key("Áudio"), "audio")
        self.assertEqual(builder.sort_key("Área"), "area")
        self.assertLess(builder.sort_key("Áudio"), builder.sort_key("Zebra"))

    def test_partial_regional_table_falls_back_per_message(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for locale, catalog in {"en": {"One": "One", "Two": "Two", "Three": "Three"},
                                    "es": {"One": "Uno", "Two": "Dos"},
                                    "es_MX": {"One": "Regional", "Two": ""}}.items():
                path = root / "i18n/catalogs" / locale / "menus.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(catalog))
            self.assertEqual(eitr_i18n.table("menus", "es_MX", root),
                             {"One": "Regional", "Two": "Dos", "Three": "Three"})

    def test_gettext_source_fallback_preserves_named_values(self):
        with patch.dict(os.environ, {"LC_ALL": "C"}):
            self.assertEqual(eitr_i18n.tr("Hello {name}", name="Erick"), "Hello Erick")
            self.assertEqual(eitr_i18n.ntr("{count} item", "{count} items", 2), "2 items")

    def test_shell_never_evaluates_translation_or_message(self):
        script = 'source "$1"; eitr_gettext "$2"'
        source = 'Hello $(false); `false` {name}'
        output = subprocess.check_output(["bash", "-c", script, "i18n-test",
                                          str(ROOT / "distro/lib/i18n.sh"), source], text=True)
        self.assertEqual(output, source)

    def test_compiled_gettext_matches_each_catalog(self):
        for locale in ("pt_BR", "es", "de", "fr"):
            expected = json.loads((ROOT / "i18n/catalogs" / locale / "helpers.json").read_text())["Cancelled."]
            with self.subTest(locale=locale), patch.dict(os.environ, {"LC_ALL": "", "LC_MESSAGES": locale + ".UTF-8"}):
                self.assertEqual(eitr_i18n.tr("Cancelled."), expected)
                self.assertNotEqual(expected, "Cancelled.")
                self.assertEqual(eitr_i18n.tr("An unregistered English message"), "An unregistered English message")

    def test_confirmation_word_is_identical_in_prompt_and_check(self):
        specification = importlib.util.spec_from_file_location("translated_factory_reset", ROOT / "distro/system/factory-reset.py")
        reset = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(reset)
        for locale in ("en", "pt_BR", "es", "de", "fr"):
            with self.subTest(locale=locale), patch.dict(os.environ, {"LC_ALL": "", "LC_MESSAGES": locale}), \
                    patch.object(reset, "layout", side_effect=AssertionError("stopped before any disk access")):
                with self.assertRaises(reset.ResetError) as rejected:
                    reset.reset(next(iter(reset.MODES)), "wrong confirmation")
                self.assertIn(reset.CONFIRMATION, str(rejected.exception))
                with self.assertRaisesRegex(AssertionError, "stopped before any disk access"):
                    reset.reset(next(iter(reset.MODES)), reset.CONFIRMATION)

    def test_installer_translates_labels_without_changing_choice_values(self):
        specification = importlib.util.spec_from_file_location("translated_installer_ui", ROOT / "distro/archinstall/installer-ui.py")
        installer = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(installer)
        disk = {"size": 200 * 1024 ** 3, "free": 100 * 1024 ** 3, "alongside": True, "contents": "Windows BitLocker"}
        for locale in ("en", "pt_BR", "es", "de", "fr"):
            with self.subTest(locale=locale), patch.dict(os.environ, {"LC_ALL": "", "LC_MESSAGES": locale}):
                options, note = installer.layout_options(disk)
                self.assertEqual([value for label, value in options], ["alongside", "erase"])
                self.assertTrue(note)
                self.assertEqual(len(installer.alongside_notes(disk)), 2)


class CatalogTests(unittest.TestCase):
    def test_all_marked_sources_are_covered(self):
        self.assertEqual(builder.build(check=True), [])

    def test_product_names_are_not_translated(self):
        for locale in ("pt_BR", "es", "de", "fr"):
            for layer in ("menus", "qml", "handbook"):
                catalog = json.loads((ROOT / "i18n/catalogs" / locale / (layer + ".json")).read_text())
                for product in ("WiFi", "Bluetooth", "OBS", "LIVE", "VS Code", "Steam", "GeForce NOW", "RetroArch"):
                    if product in catalog:
                        with self.subTest(locale=locale, layer=layer, product=product):
                            self.assertEqual(catalog[product], product)

    def test_missing_entries_are_listed_individually(self):
        errors = builder.validate({"Hello": ""}, {"Hello": [], "Goodbye": []})
        self.assertEqual(len(errors), 2)
        self.assertTrue(all("Missing translation:" in error for error in errors))

    def test_placeholders_are_checked_with_multiplicity(self):
        source = "Hello {name}, %1 of %2 (%s)"
        self.assertEqual(builder.validate({source: "Bonjour {name}, %2 sur %1 (%s)"}, {source: []}), [])
        for translated in ("Bonjour {nom}, %1 of %2 (%s)", "Hello {name}, %1 (%s)", "Hello {name}, %1 %1 %2 (%s)"):
            self.assertIn("Placeholder mismatch:", builder.validate({source: translated}, {source: []})[0])

    def test_english_fallbacks_are_listed_and_build_tools_stay_untranslated(self):
        pending = json.loads((ROOT / "i18n/pending-helpers.json").read_text())
        for locale in ("pt_BR", "es", "de", "fr"):
            catalog = json.loads((ROOT / "i18n/catalogs" / locale / "helpers.json").read_text())
            self.assertEqual(pending[locale], [source for source, value in catalog.items() if source == value])
            for source in catalog:
                self.assertNotIn("display_value_", source)
                self.assertFalse(source.lower().startswith("usage:"), source)
                if "[y/N]" in source:
                    self.assertIn("[y/N]", catalog[source])
                self.assertNotIn("[Y/n]", source)
                self.assertFalse(source.startswith(("export ", "unset ")), source)
        for directory in (ROOT / "distro/payload", ROOT / "distro/repo"):
            for path in directory.glob("*.py"):
                self.assertNotIn("from eitr_i18n import", path.read_text(), str(path))

    def test_msgfmt_output_is_readable_by_standard_gettext(self):
        po, binary = builder.compile_gettext({"Hello {name}": "Bonjour {name}"}, "fr")
        self.assertIn('msgid "Hello {name}"', po)
        catalog = gettext.GNUTranslations(io.BytesIO(binary))
        self.assertEqual(catalog.gettext("Hello {name}").format(name="Erick"), "Bonjour Erick")


if __name__ == "__main__":
    unittest.main()

class OutputBoundaryTests(unittest.TestCase):
    def load(self, relative):
        spec = importlib.util.spec_from_file_location("boundary_" + Path(relative).stem.replace('-', '_'), ROOT / relative)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_cloud_shell_output_is_literal_in_all_locales(self):
        contexts = self.load("walker/scripts/menus/cloud/contexts.py")
        for locale in ("en", "pt_BR", "es", "de", "fr"):
            output = io.StringIO()
            with self.subTest(locale=locale), patch.dict(os.environ, LC_ALL="", LC_MESSAGES=locale), \
                    patch("sys.argv", ["contexts.py", "gcp", "--shell", "--defer-project"]), \
                    patch.object(contexts, "contexts", return_value=[{}]), \
                    patch.object(contexts, "pick", return_value={}), \
                    patch.object(contexts, "environment", return_value={"CLOUDSDK_ACTIVE_CONFIG_NAME": "my config"}), \
                    patch("sys.stdout", output):
                contexts.main()
            self.assertEqual(output.getvalue(), "unset CLOUDSDK_CORE_PROJECT\nexport CLOUDSDK_ACTIVE_CONFIG_NAME='my config'\n")
            subprocess.run(["bash", "-n"], input=output.getvalue(), text=True, check=True)

    def test_prompt_tokens_are_literal_and_negative_answer_never_runs_sudo(self):
        for filename in ("firewall", "home-snapshots"):
            module = self.load("walker/scripts/actions/system/" + filename + ".py")
            for locale in ("en", "pt_BR", "es", "de", "fr"):
                with self.subTest(module=filename, locale=locale), \
                        patch.dict(os.environ, LC_ALL="", LC_MESSAGES=locale), \
                        patch.object(module.Path, "is_file", return_value=True), \
                        patch.object(module.subprocess, "run") as command, \
                        patch("builtins.input", return_value="n") as prompt, patch("sys.stdout", io.StringIO()):
                    command.return_value.returncode = 0
                    module.main()
                    self.assertIn("[y/N]", prompt.call_args.args[0])
                    self.assertEqual(command.call_count, 1)
                with patch.dict(os.environ, LC_ALL="", LC_MESSAGES=locale), \
                        patch.object(module.Path, "is_file", return_value=True), \
                        patch.object(module.subprocess, "run") as command, \
                        patch("builtins.input", return_value="yes"), patch("sys.stdout", io.StringIO()):
                    command.return_value.returncode = 0
                    module.main()
                    self.assertEqual(command.call_count, 2)
                    self.assertEqual(command.call_args.args[0][0], "sudo")

    def test_factory_reset_prompt_tokens_match_both_checks(self):
        reset = self.load("walker/scripts/actions/system/factory-reset.py")
        root_reset = self.load("distro/system/factory-reset.py")
        self.assertEqual(reset.CONFIRMATION, root_reset.CONFIRMATION)
        for locale in ("en", "pt_BR", "es", "de", "fr"):
            with self.subTest(locale=locale), patch.dict(os.environ, LC_ALL="", LC_MESSAGES=locale), \
                    patch.object(reset, "show"), patch.object(reset, "helper") as helper, \
                    patch("builtins.input", return_value="n") as prompt, patch("sys.stdout", io.StringIO()):
                reset.reset("everything")
                helper.assert_not_called()
                self.assertIn("[y/N]", prompt.call_args.args[0])
            with patch.dict(os.environ, LC_ALL="", LC_MESSAGES=locale), \
                    patch.object(reset, "show"), patch.object(reset, "helper") as helper, \
                    patch("builtins.input", side_effect=["yes", reset.CONFIRMATION]) as prompt:
                reset.reset("everything")
                self.assertIn(reset.CONFIRMATION, prompt.call_args.args[0])
                self.assertEqual(helper.call_args.args, ("reset", "--mode", "everything", "--confirm", reset.CONFIRMATION))

    def test_form_confirmations_keep_literal_english_answer_tokens(self):
        from eitr_forms import Terminal
        terminal = Terminal.__new__(Terminal)
        for locale in ("en", "pt_BR", "es", "de", "fr"):
            for answer, expected in (("y", True), ("yes", True), ("n", False), ("", False)):
                with self.subTest(locale=locale, answer=answer), \
                        patch.dict(os.environ, LC_ALL="", LC_MESSAGES=locale), \
                        patch.object(terminal, "ask", return_value=answer) as ask:
                    self.assertEqual(terminal.confirm("Continue?", default=False), expected)
                    self.assertEqual(ask.call_args.args[1], "y/N")

    def test_language_picker_only_writes_its_owned_preference(self):
        import eitr_language
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, XDG_CONFIG_HOME=temporary):
            self.assertEqual(eitr_language.selected(), "system")
            eitr_language.save("pt_BR")
            self.assertEqual(eitr_language.selected(), "pt_BR")
            self.assertIn("LC_MESSAGES=pt_BR.UTF-8\nLC_ALL=\n", eitr_language.preference_path().read_text())
            eitr_language.save("system")
            self.assertFalse(eitr_language.preference_path().exists())
            with self.assertRaises(ValueError):
                eitr_language.save("../../evil")

class BootstrapTests(unittest.TestCase):
    def test_commands_installed_in_usr_bin_find_the_library_themselves(self):
        # /usr/bin holds no eitr_bootstrap link, so its commands cannot import it.
        packaged = re.findall(r"install -Dm755 (distro/bin/[\w-]+) \"\$pkgdir/usr/bin/",
                              (ROOT / "distro/pkg/eitr-desktop/PKGBUILD").read_text())
        self.assertIn("distro/bin/eitr", packaged)
        for command in packaged:
            with self.subTest(command=command):
                self.assertNotIn("import eitr_bootstrap", (ROOT / command).read_text())

    def test_isolated_root_scripts_import_the_bootstrap(self):
        # python3 -I leaves the script's folder off sys.path; the offline installer
        # stopped on exactly this ModuleNotFoundError.
        invoked = set(re.findall(r"python3 -I /usr/share/eitr/([\w/.-]+\.py)",
                                 "\n".join(path.read_text() for path in (ROOT / "distro").rglob("*.sh"))))
        shebangs = {str(path.relative_to(ROOT)) for path in (ROOT / "distro/system").glob("*.py")
                    if path.read_text().startswith("#!/usr/bin/python3 -I")}
        scripts = invoked | shebangs
        self.assertIn("quickshell/lockscreen/scripts/install-login.py", scripts)
        self.assertIn("distro/system/eitr-timezone.py", scripts)
        for script in sorted(scripts):
            with self.subTest(script=script):
                # Runs only the script's lines up to and including the bootstrap import.
                check = ("import sys; path = sys.argv[1]; "
                         "header = open(path).read().split('import eitr_bootstrap', 1)[0]; "
                         "exec(compile(header + 'import eitr_bootstrap\\n', path, 'exec'), {'__file__': path})")
                result = subprocess.run([sys.executable, "-I", "-c", check, str(ROOT / script)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_staged_entrypoint_imports_one_library_owner(self):
        from layout import Layout
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            library = root / "distro/lib"
            library.mkdir(parents=True)
            (root / "distro/layout-manifest.json").write_text(json.dumps({"version": 1, "rules": [{"pattern": "**", "runtime": True}]}))
            (root / "distro/legacy-layout.json").write_text("{}")
            (library / "eitr_bootstrap.py").write_text((ROOT / "distro/lib/eitr_bootstrap.py").read_text())
            (library / "marker.py").write_text("value = 'one owner'\n")
            scripts = root / "walker/scripts"
            scripts.mkdir(parents=True)
            (scripts / "eitr_bootstrap.py").symlink_to("../../distro/lib/eitr_bootstrap.py")
            (scripts / "entry.py").write_text("import eitr_bootstrap\nimport marker\nprint(marker.value)\n")
            destination = Path(temporary) / "installed"
            # The PKGBUILD stages with --repo ., a relative root.
            previous = os.getcwd()
            os.chdir(temporary)
            try:
                Layout(Path("source")).stage(destination)
            finally:
                os.chdir(previous)
            self.assertEqual((destination / "walker/scripts/eitr_bootstrap.py").resolve(), destination / "lib/eitr_bootstrap.py")
            environment = dict(os.environ, PYTHONPATH="")
            output = subprocess.check_output(["python3", str(destination / "walker/scripts/entry.py")], env=environment, text=True)
            self.assertEqual(output, "one owner\n")


class SystemLanguageNameTests(unittest.TestCase):
    def test_system_file_precedence_ignores_session(self):
        import eitr_language
        with tempfile.TemporaryDirectory() as temporary:
            locale_file = Path(temporary) / 'locale.conf'
            with patch.dict(os.environ, LC_ALL='fr_FR.UTF-8', LC_MESSAGES='es_ES.UTF-8'):
                for contents, expected in [
                    ('LANG=en_US.UTF-8\nLC_MESSAGES="pt_BR.UTF-8" # message\nLC_ALL=de_DE.UTF-8\n', 'Deutsch'),
                    ('LANG=en_US.UTF-8\nLC_MESSAGES="pt_BR.UTF-8"\nLC_ALL=\n', 'Português (Brasil)'),
                    ('LANG=es_MX.UTF-8\n', 'Español'),
                    ('LANG=unsupported\n', 'English'),
                    ('LANG=C\n', 'English'),
                    ('', 'English'),
                ]:
                    with self.subTest(contents=contents):
                        locale_file.write_text(contents)
                        self.assertEqual(eitr_language.system_name(locale_file), expected)

    def test_unreadable_or_malformed_file_is_not_a_session_fallback(self):
        import eitr_language
        with tempfile.TemporaryDirectory() as temporary:
            locale_file = Path(temporary) / 'locale.conf'
            with self.assertRaises(OSError):
                eitr_language.system_name(locale_file)
            locale_file.write_text('LANG="broken')
            with self.assertRaises(ValueError):
                eitr_language.system_name(locale_file)
