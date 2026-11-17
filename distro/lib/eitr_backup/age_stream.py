"""PTY-backed age encryption/decryption pipeline and subprocess lifecycle helpers."""
import fcntl
import os
import pty
import selectors
import shutil
import subprocess
import termios
import threading

from eitr_backup import BackupError, PassphraseError
from eitr_i18n import tr


def require_tool(name):
    binary = shutil.which(name)
    if not binary:
        raise BackupError(tr("Required tool '{tool}' is not installed.", tool=name))
    return binary


def _drive_pty(master_fd, slave_fd, proc, responses, error_holder):
    selector = selectors.DefaultSelector()
    selector.register(master_fd, selectors.EVENT_READ)
    buf = bytearray()
    index = 0
    try:
        while True:
            events = selector.select(timeout=0.05)
            if events:
                try:
                    chunk = os.read(master_fd, 4096)
                except OSError:
                    chunk = b""
                if chunk:
                    buf.extend(chunk)
                    if index < len(responses) and b":" in buf:
                        try:
                            os.write(master_fd, responses[index].encode("utf-8") + b"\n")
                        except OSError:
                            break
                        index += 1
                        buf.clear()
                elif proc.poll() is not None:
                    break
            elif proc.poll() is not None:
                break
    except Exception as exc:
        error_holder.append(exc)
    finally:
        selector.close()
        os.close(master_fd)
        os.close(slave_fd)


def spawn_age(args, responses, *, stdin=subprocess.PIPE, stdout=subprocess.PIPE):
    age_bin = require_tool("age")
    master_fd, slave_fd = pty.openpty()
    attrs = termios.tcgetattr(slave_fd)
    attrs[3] &= ~termios.ECHO
    termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)

    def attach_tty():
        os.umask(0o077)
        os.setsid()
        fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)
        os.close(slave_fd)

    try:
        proc = subprocess.Popen(
            [age_bin, *args],
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.PIPE,
            pass_fds=(slave_fd,),
            preexec_fn=attach_tty,
        )
    except Exception:
        os.close(master_fd)
        os.close(slave_fd)
        raise

    errors = []
    driver = threading.Thread(target=_drive_pty, args=(master_fd, slave_fd, proc, responses, errors), daemon=True)
    driver.start()
    return proc, driver, errors


def format_age_error(stderr_text, *, for_decrypt=False):
    msg = (stderr_text or "").strip()
    lower = msg.casefold()
    if for_decrypt and ("incorrect passphrase" in lower or "no identity matched" in lower or "bad decrypt" in lower):
        return PassphraseError(tr("Incorrect passphrase for backup archive."))
    return BackupError(msg or tr("Encryption helper failed."))


def stop_procs_early(procs):
    for proc in procs:
        if not proc:
            continue
        for pipe in (proc.stdin, proc.stdout, proc.stderr):
            if pipe and not pipe.closed:
                try:
                    pipe.close()
                except OSError:
                    pass
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=1)


def open_decrypt_pipeline(archive_path, passphrase):
    """Spawn age -d | zstd -d and return (age_proc, zstd_proc, driver, pty_errors)."""
    zstd_bin = require_tool("zstd")
    age_proc, driver, pty_errors = spawn_age(["-d", str(archive_path)], [passphrase], stdin=subprocess.DEVNULL)
    try:
        zstd_proc = subprocess.Popen(
            [zstd_bin, "-d", "-c"],
            stdin=age_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception:
        stop_procs_early((age_proc,))
        driver.join(timeout=1)
        raise
    age_proc.stdout.close()
    return age_proc, zstd_proc, driver, pty_errors
