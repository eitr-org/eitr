from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
DISTRO = ROOT / "distro"
SCANNED = ("hypr", "walker", "quickshell", "elephant", "HOME_FILES", "systemd")
SUFFIXES = {"", ".sh", ".py", ".lua", ".qml", ".js", ".toml", ".desktop", ".service", ".zsh"}
# External commands with distinctive names, mapped to the package providing them.
COMMAND_PACKAGES = {
    "playerctl": "playerctl", "jq": "jq", "fzf": "fzf", "wl-copy": "wl-clipboard",
    "wl-paste": "wl-clipboard", "grim": "grim", "slurp": "slurp",
    "brightnessctl": "brightnessctl", "wpctl": "wireplumber", "openrgb": "openrgb",
    "obs-cmd": "obs-cmd", "notify-send": "libnotify", "satty": "satty",
    "tesseract": "tesseract", "zbarimg": "zbar", "qrencode": "qrencode",
    "cliphist": "cliphist", "magick": "imagemagick", "ffmpeg": "ffmpeg",
    "ddcutil": "ddcutil", "sensors": "lm_sensors", "iwctl": "iwd",
    "swayosd-client": "swayosd", "hyprsunset": "hyprsunset", "hyprpicker": "hyprpicker",
    "hyprctl": "hyprland", "wtype": "wtype", "xdg-open": "xdg-utils", "btop": "btop",
    "impala": "impala", "flatpak": "flatpak",
    "snapper": "snapper", "imv": "imv", "totem": "totem", "rg": "ripgrep", "eza": "eza",
    "fprintd-enroll": "fprintd", "pamu2fcfg": "pam-u2f", "rsync": "rsync", "curl": "curl",
    "powerprofilesctl": "power-profiles-daemon",
    "rfkill": "util-linux", "nmcli": "networkmanager",
}


def manifest_packages():
    files = [DISTRO / name for name in ("packages.txt", "apps.txt", "aur-packages.txt", "aur-apps.txt")]
    files += sorted((DISTRO / "hardware").glob("*.txt"))
    packages = set()
    for path in files:
        packages.update(line.strip() for line in path.read_text().splitlines()
                        if line.strip() and not line.lstrip().startswith("#"))
    return packages


def scanned_text():
    for directory in SCANNED:
        for path in (ROOT / directory).rglob("*"):
            if (path.is_file() and not path.is_symlink() and path.suffix in SUFFIXES
                    and "tests" not in path.parts and "__pycache__" not in path.parts):
                yield path, path.read_text(errors="ignore")


class CommandPackageTests(unittest.TestCase):
    def test_used_commands_have_manifest_packages(self):
        packages = manifest_packages()
        patterns = {command: re.compile(r"(?<![\w./-])" + re.escape(command) + r"(?![\w.-])")
                    for command in COMMAND_PACKAGES}
        missing = {}
        for path, text in scanned_text():
            for command, pattern in patterns.items():
                package = COMMAND_PACKAGES[command]
                if package not in packages and pattern.search(text):
                    missing.setdefault(f"{command} ({package})", path.relative_to(ROOT).as_posix())
        self.assertEqual(missing, {}, "Commands used without a manifest package")


if __name__ == "__main__":
    unittest.main()
