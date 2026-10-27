#!/usr/bin/env python3
"""Collect a private, redacted diagnostic report for a problem. Nothing is
uploaded: the user reads it, then may open it in their email app, open a GitHub
issue in the browser, or copy it."""
import eitr_bootstrap
from eitr_app import app_command
from eitr_i18n import mark, tr
import argparse
import getpass
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
from urllib.parse import quote, urlencode

REPORTS_EMAIL = "reports@eitr.info"
NEW_ISSUE = "https://github.com/eitr-org/eitr/issues/new"
# Mail apps and GitHub cut long links; the full report stays in the saved file.
SUMMARY_LIMIT = 1800

PACKAGES = ("eitr-desktop", "hyprland", "quickshell", "walker", "elephant", "linux", "mesa",
            "nvidia-open", "nvidia-utils", "sddm", "pipewire", "iwd", "networkmanager")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
MAC = re.compile(r"\b(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\b")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# Full eight-group or "::"-compressed addresses only, so clock times stay readable.
IPV6 = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
                  r"|\b[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4})*::(?:[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4})*)?")


def redact(text, user=None, host=None, home=None):
    """Remove what identifies the person or machine; keep what explains the problem."""
    user = user if user is not None else getpass.getuser()
    host = host if host is not None else socket.gethostname()
    home = home if home is not None else str(Path.home())
    text = text.replace(home, "~")
    text = EMAIL.sub("<email>", text)
    text = MAC.sub("<mac>", text)
    text = IPV6.sub("<ip>", text)
    text = IPV4.sub("<ip>", text)
    for value, label in ((host, "<host>"), (user, "<user>")):
        if len(value) >= 3:
            text = re.sub(rf"(?<![\w-]){re.escape(value)}(?![\w-])", label, text)
    return text


def command(title, arguments, limit=200, keep_start=False):
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=20, check=False)
        output = (result.stdout + result.stderr).strip() or "(no output)"
    except (OSError, subprocess.SubprocessError) as error:
        output = f"(unavailable: {error})"
    lines = output.splitlines()
    if len(lines) > limit:
        lines = lines[:limit] if keep_start else lines[-limit:]
    return f"## {title}\n" + "\n".join(lines) + "\n"


def file_tail(title, path, limit=60):
    path = Path(path)
    lines = path.read_text(errors="replace").splitlines()[-limit:] if path.is_file() else ["(none)"]
    return f"## {title}\n" + "\n".join(lines) + "\n"


def latest_file(title, pattern_directory, pattern, limit=80):
    files = sorted(Path(pattern_directory).glob(pattern), key=lambda path: path.stat().st_mtime)
    return file_tail(title, files[-1], limit) if files else f"## {title}\n(none)\n"


def collect():
    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    cache = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    version = Path("/usr/share/eitr/version")
    release = Path("/usr/share/eitr/release.json")
    from eitr_selfcheck import collect as selfcheck_collect, plain as selfcheck_plain, summary as selfcheck_summary
    checks = selfcheck_collect()
    sections = [
        "# EITR problem report",
        f"Created: {time.strftime('%Y-%m-%d %H:%M %Z')}",
        f"EITR version: {version.read_text().strip() if version.is_file() else 'not installed from the package'}",
        f"Release: {' '.join(release.read_text().split()) if release.is_file() else 'unknown'}",
        f"Layout adopted: {(state / 'eitr/layout.json').is_file()}",
        "",
        "## Self-check summary\n" + selfcheck_summary(checks) + "\n\n" + selfcheck_plain(checks),
        command("Kernel", ["uname", "-srm"]),
        command("Packages", ["pacman", "-Q", *PACKAGES]),
        command("Graphics", ["sh", "-c", "lspci -nnk | grep -A3 -Ei 'vga|3d|display'"]),
        command("Hyprland version", ["sh", "-c", "hyprctl version | head -3"]),
        command("Hyprland config errors", ["hyprctl", "configerrors"]),
        command("Failed user services", ["systemctl", "--user", "--failed", "--no-legend"]),
        command("Recent warnings (user journal, this boot)",
                ["journalctl", "--user", "-b", "-p", "warning", "--no-pager", "-o", "short-monotonic"]),
        command("Settings status", ["eitr-config", "status"]),
        file_tail("Settings migrations", state / "eitr/migrations.log"),
        command("Crashes (last 7 days)", ["coredumpctl", "--no-pager", "list", "--since=-7d"], limit=30),
        command("Latest crash", ["coredumpctl", "--no-pager", "info", "--since=-7d"], limit=80, keep_start=True),
        latest_file("Latest Hyprland crash report", cache / "hyprland", "hyprlandCrashReport*.txt"),
        command("Errors (user journal, previous boot)",
                ["journalctl", "--user", "-b", "-1", "-p", "err", "--no-pager", "-o", "short-monotonic"], limit=80),
        file_tail("Installation", "/var/log/eitr-install.log", limit=40),
        command("Recent package changes", ["sh", "-c", "grep -E '\\] (upgraded|installed|removed) ' /var/log/pacman.log | tail -n 30"]),
    ]
    return "\n".join(sections)


