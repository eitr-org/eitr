import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

DISTRO = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


payload = load("eitr_payload_repo", DISTRO / "payload/payload.py")
publish = load("eitr_publish", DISTRO / "repo/publish.py")


class RepositoryTests(unittest.TestCase):
    def test_keyring_and_online_repository_wait_for_the_signing_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "distro").mkdir()
            (root / "distro/local-packages.txt").write_text("eitr-cmux-tui-bin\n")
            self.assertIsNone(payload.signing_key(root))
            self.assertEqual(payload.desktop_local(root), ["eitr-cmux-tui-bin"])
            (root / "distro/keys").mkdir()
            (root / "distro/keys/eitr.asc").write_text("-----BEGIN PGP PUBLIC KEY BLOCK-----\n")
            (root / "distro/keys/eitr.fingerprint").write_text("0123456789ABCDEF0123456789ABCDEF01234567\n")
            self.assertEqual(payload.desktop_local(root), ["eitr-cmux-tui-bin", "eitr-keyring"])
            (root / "distro/keys/eitr.fingerprint").write_text("not a fingerprint\n")
            with self.assertRaises(ValueError):
                payload.signing_key(root)

    def test_online_repository_requires_signatures(self):
        section = payload.eitr_repository()
        self.assertIn("[eitr]", section)
        self.assertIn("SigLevel = Required", section)
        self.assertIn("Server = https://download.eitr.info/repo", section)

    def test_personal_only_packages_never_reach_the_public_repository(self):
        personal_only = json.loads((DISTRO / "redistribution.json").read_text())["personal_only"]
        aur = {line.strip() for name in ("aur-packages.txt", "aur-apps.txt")
               for line in (DISTRO / name).read_text().splitlines() if line.strip() and not line.startswith("#")}
        # The default payload never carries them; Install > Browsers, Developer Apps and Productivity offer them.
        self.assertEqual(set(personal_only) & aur, set())
        with tempfile.TemporaryDirectory() as directory:
            for name in ("google-chrome-141.0-1-x86_64.pkg.tar.zst", "walker-2.17.2-1-x86_64.pkg.tar.zst",
                         "eitr-desktop-1:0.3.0.20261014.120000.gabc1234-1-any.pkg.tar.zst",
                         "walker-2.17.2-1-x86_64.pkg.tar.zst.sig"):
                (Path(directory) / name).write_text("")
            kept, excluded = publish.select(directory, personal_only)
        self.assertEqual([path.name for path in kept], ["eitr-desktop-1:0.3.0.20261014.120000.gabc1234-1-any.pkg.tar.zst",
                                                         "walker-2.17.2-1-x86_64.pkg.tar.zst"])
        self.assertEqual(excluded, ["google-chrome"])

    def test_epoch_colons_are_renamed_in_file_names(self):
        name = Path("eitr-desktop-1:0.3.0.20261014.120000.gabc1234-1-any.pkg.tar.zst")
        self.assertEqual(publish.package_name(name), "eitr-desktop")
        self.assertEqual(publish.asset_name(name), "eitr-desktop-1.0.3.0.20261014.120000.gabc1234-1-any.pkg.tar.zst")


