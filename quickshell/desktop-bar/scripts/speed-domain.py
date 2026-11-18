"""On-demand disk and network speed tests for Control Center."""
import mmap
import os
from pathlib import Path
import statistics
import tempfile
import threading
import time
import urllib.error
import urllib.request

DEFAULT_DISK_BYTES = 256 * 1024 * 1024
DEFAULT_DOWNLOAD_BYTES = 25 * 1000 * 1000
DEFAULT_UPLOAD_BYTES = 10 * 1000 * 1000
CHUNK_SIZE = 1024 * 1024
READ_CHUNK = 65536
DEFAULT_BASE_URL = "https://speed.cloudflare.com"


def cache_directory(cache_home=None):
    base = cache_home or os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    target = Path(base) / "eitr"
    target.mkdir(parents=True, exist_ok=True)
    return target


def check_limits(deadline, cancelled):
    if cancelled is not None and cancelled.is_set():
        raise InterruptedError("cancelled")
    if time.monotonic() >= deadline:
        raise TimeoutError("speed-timeout")


class SpeedDomain:
    def __init__(self, cache_home=None, base_url=DEFAULT_BASE_URL):
        self.cache_home = cache_home
        self.base_url = base_url.rstrip("/")

    def run_disk(self, total_bytes, deadline, cancelled):
        target_dir = cache_directory(self.cache_home)
        chunk = os.urandom(min(CHUNK_SIZE, total_bytes))
        fd, raw_path = tempfile.mkstemp(prefix="eitr-speed-", suffix=".tmp", dir=str(target_dir))
        path = Path(raw_path)
        started = time.monotonic()
        try:
            written = 0
            write_start = time.monotonic()
            try:
                while written < total_bytes:
                    check_limits(deadline, cancelled)
                    to_write = min(len(chunk), total_bytes - written)
                    view = memoryview(chunk)[:to_write]
                    offset = 0
                    while offset < to_write:
                        n = os.write(fd, view[offset:])
                        if n <= 0:
                            raise OSError("short-write")
                        offset += n
                    written += to_write
                os.fsync(fd)
            finally:
                os.close(fd)
            write_elapsed = max(0.001, time.monotonic() - write_start)

            # Drop page cache / prefer direct I/O for the sequential read pass.
            read_fd = None
            direct = False
            o_direct = getattr(os, "O_DIRECT", 0)
            if o_direct:
                try:
                    read_fd = os.open(path, os.O_RDONLY | o_direct)
                    direct = True
                except OSError:
                    read_fd = None
            if read_fd is None:
                read_fd = os.open(path, os.O_RDONLY)
                if hasattr(os, "posix_fadvise") and hasattr(os, "POSIX_FADV_DONTNEED"):
                    try:
                        os.posix_fadvise(read_fd, 0, total_bytes, os.POSIX_FADV_DONTNEED)
                    except OSError:
                        pass

            read_start = time.monotonic()
            buf = mmap.mmap(-1, CHUNK_SIZE) if direct else None
            try:
                remaining = total_bytes
                while remaining > 0:
                    check_limits(deadline, cancelled)
                    if direct and buf is not None:
                        try:
                            n = os.readv(read_fd, [buf])
                        except OSError:
                            # Fallback if filesystem rejects unaligned tail or O_DIRECT.
                            os.close(read_fd)
                            read_fd = os.open(path, os.O_RDONLY)
                            os.lseek(read_fd, total_bytes - remaining, os.SEEK_SET)
                            direct = False
                            continue
                        if n <= 0:
                            break
                        remaining -= min(n, remaining)
                    else:
                        data = os.read(read_fd, min(CHUNK_SIZE, remaining))
                        if not data:
                            break
                        remaining -= len(data)
            finally:
                if buf is not None:
                    buf.close()
                os.close(read_fd)
            read_elapsed = max(0.001, time.monotonic() - read_start)
            return {
                "kind": "disk",
                "writeMBps": round(total_bytes / 1_000_000 / write_elapsed, 1),
                "readMBps": round(total_bytes / 1_000_000 / read_elapsed, 1),
                "bytes": total_bytes,
                "durationMs": int((time.monotonic() - started) * 1000),
            }
        finally:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    def _open(self, url, deadline, data=None, method="GET"):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("speed-timeout")
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={"User-Agent": "Eitr-SpeedTest/1.0"},
        )
        return urllib.request.urlopen(request, timeout=min(15.0, remaining))

    def run_network(self, download_bytes, upload_bytes, deadline, cancelled):
        rtts = []
        for _ in range(3):
            check_limits(deadline, cancelled)
            probe_start = time.monotonic()
            with self._open(f"{self.base_url}/__down?bytes=0", deadline) as response:
                response.read()
            rtts.append((time.monotonic() - probe_start) * 1000.0)
        latency_ms = round(statistics.median(rtts), 1)

        check_limits(deadline, cancelled)
        dl_start = time.monotonic()
        dl_received = 0
        with self._open(f"{self.base_url}/__down?bytes={download_bytes}", deadline) as response:
            while True:
                check_limits(deadline, cancelled)
                chunk = response.read(READ_CHUNK)
                if not chunk:
                    break
                dl_received += len(chunk)
        dl_elapsed = max(0.001, time.monotonic() - dl_start)
        download_mbps = round((dl_received * 8) / 1_000_000 / dl_elapsed, 1)

        check_limits(deadline, cancelled)
        payload = b"0" * upload_bytes
        ul_start = time.monotonic()
        with self._open(f"{self.base_url}/__up", deadline, data=payload, method="POST") as response:
            response.read()
        ul_elapsed = max(0.001, time.monotonic() - ul_start)
        upload_mbps = round((upload_bytes * 8) / 1_000_000 / ul_elapsed, 1)

        return {
            "kind": "network",
            "latencyMs": latency_ms,
            "downloadMbps": download_mbps,
            "uploadMbps": upload_mbps,
            "service": self.base_url.replace("https://", "").replace("http://", ""),
        }

    def query(self, name, args, deadline, cancelled=None):
        if name == "disk":
            size = int(args.get("bytes") or DEFAULT_DISK_BYTES)
            size = max(1024 * 1024, min(DEFAULT_DISK_BYTES, size))
            return self.run_disk(size, deadline, cancelled)
        if name == "network":
            dl = int(args.get("downloadBytes") or DEFAULT_DOWNLOAD_BYTES)
            ul = int(args.get("uploadBytes") or DEFAULT_UPLOAD_BYTES)
            dl = max(1024, min(DEFAULT_DOWNLOAD_BYTES, dl))
            ul = max(1024, min(DEFAULT_UPLOAD_BYTES, ul))
            return self.run_network(dl, ul, deadline, cancelled)
        raise ValueError("invalid-speed-test")
