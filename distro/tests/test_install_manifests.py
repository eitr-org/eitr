from pathlib import Path
import configparser
import json
import shutil
import os
import subprocess
import tempfile
import unittest


DISTRO = Path(__file__).resolve().parents[1]


class InstallManifestTests(unittest.TestCase):
    @unittest.skipIf(os.geteuid() == 0, "Installer intentionally rejects root")
    def test_non_executable_installer_runs_preflight_before_installing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            installer = root / "install.sh"
            installer.write_text((DISTRO / "install.sh").read_text())
            installer.chmod(0o644)
            binaries = root / "bin"
            binaries.mkdir()
            for name in ("pacman", "sudo", "systemctl"):
                mock = binaries / name
                mock.write_text("#!/bin/sh\nexit 0\n")
                mock.chmod(0o755)
            env = dict(os.environ, HOME=directory,
                       PATH=str(binaries) + os.pathsep + os.environ["PATH"])
            result = subprocess.run(["bash", str(installer)], env=env,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("NetworkManager is enabled", result.stderr)
            self.assertNotIn("Permission denied", result.stderr)

    def run_check(self, home, populate, findmnt="echo btrfs"):
        binaries = home / "bin"
        binaries.mkdir()
        mocks = {"pacman": "exit 0", "sudo": "exit 0", "systemctl": "exit 1",
                 "findmnt": findmnt}
        for name, body in mocks.items():
            (binaries / name).write_text(f"#!/bin/sh\n{body}\n")
            (binaries / name).chmod(0o755)
        populate(home)
        env = {key: value for key, value in os.environ.items() if not key.startswith("XDG_")}
        env.update(HOME=str(home), PATH=str(binaries) + os.pathsep + os.environ["PATH"])
        return subprocess.run(["bash", str(DISTRO / "install.sh"), "--check"], env=env,
                              capture_output=True, text=True)

    @unittest.skipIf(os.geteuid() == 0, "Installer intentionally rejects root")
    def test_check_lists_every_differing_user_config(self):
        def populate(home):
            for name in ("kitty", "nvim"):
                (home / ".config" / name).mkdir(parents=True)
                filename = "kitty.conf" if name == "kitty" else "init.lua"
                (home / ".config" / name / filename).write_text("mine\n")
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_check(Path(directory), populate)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("would be overwritten", result.stderr)
        self.assertIn(f"{directory}/.config/kitty", result.stderr)
        self.assertIn(f"{directory}/.config/nvim", result.stderr)

    @unittest.skipIf(os.geteuid() == 0, "Installer intentionally rejects root")
    def test_check_rejects_package_database_outside_root_snapshot(self):
        findmnt = 'case "$*" in *FSTYPE*) echo btrfs ;; *pacman*) echo /dev/other ;; *) echo /dev/root ;; esac'
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_check(Path(directory), lambda home: None, findmnt)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("/var/lib/pacman is outside the root snapshot", result.stderr)
        self.assertIn("supported Btrfs layout", result.stderr)

    @unittest.skipIf(os.geteuid() == 0, "Installer intentionally rejects root")
    def test_check_skips_paths_recorded_by_a_previous_partial_run(self):
        def populate(home):
            (home / ".config/kitty").mkdir(parents=True)
            (home / ".config/kitty/changed-after-install").write_text("x\n")
            state = home / ".local/state/eitr"
            state.mkdir(parents=True)
            (state / "installed-paths").write_text(".config/kitty/kitty.conf\n.local/bin/walker\n")
            (home / ".config/kitty/kitty.conf").write_text("mine\n")
            (home / ".local/bin").mkdir(parents=True)
            (home / ".local/bin/walker").symlink_to("../../.config/walker/bin/walker")
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_check(Path(directory), populate)
        self.assertNotIn("would be overwritten", result.stderr)
        self.assertIn("Already installed by this installer (will skip): 2 paths", result.stdout)

    def test_installer_never_overwrites_home_trees_directly(self):
        installer = (DISTRO / "install.sh").read_text()
        self.assertNotIn("cp -a -- \"$repo_root/systemd", installer)
        self.assertNotIn("cp -a -- \"$icon_source", installer)
        self.assertNotIn("HOME_FILES/.local/share/applications/.", installer)
        self.assertIn("gtk-update-icon-cache", installer)
        self.assertNotIn("RequiredForOnline", (DISTRO / "network/20-ethernet.network").read_text())

    def test_removed_packages_stay_out_of_install_manifests(self):
        packages = set()
        for filename in ("packages.txt", "apps.txt", "aur-packages.txt", "aur-apps.txt"):
            packages.update(line.strip() for line in (DISTRO / filename).read_text().splitlines()
                            if line.strip() and not line.startswith("#"))
        self.assertFalse({"swaync", "walker-debug", "mongosh-bin-debug", "cef",
                          "bruno-bin", "ngrok", "kubectl", "helm", "minikube",
                          "cups", "hplip", "system-config-printer", "xf86-input-wacom"} & packages)
        installer = (DISTRO / "install.sh").read_text()
        self.assertIn("https://aur.archlinux.org/yay.git", installer)
        self.assertIn('export MAKEPKG_CONF="$repo_root/distro/makepkg.conf"', installer)
        self.assertNotIn('--options', installer)
        self.assertNotIn('bash "$repo_root/distro/install-development.sh"', installer)
        self.assertNotIn('npm install --global', installer)
        self.assertNotIn('https://claude.ai/install.sh', installer)

    def test_database_tools_and_gnome_shell_are_not_default_installs(self):
        packages = set()
        for filename in ("packages.txt", "apps.txt", "aur-packages.txt", "aur-apps.txt"):
            packages.update(line.strip() for line in (DISTRO / filename).read_text().splitlines()
                            if line.strip() and not line.startswith("#"))
        # Database tools are optional Walker → Install → Databases recipes.
        self.assertFalse({"dbeaver", "mariadb-clients", "mongosh-bin", "pgcli", "redis"} & packages)
        # gnome-control-center depends on gnome-shell, whose GNOME session SDDM lists first.
        self.assertFalse({"gnome-control-center", "gnome-shell", "gnome-session",
                          "nwg-look", "gnome-online-accounts"} & packages)
        # SUPER+; opens the Walker emoji picker, which replaced GNOME Characters.
        self.assertNotIn("gnome-characters", packages)
        # The prebuilt LocalSend bundle avoids a Flutter SDK build on installation.
        self.assertIn("localsend-bin", packages)
        self.assertNotIn("localsend", packages)

    def test_direct_desktop_helper_dependencies_are_explicit(self):
        packages = set((DISTRO / "packages.txt").read_text().splitlines())
        self.assertFalse({"desktop-file-utils", "lm_sensors", "qrencode", "iproute2",
                          "iputils", "procps-ng", "util-linux"} - packages)

    def test_development_runtimes_are_managed_not_explicit_system_packages(self):
        packages = set()
        for filename in ("packages.txt", "apps.txt", "aur-packages.txt", "aur-apps.txt"):
            packages.update(line.strip() for line in (DISTRO / filename).read_text().splitlines()
                            if line.strip() and not line.startswith("#"))
        self.assertFalse({"nodejs", "npm"} & packages)
        self.assertFalse({package for package in packages if package.startswith(("jdk", "jre"))})
        self.assertFalse({"go", "rustup", "fvm", "python-pip"} & packages)
        self.assertIn("python", packages)  # Required by desktop helpers.

    def test_snapshot_and_gaming_dependencies_are_explicit(self):
        packages = set((DISTRO / "packages.txt").read_text().splitlines())
        self.assertFalse({"snapper", "flatpak", "fprintd", "pam-u2f", "lazygit", "lazydocker"} - packages)
        installer = (DISTRO / "install.sh").read_text()
        self.assertIn("recipe gaming geforcenow", installer)
        self.assertNotIn("geforcenow.flatpakrepo", installer)
        self.assertIn("snapshots-setup", installer)
        self.assertIn("sudo /usr/lib/eitr/eitr-system snapshots-setup", installer)
        self.assertNotIn("/usr/local/lib/eitr", installer)

    def test_installer_seeds_defaults_from_the_package(self):
        installer = (DISTRO / "install.sh").read_text()
        package = installer.index("\ninstall_desktop_package\n")
        self.assertLess(installer.index("yay -S --needed"), package)
        self.assertLess(package, installer.index("snapshots-setup\n"))
        self.assertLess(installer.index("clone_once https://github.com/ohmyzsh"), installer.index("  eitr-config seed\n"))
        self.assertIn("/usr/share/eitr/system-update-policy.conf", installer)
        self.assertIn("makepkg --nodeps", installer)
        self.assertIn("sudo pacman -U --needed", installer)
        self.assertNotIn(".local/share/eitr", installer)
        self.assertNotIn("install_path", installer)

    def test_sudo_lecture_is_disabled_by_a_valid_package_drop_in(self):
        drop_in = DISTRO / "system/sudoers-eitr"
        self.assertEqual(drop_in.read_text(), "Defaults lecture = never\n")
        package = (DISTRO / "pkg/eitr-desktop/PKGBUILD").read_text()
        self.assertIn('install -dm750 "$pkgdir/etc/sudoers.d"', package)
        self.assertIn('install -m440 distro/system/sudoers-eitr "$pkgdir/etc/sudoers.d/eitr"', package)
        if shutil.which("visudo"):
            subprocess.run(["visudo", "-cf", str(drop_in)], check=True, capture_output=True)

    def test_dolphin_starts_with_only_the_places_panel(self):
        import base64
        state = (DISTRO / "defaults/home/.local/state/dolphinstaterc").read_text()
        data = base64.b64decode(state.split("State=", 1)[1].strip())
        for dock, visible in (("placesDock", 1), ("foldersDock", 0), ("infoDock", 0), ("terminalDock", 0)):
            name = dock.encode("utf-16-be")
            self.assertEqual(data[data.index(name) + len(name)], visible, dock)

    def test_new_homes_get_standard_folders_and_development(self):
        packages = (DISTRO / "packages.txt").read_text().split()
        self.assertIn("xdg-user-dirs", packages)
        installer = (DISTRO / "install.sh").read_text()
        seed = installer[installer.index("seed_user() {"):installer.index("  eitr-config seed\n")]
        self.assertIn("xdg-user-dirs-update", seed)
        self.assertIn('mkdir -p "$HOME/Development"', seed)
        self.assertIn('xdg-user-dirs-update --set PROJECTS "$HOME/Development"', seed)

    def test_user_seeding_runs_before_the_system_login_setup(self):
        installer = (DISTRO / "install.sh").read_text()
        main = installer.index("\ninstall_desktop_package\n")
        self.assertLess(main, installer.index("\nseed_user\n"))
        self.assertLess(installer.index("\nseed_user\n"),
                        installer.index('sudo bash "$repo_root/distro/system/configure-desktop.sh"'))
        self.assertIn("--seed-user", installer)
        self.assertIn("EITR_NO_SESSION=1", installer)
        self.assertIn('tar --zstd -xf "$EITR_SHELL_ASSETS/$name.tar.zst"', installer)
        self.assertNotIn("Choose a theme in Walker after first login", installer)

    def test_system_setup_preselects_hyprland_for_new_systems_only(self):
        script = (DISTRO / "system/configure-desktop.sh").read_text()
        self.assertIn('if [[ ! -e "$sddm_state" ]]; then', script)
        self.assertIn("Session=/usr/share/wayland-sessions/hyprland-uwsm.desktop", script)
        self.assertIn('SUDO_UID="$uid" /usr/bin/python3 -I /usr/share/eitr/', script)
        self.assertIn("systemctl enable iwd systemd-networkd systemd-resolved bluetooth sddm", script)
        self.assertNotIn("NOPASSWD", script)

    @unittest.skipIf(os.geteuid() == 0, "Development installer intentionally rejects root")
    def test_optional_node_setup_uses_lts_with_mocked_manager(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            log = home / "calls"
            nvm = home / ".nvm/nvm.sh"
            sdk = home / ".sdkman/bin/sdkman-init.sh"
            binaries = home / "bin"
            nvm.parent.mkdir(parents=True)
            sdk.parent.mkdir(parents=True)
            binaries.mkdir()
            nvm.write_text('nvm() { printf "nvm %s\\n" "$*" >> "$TEST_LOG"; }\n')
            sdk.write_text('sdk() { printf "sdk %s\\n" "$*" >> "$TEST_LOG"; }\n')
            npm = binaries / "npm"
            npm.write_text('#!/bin/bash\nprintf "npm %s\\n" "$*" >> "$TEST_LOG"\n')
            npm.chmod(0o755)
            curl = binaries / "curl"
            curl.write_text('#!/bin/bash\necho "Unexpected network access" >&2\nexit 99\n')
            curl.chmod(0o755)
            env = dict(os.environ, HOME=directory, TEST_LOG=str(log),
                       PATH=str(binaries) + os.pathsep + os.environ["PATH"])
            script = DISTRO.parent / "walker/scripts/actions/install/development.sh"
            subprocess.run(["bash", str(script), "node"],
                           env=env, capture_output=True, text=True, check=True)
            calls = log.read_text()
            self.assertIn("nvm install --lts", calls)
            self.assertIn("nvm alias default lts/*", calls)
            self.assertIn("nvm use default", calls)
            self.assertNotIn("npm install", calls)
            self.assertNotIn("sdk install", calls)
            self.assertFalse((home / ".zshrc").exists())

    @unittest.skipIf(os.geteuid() == 0, "Development installer intentionally rejects root")
    def test_optional_java_installs_the_latest_oracle_lts_with_maven(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            log = home / "calls"
            sdk = home / ".sdkman/bin/sdkman-init.sh"
            binaries = home / "bin"
            sdk.parent.mkdir(parents=True)
            binaries.mkdir()
            listing = ("25.0.1-tem 25.0.2-oracle 25.0.10-oracle 26-oracle 21.0.9-oracle "
                       "25.0.11-graal 25.0.12-tem")
            sdk.write_text('sdk() { if [[ $1 == list ]]; then echo "' + listing + '"; '
                           'else printf "sdk %s\\n" "$*" >> "$TEST_LOG"; fi; }\n')
            curl = binaries / "curl"
            curl.write_text('#!/bin/bash\necho \'{"most_recent_lts": 25}\'\n')
            curl.chmod(0o755)
            env = dict(os.environ, HOME=directory, TEST_LOG=str(log),
                       PATH=str(binaries) + os.pathsep + os.environ["PATH"])
            script = DISTRO.parent / "walker/scripts/actions/install/development.sh"
            subprocess.run(["bash", str(script), "java"], env=env, capture_output=True, text=True, check=True)
            self.assertEqual(log.read_text().splitlines(),
                             ["sdk install java 25.0.10-oracle", "sdk default java 25.0.10-oracle",
                              "sdk install maven"])

    def run_development(self, home, kind):
        log = home / "calls"
        binaries = home / "bin"
        binaries.mkdir(exist_ok=True)
        # The mocked download is an installer that records how it was invoked.
        (binaries / "curl").write_text(
            '#!/bin/bash\nwhile [[ $# -gt 0 ]]; do [[ $1 == -o ]] && out=$2; shift; done\n'
            'printf \'printf "installer %%s UV_NO_MODIFY_PATH=%%s\\\\n" "$*" "${UV_NO_MODIFY_PATH:-}" >> "$TEST_LOG"\\n\' > "$out"\n')
        for name in ("npm", "uv"):
            target = home / ".local/bin" / name if name == "uv" else binaries / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f'#!/bin/bash\nprintf "{name} %s\\n" "$*" >> "$TEST_LOG"\n')
            target.chmod(0o755)
        (binaries / "curl").chmod(0o755)
        nvm = home / ".nvm/nvm.sh"
        nvm.parent.mkdir(parents=True, exist_ok=True)
        nvm.write_text('nvm() { printf "nvm %s\\n" "$*" >> "$TEST_LOG"; }\n')
        env = dict(os.environ, HOME=str(home), TEST_LOG=str(log),
                   PATH=str(binaries) + os.pathsep + os.environ["PATH"])
        script = DISTRO.parent / "walker/scripts/actions/install/development.sh"
        result = subprocess.run(["bash", str(script), kind], env=env, capture_output=True, text=True)
        return result, log.read_text() if log.exists() else ""

    @unittest.skipIf(os.geteuid() == 0, "Development installer intentionally rejects root")
    def test_node_tools_install_nvm_first_on_a_fresh_home(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            binaries = home / "bin"
            binaries.mkdir()
            # Like the real NVM installer: it refuses an NVM_DIR that does not exist.
            installer = ('[[ -d "$NVM_DIR" ]] || { echo "NVM_DIR does not exist" >&2; exit 1; }\n'
                         'printf \'nvm() { printf "nvm %%s\\\\n" "$*" >> "$TEST_LOG"; }\\n\' > "$NVM_DIR/nvm.sh"\n')
            (binaries / "curl").write_text('#!/bin/bash\nwhile [[ $# -gt 0 ]]; do [[ $1 == -o ]] && out=$2; shift; done\n'
                                           f"cat > \"$out\" <<'EOF'\n{installer}EOF\n")
            (binaries / "npm").write_text('#!/bin/bash\nprintf "npm %s\\n" "$*" >> "$TEST_LOG"\n')
            for name in ("curl", "npm"):
                (binaries / name).chmod(0o755)
            log = home / "calls"
            env = dict(os.environ, HOME=str(home), TEST_LOG=str(log), PATH=str(binaries) + os.pathsep + os.environ["PATH"])
            env.pop("NVM_DIR", None)
            script = DISTRO.parent / "walker/scripts/actions/install/development.sh"
            result = subprocess.run(["bash", str(script), "codex"], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = log.read_text()
            self.assertIn("nvm install --lts", calls)
            self.assertIn("npm install --global @openai/codex", calls)

    @unittest.skipIf(os.geteuid() == 0, "Development installer intentionally rejects root")
    def test_development_installers_never_edit_shell_profiles(self):
        expectations = {"python": "UV_NO_MODIFY_PATH=1", "deno": "installer -y --no-modify-path"}
        for kind, expected in expectations.items():
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                result, calls = self.run_development(Path(directory), kind)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected, calls)
        with tempfile.TemporaryDirectory() as directory:
            result, calls = self.run_development(Path(directory), "bun")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("npm install --global bun", calls)
            self.assertNotIn("installer", calls)
        self.assertNotIn("bun", json.loads((DISTRO / "installers.json").read_text()))

    @unittest.skipIf(os.geteuid() == 0, "Development installer intentionally rejects root")
    def test_unknown_development_tool_exits_with_usage_error(self):
        with tempfile.TemporaryDirectory() as directory:
            result, calls = self.run_development(Path(directory), "cobol")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown optional development tool", result.stderr)
        self.assertEqual(calls, "")

    def test_gnome_videos_launcher_uses_scoped_graphics_fix(self):
        root = DISTRO.parent
        launcher = configparser.ConfigParser(interpolation=None)
        launcher.read(root / "distro/defaults/home/.local/share/applications/org.gnome.Totem.desktop")
        self.assertEqual(launcher["Desktop Entry"]["Exec"], "env GDK_GL=gles totem %U")
        self.assertFalse(launcher["Desktop Entry"].getboolean("DBusActivatable"))
        associations = configparser.ConfigParser(interpolation=None)
        associations.read(root / "mimeapps.list")
        self.assertEqual(associations["Default Applications"]["video/mp4"], "org.gnome.Totem.desktop")

    def test_mpv_is_not_installed(self):
        packages = (DISTRO / "packages.txt").read_text().splitlines()
        self.assertNotIn("mpv", packages)

    def test_common_media_backends_and_steam_are_explicit(self):
        packages = set()
        for filename in ("packages.txt", "apps.txt"):
            packages.update(line.strip() for line in (DISTRO / filename).read_text().splitlines()
                            if line.strip() and not line.startswith("#"))
        required = {"ffmpeg", "qt6-multimedia-ffmpeg", "gstreamer", "gst-libav",
                    "gst-plugins-base", "gst-plugins-good", "gst-plugins-bad",
                    "gst-plugins-ugly", "gst-plugin-pipewire", "steam"}
        self.assertFalse(required - packages, f"Missing packages: {required - packages}")


class RetiredNotificationServiceTests(unittest.TestCase):
    def test_swaync_activation_shadow_is_not_shipped(self):
        root = Path(__file__).resolve().parents[2]
        self.assertFalse((root / 'HOME_FILES/.local/share/dbus-1/services/org.erikreider.swaync.service').exists())
        self.assertNotIn('org.erikreider.swaync.service', (root / 'distro/legacy-layout.json').read_text())


if __name__ == "__main__":
    unittest.main()
