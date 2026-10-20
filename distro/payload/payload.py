"""Shared definitions of Eitr's offline installation payload.

The payload is a directory on the ISO medium:

  pool/    official Arch packages with their .sig files, plus the core, extra
           and multilib sync databases they were downloaded with
  repo/    the unsigned `eitr` repository: prebuilt AUR packages, yay and
           eitr-desktop, with its own database
  assets/  pinned Git checkouts the desktop setup unpacks (Oh My Zsh, ...)
  manifest.json, SHA256SUMS   provenance and checksums of every file

Official packages keep Arch's signatures; pacman verifies them against the
archlinux-keyring of the same snapshot. The eitr repository database records
each package's SHA-256, which pacman checks on installation.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
DISTRO = ROOT / "distro"
OFFICIAL_REPOS = ("core", "extra", "multilib")
LOCAL_REPO = "eitr"
DESKTOP = "@desktop"
SHELL_ASSETS = {
    "oh-my-zsh": "https://github.com/ohmyzsh/ohmyzsh.git",
    "powerlevel10k": "https://github.com/romkatv/powerlevel10k.git",
}


def manifest(path):
    """Package names from a manifest: one per line, # comments ignored."""
    names = []
    for line in Path(path).read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.append(line)
    return names


def desktop_official(root=ROOT):
    distro = root / "distro"
    return manifest(distro / "packages.txt") + manifest(distro / "apps.txt")


def desktop_aur(root=ROOT):
    distro = root / "distro"
    return manifest(distro / "aur-packages.txt") + manifest(distro / "aur-apps.txt")


def desktop_local(root=ROOT):
    packages = manifest(root / "distro/local-packages.txt")
    # The keyring exists once the EITR signing key does (distro/REPOSITORY.md).
    return [*packages, "eitr-keyring"] if signing_key(root) else packages


def signing_key(root=ROOT):
    """The EITR package-signing key's fingerprint, or None before the key exists."""
    path = Path(root) / "distro/keys/eitr.fingerprint"
    if not path.is_file() or not (Path(root) / "distro/keys/eitr.asc").is_file():
        return None
    fingerprint = path.read_text().strip()
    if not re.fullmatch(r"[0-9A-F]{40}", fingerprint):
        raise ValueError(f"Invalid fingerprint in {path}")
    return fingerprint


ONLINE_REPOSITORY = "https://download.eitr.info/repo"


def eitr_repository():
    """The signed [eitr] section installed systems use for EITR updates."""
    return (f"\n[{LOCAL_REPO}]\n"
            "# Signed EITR packages; the key comes from the eitr-keyring package.\n"
            "SigLevel = Required\n"
            f"Server = {ONLINE_REPOSITORY}\n")


def hardware_manifests(root=ROOT):
    return sorted((root / "distro/hardware").glob("*.txt"))


def transactions(root=ROOT):
    """Every package transaction the payload must satisfy, in install order."""
    result = []
    for line in (root / "distro/payload/transactions.txt").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if line != DESKTOP:
            result.append(line.split())
            continue
        desktop = desktop_official(root) + desktop_aur(root) + desktop_local(root) + ["eitr-desktop"]
        result.append(desktop)
        result.extend(desktop + manifest(path) for path in hardware_manifests(root))
    return result


def dependency_name(dependency):
    """`python-clickgen>=2.0.0` -> `python-clickgen`; `libgtk-3.so=0` -> `libgtk-3.so`."""
    return re.split(r"[<>=]", dependency, maxsplit=1)[0].strip()


def package_file_name(path):
    """`elephant-menus-bin-2.22.1-1-x86_64.pkg.tar.zst` -> `elephant-menus-bin`."""
    return Path(path).name.split(".pkg.tar")[0].rsplit("-", 3)[0]


def build_order(graph):
    """Topological order of {name: dependencies}; dependencies outside the graph
    are ignored. Raises ValueError on a cycle."""
    order, state = [], {}

    def visit(name, path):
        if state.get(name) == "done":
            return
        if state.get(name) == "visiting":
            raise ValueError("AUR dependency cycle: " + " -> ".join([*path, name]))
        state[name] = "visiting"
        for dependency in sorted(graph[name]):
            if dependency in graph:
                visit(dependency, [*path, name])
        state[name] = "done"
        order.append(name)

    for name in sorted(graph):
        visit(name, [])
    return order


def pacman_conf(pool, repo):
    """pacman.conf that installs only from the payload directories."""
    sections = "".join(f"\n[{name}]\nServer = file://{pool}\n" for name in OFFICIAL_REPOS)
    return ("# Offline Eitr installation payload; replaced on the installed system.\n"
            "[options]\n"
            "HoldPkg = pacman glibc\n"
            "Architecture = auto\n"
            "ParallelDownloads = 5\n"
            "SigLevel = Required DatabaseOptional\n"
            "LocalFileSigLevel = Optional\n"
            f"{sections}"
            f"\n[{LOCAL_REPO}]\n"
            "# Built by distro/payload/build-payload.py; the database pins each SHA-256.\n"
            "SigLevel = Optional TrustAll\n"
            f"Server = file://{repo}\n")


def online_pacman_conf(default):
    """The pacman package's default pacman.conf with [multilib] enabled."""
    lines = default.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if re.fullmatch(r"#\s*\[multilib\]\s*", line):
            lines[index] = "[multilib]\n"
            if index + 1 < len(lines) and re.fullmatch(r"#\s*Include\s*=.*\s*", lines[index + 1]):
                lines[index + 1] = lines[index + 1].lstrip("#").lstrip()
    result = "".join(lines)
    if not re.search(r"^\[multilib\]$", result, re.M):
        raise ValueError("The default pacman.conf has no [multilib] section to enable")
    return result
