import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eitr_payload", DISTRO / "payload/payload.py")
payload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(payload)


class PayloadDefinitionTests(unittest.TestCase):
    def test_local_packages_are_built_and_installed_on_both_paths(self):
        # The committed signing key adds the keyring that trusts the [eitr] repository.
        self.assertEqual(payload.desktop_local(), ["eitr-artwork", "eitr-cmux-tui-bin", "eitr-keyring"])
        builder = (DISTRO / "payload/build-payload.py").read_text()
        self.assertIn("builder.build_local_packages()", builder)
        self.assertIn("payload.desktop_local(SOURCE)", (DISTRO / "archinstall/eitr-guided-install").read_text())
        self.assertIn('manifest "$repo_root/distro/local-packages.txt"', (DISTRO / "install.sh").read_text())
        recipe = (DISTRO / "pkg/eitr-cmux-tui-bin/PKGBUILD").read_text()
        self.assertNotIn("SKIP", recipe)
        self.assertNotIn("/latest/", recipe)
        self.assertIn('"$pkgdir/usr/bin/cmux"', recipe)

    def test_transactions_cover_installer_template_and_every_hardware_manifest(self):
        transactions = payload.transactions()
        template = json.loads((DISTRO / "archinstall/user_configuration.json").read_text())
        self.assertIn(template["packages"], transactions)
        desktop = [packages for packages in transactions if "eitr-desktop" in packages]
        self.assertEqual(len(desktop), 1 + len(payload.hardware_manifests()))
        for packages in desktop:
            self.assertIn("hyprland", packages)
            self.assertIn("yay", packages)
            self.assertIn("walker", packages)
            self.assertIn("eitr-cmux-tui-bin", packages)
            self.assertIn("less", packages)
        for manifest in payload.hardware_manifests():
            self.assertTrue(any(set(payload.manifest(manifest)) <= set(packages) for packages in desktop),
                            manifest.name)
        self.assertEqual(transactions[0][:2], ["base", "sudo"])

    def test_dependency_names_drop_version_constraints(self):
        self.assertEqual(payload.dependency_name("python-clickgen>=2.0.0"), "python-clickgen")
        self.assertEqual(payload.dependency_name("libgtk-3.so=0"), "libgtk-3.so")
        self.assertEqual(payload.dependency_name("walker"), "walker")

    def test_package_file_names_keep_hyphenated_names(self):
        self.assertEqual(payload.package_file_name("/w/elephant-menus-bin-2.22.1-1-x86_64.pkg.tar.zst"),
                         "elephant-menus-bin")
        self.assertEqual(payload.package_file_name("kvantum-theme-catppuccin-git-r52.abc-1-any.pkg.tar.zst"),
                         "kvantum-theme-catppuccin-git")
        self.assertEqual(payload.package_file_name("1password-8.12.40-31-x86_64.pkg.tar.xz"), "1password")

    def test_builder_prunes_superseded_versions_after_a_build(self):
        source = (DISTRO / "payload/build-payload.py").read_text()
        self.assertIn('"--keep", "1"', source)
        main = source.split("def main():", 1)[1]
        self.assertLess(main.index("builder.write_manifest("), main.index("builder.prune_work()"))
        self.assertIn('"paccache")', main)

    def test_build_order_puts_dependencies_first_and_rejects_cycles(self):
        order = payload.build_order({"bibata": {"clickgen"}, "clickgen": {"python-attrs-official"},
                                     "walker": set()})
        self.assertLess(order.index("clickgen"), order.index("bibata"))
        with self.assertRaises(ValueError):
            payload.build_order({"a": {"b"}, "b": {"a"}})

    def test_offline_config_reads_only_the_payload(self):
        conf = payload.pacman_conf("/media/eitr/pool", "/media/eitr/repo")
        self.assertNotIn("Include", conf)
        self.assertNotIn("http", conf)
        for repository in ("core", "extra", "multilib"):
            self.assertIn(f"[{repository}]\nServer = file:///media/eitr/pool\n", conf)
        self.assertIn("SigLevel = Required DatabaseOptional", conf)
        self.assertIn("[eitr]\n", conf)

    def test_online_config_enables_multilib_from_the_package_default(self):
        default = ("[options]\nArchitecture = auto\n\n[core]\nInclude = /etc/pacman.d/mirrorlist\n\n"
                   "#[multilib]\n#Include = /etc/pacman.d/mirrorlist\n")
        conf = payload.online_pacman_conf(default)
        self.assertIn("[multilib]\nInclude = /etc/pacman.d/mirrorlist\n", conf)
        self.assertNotIn("file://", conf)
        with self.assertRaises(ValueError):
            payload.online_pacman_conf("[options]\n")

    def test_target_mirrorlist_uses_https_servers(self):
        servers = [line for line in (DISTRO / "payload/mirrorlist").read_text().splitlines()
                   if line.startswith("Server")]
        self.assertTrue(servers)
        self.assertTrue(all(line.startswith("Server = https://") for line in servers))


