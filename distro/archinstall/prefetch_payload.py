"""Warm the offline packages while the installer collects its choices."""
from contextlib import contextmanager, suppress
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

RESERVE = 2 * 1024 ** 3
BLOCK = 1024 ** 2


def memory_available():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    return 0


def base_files(pool, manifest):
    """Resolve the base transaction against the offline databases and an empty local DB."""
    targets = next(line.split() for line in manifest.read_text().splitlines()
                   if line.strip() and not line.lstrip().startswith("#"))
    with tempfile.TemporaryDirectory(prefix="eitr-prefetch-") as directory:
        root = Path(directory)
        sync = root / "sync"
        sync.mkdir()
        conf = root / "pacman.conf"
        repos = ["core", "extra", "multilib"]
        conf.write_text("[options]\nArchitecture = auto\nSigLevel = Required DatabaseOptional\n" + "".join(
            f"[{repo}]\nServer = file://{pool}\n" for repo in repos))
        for repo in repos:
            (sync / f"{repo}.db").symlink_to(pool / f"{repo}.db")
        names = subprocess.check_output(
            ["pacman", "--config", conf, "--dbpath", root, "-Sp", "--noconfirm", "--print-format", "%f", *targets],
            text=True, stderr=subprocess.DEVNULL).splitlines()
    return {pool / name for name in names}


def prefetch(root, manifest):
    budget = memory_available() - RESERVE
    if budget <= 0:
        return
    pool = root / "pool"
    files = {path: path.stat().st_size for directory in (pool, root / "repo")
             for path in directory.glob("*.pkg.tar.*") if not path.is_symlink()}
    if sum(files.values()) > budget:
        base = base_files(pool, manifest)
        files = {path: size for path, size in files.items()
                 if path in base or path.with_suffix("") in base}
    for path, size in sorted(files.items()):
        if size > budget:
            continue
        with path.open("rb") as handle:
            remaining = size
            while remaining:
                if memory_available() < RESERVE + BLOCK:
                    return
                block = handle.read(min(remaining, BLOCK))
                if not block:
                    break
                remaining -= len(block)
                budget -= len(block)


@contextmanager
def warming_payload(root, manifest):
    worker = None
    try:
        with suppress(OSError):
            worker = subprocess.Popen(
                ["ionice", "-c", "3", "nice", "-n", "19", sys.executable, __file__, root, manifest],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True)
        yield
    finally:
        if worker is not None:
            with suppress(OSError):
                os.killpg(worker.pid, signal.SIGTERM)
            try:
                worker.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                with suppress(OSError):
                    os.killpg(worker.pid, signal.SIGKILL)


if __name__ == "__main__":
    with suppress(OSError, ValueError, StopIteration, subprocess.SubprocessError):
        prefetch(Path(sys.argv[1]), Path(sys.argv[2]))