class R2UploadTests(unittest.TestCase):
    def test_packages_first_previous_publish_kept_older_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            new = folder / "eitr-desktop-3-1-any.pkg.tar.zst"
            same = folder / "eitr-artwork-1-1-any.pkg.tar.zst"
            for path in (new, same):
                path.write_bytes(b"package")
                Path(str(path) + ".sig").write_bytes(b"sig")
            database, signature = folder / "eitr.db", folder / "eitr.db.sig"
            database.write_bytes(b"db")
            signature.write_bytes(b"sig")
            existing = dict.fromkeys({"eitr.db", "eitr.db.sig", same.name + ".sig",
                                      "eitr-desktop-2-1-any.pkg.tar.zst", "eitr-desktop-2-1-any.pkg.tar.zst.sig",
                                      "eitr-desktop-1-1-any.pkg.tar.zst", "eitr-desktop-1-1-any.pkg.tar.zst.sig"}, 1)
            existing[same.name] = len(b"package")
            calls = []

            def r2(arguments, endpoint, **kwargs):
                calls.append(arguments)
                self.assertEqual(endpoint, "https://abc.r2.cloudflarestorage.com")
                return ""

            packages = sorted([new, Path(str(new) + ".sig"), same, Path(str(same) + ".sig")])
            with patch.object(publish, "published_keys", return_value=existing), \
                    patch.object(publish, "listed_files", return_value={"eitr-desktop-2-1-any.pkg.tar.zst", same.name}), \
                    patch.object(publish, "r2", side_effect=r2):
                publish.upload_r2(packages, [database, signature], "https://abc.r2.cloudflarestorage.com")
        uploads = [call[2] for call in calls if call[:2] == ["s3", "cp"] and not call[2].startswith("s3://")]
        self.assertEqual(uploads, [str(new), str(new) + ".sig", str(database), str(signature)],
                         "only new packages, then the database last")
        caching = {call[2]: call[call.index("--cache-control") + 1] for call in calls if "--cache-control" in call}
        self.assertEqual(caching[str(database)], "no-cache")
        self.assertIn("immutable", caching[str(new)])
        removed = [call[2].rsplit("/", 1)[1] for call in calls if call[:2] == ["s3", "rm"]]
        self.assertEqual(removed, ["eitr-desktop-1-1-any.pkg.tar.zst", "eitr-desktop-1-1-any.pkg.tar.zst.sig"],
                         "the previous publish stays one more round; older files go")

    def test_upload_refuses_a_published_name_with_different_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "eitr-artwork-1-1-any.pkg.tar.zst"
            package.write_bytes(b"rebuilt package")
            with patch.object(publish, "published_keys", return_value={package.name: 3}), \
                    patch.object(publish, "r2", return_value=""), \
                    self.assertRaisesRegex(RuntimeError, "different contents"):
                publish.upload_r2([package], [], "https://abc.r2.cloudflarestorage.com")

    def test_r2_commands_always_name_the_profile_and_endpoint(self):
        with patch.object(publish, "run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run:
            publish.r2(["s3", "ls"], "https://abc.r2.cloudflarestorage.com")
        command = run.call_args.args[0]
        self.assertEqual(command[-6:], ["--profile", "eitr-r2", "--endpoint-url",
                                        "https://abc.r2.cloudflarestorage.com", "--region", "auto"])

    def test_a_database_lists_its_package_files(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name, file in (("eitr-desktop-1-1", "eitr-desktop-1.0.6-1-any.pkg.tar.zst"), ("yay-13-1", "yay-13-1-x86_64.pkg.tar.zst")):
                (folder / name).mkdir()
                (folder / name / "desc").write_text(f"%FILENAME%\n{file}\n\n%NAME%\n{name}\n")
            subprocess.run(["bsdtar", "-czf", str(folder / "eitr.db"), "-C", str(folder), "eitr-desktop-1-1", "yay-13-1"], check=True)
            self.assertEqual(publish.listed_files(folder / "eitr.db"),
                             {"eitr-desktop-1.0.6-1-any.pkg.tar.zst", "yay-13-1-x86_64.pkg.tar.zst"})


class ReleaseDesktopTests(unittest.TestCase):
    def load(self):
        spec = importlib.util.spec_from_file_location("release_desktop", DISTRO / "repo/release-desktop.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_downloads_name_a_user_agent_cloudflare_accepts(self):
        release = self.load()
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(release.urllib.request, "urlopen", side_effect=OSError("stop")) as urlopen, \
                self.assertRaises(OSError):
            release.fetch("https://download.eitr.info/repo/eitr.db", Path(directory) / "eitr.db")
        self.assertNotIn("Python-urllib", urlopen.call_args.args[0].get_header("User-agent"))

    def test_repository_filenames_cannot_escape_download_directories(self):
        for filename in ("../../outside.pkg.tar.zst", "/outside.pkg.tar.zst",
                         "https://example.org/file.pkg.tar.zst", "file?query.pkg.tar.zst",
                         "file#fragment.pkg.tar.zst", "file\\name.pkg.tar.zst", "-option.pkg.tar.zst"):
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                publish.validate_package_filename(filename)
        publish.validate_package_filename("eitr-desktop-1:0.6.3-1-any.pkg.tar.zst")
        release = self.load()
        with patch.object(release, "fetch") as fetch, self.assertRaises(ValueError):
            release.reuse_published_packages(["../../outside.pkg.tar.zst"], Path("/unused"), Path("/unused"))
        fetch.assert_not_called()

    def test_database_rejects_unsafe_filenames_and_archive_errors(self):
        with patch.object(publish.subprocess, "run", return_value=subprocess.CompletedProcess(
                [], 0, "%FILENAME%\n../../outside.pkg.tar.zst\n", "")), self.assertRaises(ValueError):
            publish.listed_files(Path("unused.db"))
        with patch.object(publish.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "bsdtar")), \
                self.assertRaises(subprocess.CalledProcessError):
            publish.listed_files(Path("unused.db"))

    def test_database_is_authenticated_before_package_names_are_read(self):
        release = self.load()
        for accepted in (False, True):
            with self.subTest(accepted=accepted), patch.object(release, "fetch") as fetch, \
                    patch.object(release, "signing_environment", return_value={}), \
                    patch.object(release, "valid_signature", return_value=accepted), \
                    patch.object(release.publish, "listed_files", return_value={"example-1-1-any.pkg.tar.zst"}) as listed:
                if accepted:
                    self.assertEqual(release.published_assets(), ["example-1-1-any.pkg.tar.zst"])
                    listed.assert_called_once()
                else:
                    with self.assertRaisesRegex(RuntimeError, "database failed signature"):
                        release.published_assets()
                    listed.assert_not_called()
                self.assertTrue(fetch.call_args_list[-1].args[0].endswith("eitr.db.sig"))

    def test_signature_requires_success_and_exact_signer(self):
        release = self.load()
        fingerprint = (DISTRO / "keys/eitr.fingerprint").read_text().strip()
        for status, output, accepted in (
                (0, f"[GNUPG:] VALIDSIG {fingerprint} 2026", True),
                (1, f"[GNUPG:] VALIDSIG {fingerprint} 2026", False),
                (0, f"[GNUPG:] VALIDSIG {fingerprint}BAD 2026", False),
                (0, f"untrusted text VALIDSIG {fingerprint}", False)):
            with self.subTest(status=status, output=output), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                downloads, repo, work = root / "cache", root / "repo", root / "work"
                for folder in (downloads, repo, work):
                    folder.mkdir()
                name = "example-1-1-any.pkg.tar.zst"
                (downloads / name).write_bytes(b"package")
                with patch.object(release, "cache", return_value=downloads), \
                        patch.object(release, "fetch"), patch.object(release, "run"), \
                        patch.object(release.subprocess, "run", return_value=subprocess.CompletedProcess([], status, output, "")):
                    if accepted:
                        release.reuse_published_packages([name], repo, work)
                        self.assertEqual((repo / name).read_bytes(), b"package")
                    else:
                        with self.assertRaises(RuntimeError):
                            release.reuse_published_packages([name], repo, work)
                        self.assertFalse((repo / name).exists())

    def test_artwork_is_rebuilt_only_when_its_version_is_not_published(self):
        release = self.load()
        for published, expected in ((True, ["eitr-desktop", "eitr-sunshine"]), (False, ["eitr-desktop", "eitr-artwork", "eitr-sunshine"])):
            artwork = "eitr-artwork-20261014.211144.gea4111e-1-any.pkg.tar.zst"
            assets = ["eitr.db", "linux-1-1-x86_64.pkg.tar.zst", "eitr-desktop-1.0.3.0-1-any.pkg.tar.zst",
                      *([artwork] if published else ["eitr-artwork-20261001.000000.g1111111-1-any.pkg.tar.zst"])]
            built, reused = [], []

            def build(name, work):
                built.append(name)
                path = Path(work) / f"{name}-9-1-any.pkg.tar.zst"
                path.write_bytes(b"")
                return path

            with self.subTest(published=published), \
                    patch.object(release, "require_pushed_head", return_value="abc1234"), \
                    patch.object(release, "published_assets", return_value=assets), \
                    patch.object(release, "package_file", side_effect=lambda name: artwork if name == "eitr-artwork" else "eitr-sunshine-9-1-any.pkg.tar.zst"), \
                    patch.object(release, "build", side_effect=build), \
                    patch.object(release, "reuse_published_packages",
                                 side_effect=lambda names, repo, work, **options: reused.extend(names)), \
                    patch.object(release, "run"), patch.object(sys, "argv", ["release", "--dry-run", "/tmp/x"]):
                release.main()
            self.assertEqual(built, expected)
            self.assertEqual(reused, ["linux-1-1-x86_64.pkg.tar.zst", *([artwork] if published else [])])

    def test_testing_mirrors_the_desktop_but_not_the_artwork(self):
        release = self.load()
        desktop = Path("eitr-desktop-1:0.6.3.20261018.120000.gabc1234-1-any.pkg.tar.zst")
        artwork = Path("eitr-artwork-20261018.120000.gabc1234-1-any.pkg.tar.zst")
        self.assertEqual(release.mirrored([desktop, artwork]), [desktop])

    def test_release_tool_is_not_packaged(self):
        sys.path.insert(0, str(DISTRO / "lib"))
        from layout import Layout
        self.assertFalse(Layout(DISTRO.parent).classify("distro/repo/release-desktop.py")["runtime"])


if __name__ == "__main__":
    unittest.main()