class LocalPackageBuildTests(unittest.TestCase):
    def test_recipes_build_and_download_under_the_work_directory(self):
        spec = importlib.util.spec_from_file_location("eitr_build_payload", DISTRO / "payload/build-payload.py")
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            builder = build.Builder(work, work / "out")
            seen = {}

            def makepkg(recipe, flags):
                seen[recipe.name] = {"build": os.environ["BUILDDIR"], "sources": os.environ["SRCDEST"]}
                return []

            with patch.object(builder, "makepkg", side_effect=makepkg), patch.dict(os.environ):
                os.environ.pop("BUILDDIR", None)
                os.environ.pop("SRCDEST", None)
                builder.build_local_packages()
                self.assertNotIn("BUILDDIR", os.environ)
                self.assertNotIn("SRCDEST", os.environ)
            self.assertEqual(sorted(seen), payload.desktop_local())
            self.assertEqual(seen["eitr-cmux-tui-bin"]["build"], str(work / "eitr-cmux-tui-bin"))
            self.assertEqual(seen["eitr-cmux-tui-bin"]["sources"], str(work / "sources/eitr-cmux-tui-bin"))
            self.assertTrue((work / "sources/eitr-cmux-tui-bin").is_dir())


    def test_sources_of_every_built_package_are_archived_outside_the_payload(self):
        spec = importlib.util.spec_from_file_location("eitr_build_payload", DISTRO / "payload/build-payload.py")
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            builder = build.Builder(work, work / "out")
            builder.recipes = {"walker": work / "aur/walker", "unshipped": work / "aur/unshipped"}
            aur = {"walker": {"commit": "abc", "version": "1-1", "url": "https://aur.archlinux.org/walker.git"}}
            calls = []
            with patch.object(build, "run", side_effect=lambda args, **kwargs: calls.append((args, kwargs))):
                saved = builder.save_sources(work / "sources-out", aur)
            self.assertEqual(saved, sorted(["walker"] + [name for name in payload.desktop_local() if name != "eitr-artwork"]))
            self.assertTrue(all(args[:2] == ["makepkg", "--allsource"] for args, _ in calls))
            self.assertTrue(all(kwargs["env"]["SRCPKGDEST"] == str(work / "sources-out") for _, kwargs in calls))
            local = next(kwargs for _, kwargs in calls if kwargs["cwd"].name == "eitr-cmux-tui-bin")
            self.assertEqual(local["env"]["SRCDEST"], str(work / "sources/eitr-cmux-tui-bin"))
            record = json.loads((work / "sources-out/SOURCES.json").read_text())
            self.assertEqual(record["aur"], aur)
            self.assertIn("eitr-cmux-tui-bin", record["local"])
        script = (DISTRO / "payload/build-payload.py").read_text()
        self.assertIn('"--sources", type=Path, required=True', script)
        self.assertIn("--sources must be outside the payload", script)


if __name__ == "__main__":
    unittest.main()