def summary(report):
    """The start of the report, short enough for an email or issue link."""
    head = "\n".join(line for line in report.splitlines()[:40])
    crashes = report.split("## Crashes (last 7 days)\n", 1)[1].split("\n## ", 1)[0] if "## Crashes (last 7 days)\n" in report else ""
    text = head + ("\n\n## Crashes (last 7 days)\n" + crashes if crashes.strip() else "")
    return text[:SUMMARY_LIMIT].rstrip() + "\n\n(Shortened. Please attach the saved report file.)"


def email_link(report, path):
    body = (f"What happened, and what were you doing?\n\n\n"
            f"--- Please attach {path.name} from your Documents folder. ---\n\n{summary(report)}")
    return f"mailto:{REPORTS_EMAIL}?subject={quote('Eitr problem report')}&body={quote(body)}"


def issue_link(report):
    body = ("**What happened, and what were you doing?**\n\n\n"
            "**Report** (drag the saved report file here to attach it in full):\n\n"
            f"```\n{summary(report)}\n```\n")
    return f"{NEW_ISSUE}?{urlencode({'title': 'Problem: ', 'body': body})}"


def open_link(link):
    try:
        subprocess.run(app_command(["xdg-open", link]), check=True, timeout=20,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def copy(report):
    if not shutil.which("wl-copy"):
        return False
    subprocess.run(["wl-copy"], input=report, text=True, check=False)
    return True


CHOICES = mark("""
How do you want to send it?
  1  Email it to {email} (opens your email app; attach the saved file)
  2  Open a GitHub issue (needs a GitHub account; issues are public)
  3  Copy the report, to paste anywhere
  4  Read the report (opens it in your text editor)
  Enter  Done; the report stays saved
""")


def send(report, path):
    """Offer the ways to send the report until the user is done."""
    while True:
        try:
            answer = input(tr(CHOICES, email=REPORTS_EMAIL) + "> ").strip()
        except EOFError:
            return
        if answer == "":
            return
        if answer == "1":
            if open_link(email_link(report, path)):
                print(tr('Your email app opened a message to {REPORTS_EMAIL}. Attach {path}, add what happened, and send.', REPORTS_EMAIL=f'{REPORTS_EMAIL}', path=f'{path}'))
            else:
                print(tr('No email app opened. Write to {REPORTS_EMAIL} from your webmail and attach {path}.', REPORTS_EMAIL=f'{REPORTS_EMAIL}', path=f'{path}'))
        elif answer == "2":
            if open_link(issue_link(report)):
                print(tr('The browser opened a new GitHub issue. Describe what happened and attach {path}.', path=f'{path}'))
            else:
                print(tr('No browser opened. Go to {NEW_ISSUE} and attach {path}.', NEW_ISSUE=f'{NEW_ISSUE}', path=f'{path}'))
        elif answer == "3":
            print(tr("Copied the report.") if copy(report) else tr("Copying needs wl-copy; open the saved file instead."))
        elif answer == "4":
            print(tr("The report opened in your text editor.") if open_link(path.as_uri()) else tr("Open {path} to read it.", path=path))
        else:
            print(tr('Type 1, 2, 3 or 4, or press Enter.'))


PRIVACY = mark("""
About sending it: the report is used only to find and fix this problem, and it
is deleted once the problem is fixed. An email also shares your email address;
reply to it anytime to have your report deleted. A GitHub issue is public.
""")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crash-summary", default="")
    options = parser.parse_args()
    report = redact(("## " + tr("Crash summary") + "\n" + options.crash_summary[:32000] + "\n\n" if options.crash_summary else "") + collect())
    directory = Path.home() / "Documents"
    directory.mkdir(exist_ok=True)
    path = directory / f"eitr-problem-report-{time.strftime('%Y%m%d-%H%M%S')}.txt"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        output.write(report)
    print(tr('Collected a problem report ({line_count} lines) and saved it privately to\n{path}.', line_count=f'{len(report.splitlines())}', path=f'{path}'))
    print(tr('Nothing was sent. Read it and remove anything you do not want to share.'))
    print(tr(PRIVACY).rstrip())
    if sys.stdin.isatty():
        send(report, path)


if __name__ == "__main__":
    try:
        main()
    except OSError as error:
        sys.exit(str(error))
