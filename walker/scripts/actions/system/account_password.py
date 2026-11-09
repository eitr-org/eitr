#!/usr/bin/env python3
"""Change the signed-in user's password and keep the login keyring opening with it.

passwd does the change, so the system's PAM rules decide what is accepted. SDDM
unlocks the GNOME login keyring with the login password, but passwd's PAM stack does
not touch the keyring, so the keyring is re-keyed from the old to the new password
afterwards through gnome-keyring's own D-Bus call (the one Seahorse uses).

Settings runs `account_password.py` and writes {"current": ..., "new": ...} on stdin;
it answers one JSON line. Passwords never appear in arguments, files or logs.
"""
import json
import os
import pty
import re
import select
import signal
import sys
import time

# passwd's prompts, as printed with LC_ALL=C; checked against the end of the output.
PROMPT_CURRENT = re.compile(rb"(?:Current password|\(current\) UNIX password):$")
PROMPT_RETYPE = re.compile(rb"Retype new password:$")
PROMPT_NEW = re.compile(rb"(?<!Retype )New password:$")
SUCCESS = re.compile(rb"password updated successfully", re.I)
WRONG_CURRENT = re.compile(rb"Authentication token manipulation error|Authentication failure", re.I)
TIMEOUT = 30


def _read(descriptor, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError
    ready, _, _ = select.select([descriptor], [], [], remaining)
    if not ready:
        raise TimeoutError
    try:
        return os.read(descriptor, 4096)
    except OSError:
        return b""


def _rejection(transcript):
    """The PAM message passwd printed before asking again, without its prompts."""
    lines = [line.strip() for line in transcript.decode(errors="replace").splitlines()]
    lines = [line for line in lines if line and not re.search(r"password:\s*$", line, re.I)
             and not line.lower().startswith("changing password")]
    return lines[-1].removeprefix("BAD PASSWORD:").strip() if lines else ""


def run_passwd(current, new, command=("passwd",)):
    """Drive passwd on a terminal; returns (status, detail).

    status is "changed", "wrong-current", "rejected" (detail is PAM's reason) or "failed".
    """
    process, descriptor = pty.fork()
    if process == 0:
        environment = dict(os.environ, LC_ALL="C", LANG="C", LANGUAGE="C")
        try:
            os.execvpe(command[0], list(command), environment)
        finally:
            os._exit(127)
    deadline = time.monotonic() + TIMEOUT
    pending, transcript = b"", b""
    sent_current = sent_new = sent_retype = False
    status, detail = "failed", ""
    try:
        while True:
            chunk = _read(descriptor, deadline)
            if not chunk:
                break
            pending += chunk
            transcript += chunk
            if SUCCESS.search(transcript):
                status = "changed"
                continue
            if WRONG_CURRENT.search(transcript) and not sent_new:
                status = "wrong-current"
                continue
            tail = pending.rstrip()
            if PROMPT_RETYPE.search(tail):
                if sent_retype:
                    status, detail = "rejected", _rejection(transcript)
                    break
                os.write(descriptor, new.encode() + b"\n")
                sent_retype, pending = True, b""
            elif PROMPT_NEW.search(tail):
                if sent_new:
                    # Asked again: PAM refused the new password and wants another.
                    status, detail = "rejected", _rejection(transcript)
                    break
                os.write(descriptor, new.encode() + b"\n")
                sent_new, pending = True, b""
            elif PROMPT_CURRENT.search(tail):
                if sent_current:
                    status = "wrong-current"
                    break
                os.write(descriptor, current.encode() + b"\n")
                sent_current, pending = True, b""
    except TimeoutError:
        status = "failed"
    finally:
        # passwd ignores SIGTERM while it waits at a prompt, so a stop is a hang-up and a kill.
        os.close(descriptor)
        finished, exit_status = os.waitpid(process, os.WNOHANG)
        if not finished:
            time.sleep(0.2)
            finished, exit_status = os.waitpid(process, os.WNOHANG)
        if not finished:
            os.kill(process, signal.SIGKILL)
            _, exit_status = os.waitpid(process, 0)
    if status == "changed" and os.waitstatus_to_exitcode(exit_status) != 0:
        status = "failed"
    if status == "failed" and not detail and transcript:
        detail = _rejection(transcript)
    return status, detail


def _secrets():
    """A session-bus caller for the Secret Service, or None without GObject or a bus."""
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

    def call(path, interface, method, parameters, reply):
        return bus.call_sync("org.freedesktop.secrets", path, interface, method, parameters,
                             GLib.VariantType(reply), Gio.DBusCallFlags.NONE, 10000, None).unpack()
    return call, GLib


def rekey_collection(collection, old, new):
    """Change one keyring's password from old to new; raises when the keyring refuses."""
    call, GLib = _secrets()
    service = "/org/freedesktop/secrets"
    _, session = call(service, "org.freedesktop.Secret.Service", "OpenSession",
                      GLib.Variant("(sv)", ("plain", GLib.Variant("s", ""))), "(vo)")
    try:
        secret = lambda value: (session, b"", value.encode(), "text/plain")
        call(service, "org.gnome.keyring.InternalUnsupportedGuiltRiddenInterface", "ChangeWithMasterPassword",
             GLib.Variant("(o(oayays)(oayays))", (collection, secret(old), secret(new))), "()")
    finally:
        call(session, "org.freedesktop.Secret.Session", "Close", None, "()")


def change_keyring(old, new):
    """Re-key the login keyring; returns "changed", "absent" or "kept"."""
    try:
        call, GLib = _secrets()
        collection, = call("/org/freedesktop/secrets", "org.freedesktop.Secret.Service", "ReadAlias",
                           GLib.Variant("(s)", ("login",)), "(o)")
    except Exception:  # noqa: BLE001 - no session bus or no keyring service: nothing to keep in step
        return "absent"
    if collection == "/":
        return "absent"
    try:
        rekey_collection(collection, old, new)
        return "changed"
    except Exception:  # noqa: BLE001 - a refused change leaves the keyring as it was
        return "kept"


def change_password(current, new):
    """The whole change: passwd first, then the keyring only when passwd succeeded."""
    status, detail = run_passwd(current, new)
    result = {"status": status, "detail": detail}
    if status == "changed":
        result["keyring"] = change_keyring(current, new)
    return result


def main():
    try:
        request = json.loads(sys.stdin.readline())
        current, new = request["current"], request["new"]
        if not isinstance(current, str) or not isinstance(new, str) or not new or "\n" in current + new:
            raise ValueError
    except (ValueError, KeyError, TypeError):
        print(json.dumps({"status": "failed", "detail": "invalid request"}))
        return 1
    result = change_password(current, new)
    print(json.dumps(result))
    return 0 if result["status"] == "changed" else 1


if __name__ == "__main__":
    sys.exit(main())
