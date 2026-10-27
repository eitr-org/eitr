"""Eitr's console wizard; collect choices before any installation writes."""
import eitr_bootstrap
from eitr_i18n import mark, tr
from eitr_users import valid_username
from eitr_wizard import Wizard as BaseWizard, Cancelled, filtered
import curses
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import textwrap
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[2]

STEPS = (mark("Keyboard"), mark("Disk"), mark("Install type"), mark("Hostname"),
         mark("Username"), mark("Password"), mark("Encryption"), mark("Review"))


class Wizard(BaseWizard):
    def __init__(self, screen, steps=STEPS, root=ROOT):
        super().__init__(screen, steps, root)
        self.heading = tr("INSTALL STEPS")

    def review(self, details, warning):
        selected = 0
        scroll = 0
        while True:
            y, x = self.frame(tr('Review installation'), tr('Tab / arrows: choose  Enter: select  PgUp/PgDn: scroll  Esc: cancel'))
            bottom = getattr(self, "panel_bottom", self.screen.getmaxyx()[0] - 3)
            count = max(1, bottom - y - 5)
            lines = [wrapped for line in details for wrapped in (textwrap.wrap(line, self.body_width) or [''])]
            scroll = min(scroll, max(0, len(lines) - count))
            for offset, line in enumerate(lines[scroll:scroll + count]):
                self.text(y + offset, x, line)
            self.text(bottom - 3, x, warning, 2)
            labels = (f" {tr('Cancel')} ", f" {tr('Continue')} ")
            column = x
            for index, label in enumerate(labels):
                self.text(bottom - 1, column, label, 3 if index == selected else 2)
                column += max(14, len(label) + 4)
            self.screen.refresh()
            key = self.screen.get_wch()
            if key in getattr(self, "cancel_keys", ("\x1b",)):
                raise Cancelled
            if key in (curses.KEY_NPAGE, curses.KEY_PPAGE):
                scroll = max(0, scroll + (count if key == curses.KEY_NPAGE else -count))
            elif key in ("\t", curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_UP, curses.KEY_DOWN):
                selected = 1 - selected
            elif key in ("\n", "\r", curses.KEY_ENTER):
                return ("cancel", "install")[selected]

    def preparation(self, checks):
        for index, (label, check) in enumerate(checks):
            self.screen.erase()
            height, width = self.screen.getmaxyx()
            y = max(1, height // 2 - len(self.logo) // 2 - 3)
            for row in self.logo:
                self.text(y, max(0, (width - len(row)) // 2), row, 2)
                y += 1
            self.text(y + 2, max(1, (width - 32) // 2), "═" * round(32 * index / len(checks)), 2)
            self.text(y + 4, max(1, (width - len(label)) // 2), label)
            self.screen.refresh()
            check()


def locale_options(text):
    locales = set()
    for line in text.splitlines():
        match = re.fullmatch(r"#?\s*([\w.@-]+\.UTF-8)\s+UTF-8", line.strip())
        if match:
            locales.add(match[1])
    return [(name, name) for name in sorted(locales, key=lambda name: (name != "en_US.UTF-8", name))]


def alongside_notes(disk):
    notes = [tr('Boot menu: Eitr starts first and lists Windows when it is found')]
    if "BitLocker" in disk["contents"]:
        notes.append(tr('BitLocker: keep the Windows recovery key at hand'))
    return notes


def size_text(size):
    return f"{size / 1024 ** 3:.1f} GiB"


def layout_options(disk):
    """The install type choices for a disk, and a note when installing alongside
    is unavailable. The installer decides eligibility (disk["alongside"])."""
    erase = (tr('Erase the whole disk ({size_text}) and install Eitr', size_text=f"{size_text(disk['size'])}"), "erase")
    if disk["alongside"]:
        # The choice that keeps data comes first, so Enter never erases by default.
        return [(tr('Install alongside the existing systems in {size_text} of free space', size_text=f"{size_text(disk['free'])}"),
                 "alongside"), erase], tr('Installing alongside keeps every existing partition.')
    return [erase], tr('Installing alongside is unavailable: {reason}', reason=disk["alongside_reason"])


def valid_hostname(value):
    return bool(re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", value))


KEY_SEQUENCES = ("0123456789" * 5, "abcdefghijklmnopqrstuvwxyz", "qwertyuiopasdfghjklzxcvbnm")


def strong_disk_passphrase(value, username=""):
    """A stolen disk can be guessed at offline forever, so its passphrase needs more than the login password."""
    text = value.lower()
    if len(value) < 12 or len(set(text)) < 4 or "password" in text:
        return False
    if username and username.lower() in text:
        return False
    return not any(text in sequence or text in sequence[::-1] for sequence in KEY_SEQUENCES)


def automatic_timezone():
    # Some networks block one geolocation service, so try a second.
    for url in ("https://ipinfo.io/timezone", "https://ipapi.co/timezone/"):
        try:
            value = output(["curl", "--fail", "--silent", "--max-time", "4", url])
            ZoneInfo(value)
            return value
        except (subprocess.SubprocessError, ValueError, ZoneInfoNotFoundError):
            continue
    return "UTC"


def output(command):
    return subprocess.check_output(command, text=True, timeout=15).strip()



PROFILE_REVIEW = []


def collect(screen, checks, disks):
    ui = Wizard(screen)
    ui.preparation(checks)
    keyboards = [(item, item) for item in output(["localectl", "list-keymaps"]).splitlines()]
    keyboards.sort(key=lambda item: (item[1] != "us", item[0]))
    if ("en_US.UTF-8", "en_US.UTF-8") not in locale_options(Path("/usr/share/i18n/SUPPORTED").read_text()):
        raise RuntimeError(tr('English UTF-8 support is missing from the live image'))
    timezone = automatic_timezone()
    # An offline installation falls back to UTC; the installed system detects it once online.
    values = {"hostname": "eitr", "language": "en_US.UTF-8", "timezone": timezone,
              "timezone_detected": timezone != "UTC"}
    while ui.step < len(STEPS):
        try:
            step = STEPS[ui.step]
            if step == "Keyboard":
                values["keyboard"] = ui.choose(tr('Keyboard layout'), keyboards)
                subprocess.run(["loadkeys", values["keyboard"]], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif step == "Disk":
                values["disk"] = ui.choose(tr('Install on which disk?'), disks(), details=lambda disk: disk["details"])
            elif step == "Install type":
                values["layout"] = ui.choose(tr('How should Eitr use {disk}?', disk=values["disk"]["path"]),
                                             *layout_options(values["disk"]))
            elif step == "Hostname":
                values["hostname"] = ui.field(tr('Hostname'), tr('Name this computer.'), values["hostname"], validator=valid_hostname)
            elif step == "Username":
                values["username"] = ui.field(tr('User account'), tr('Lowercase name. This user will have sudo access.'),
                                              values.get("username", ""), validator=valid_username)
            elif step == "Password":
                values["password"] = ui.password(tr('Account password'))
            elif step == "Encryption":
                values["encrypted"] = ui.choose(tr('Disk encryption'), [
                    (tr('Encrypt with LUKS2: boot passphrase required (recommended)'), True),
                    (tr('Do not encrypt: files are readable without a password'), False)])
                values.pop("passphrase", None)
                if values["encrypted"]:
                    values["passphrase"] = ui.password(
                        tr('LUKS2 disk encryption: needed at every boot'),
                        tr('At least 12 characters; your input is hidden.\nThree or four random words are strong and easy to type, like "rune fjord copper lantern".'),
                        validator=lambda value: strong_disk_passphrase(value, values.get("username", "")),
                        invalid=tr('Too easy to guess: avoid patterns and your user name.'))
            elif step == "Review":
                disk = values["disk"]
                alongside = values["layout"] == "alongside"
                contents = output(["lsblk", "-o", "NAME,SIZE,FSTYPE,LABEL", disk["path"]]).splitlines()
                choice = ui.review([
                    (tr('KEEP the partitions on {path}; use {size} of free space', path=disk['path'],
                        size=size_text(disk['free']))
                     if alongside else tr('ERASE {path}: {model}', path=disk['path'], model=disk['model'])),
                    tr('Language: {language} / Keyboard: {keyboard}', language=values['language'],
                       keyboard=values['keyboard']),
                    tr('Timezone: {timezone} / Hostname: {hostname}', timezone=values['timezone'],
                       hostname=values['hostname']),
                    tr('User: {username} / Btrfs / Limine UEFI', username=values['username']),
                    tr('Encryption: LUKS2, passphrase at boot') if values["encrypted"] else tr('Encryption: DISABLED'),
                    tr('Desktop: Afterglow / Clockwork Tape, installed offline before reboot'),
                    *(alongside_notes(disk) if alongside else ()),
                    *PROFILE_REVIEW,
                    *contents],
                    tr('Existing partitions are kept. Back up important files first.') if alongside
                    else tr('All partitions and files on this disk will be erased.'))
                if choice == "cancel":
                    raise Cancelled
                warning = (tr('New partitions are added in the free space of {path}.\n'
                              'Existing partitions are kept, but back up important files first.\n', path=disk['path'])
                           if alongside else tr('ALL partitions and files on {path} will be destroyed.\n', path=disk['path']))
                ui.field(tr('Final confirmation'), warning + tr('Type {path} exactly to start installation.', path=f"{disk['path']}"),
                         validator=lambda value: value == disk["path"])
            ui.step += 1
        except Cancelled:
            if ui.step == 0 or ui.step == len(STEPS) - 1:
                raise
            ui.step -= 1
    return values


def run(checks, disks):
    if not shutil.which("localectl"):
        raise RuntimeError(tr('localectl is required on the live ISO'))
    return curses.wrapper(collect, checks, disks)


PACKAGE_PROGRESS = re.compile(r"\(\s*(\d+)\s*/\s*(\d+)\s*\)\s+(?:installing|upgrading|reinstalling)\s")
PACKAGE_TOTAL = re.compile(r"^Packages \((\d+)\)\s")
PACKAGE_STEP = re.compile(r"^(?:installing|upgrading|reinstalling|downgrading) \S+\.\.\.$")


class StageProgress:
    """Progress inside a stage from pacman's own package counts, never from
    elapsed time: "(k/N) installing" on a terminal, otherwise the "Packages (N)"
    summary followed by one "installing name..." line per package. A stage can
    run several transactions, so the fraction never moves back."""

    def __init__(self):
        self.fraction = 0.0
        self.total = 0
        self.done = 0

    def update(self, line):
        if match := PACKAGE_PROGRESS.search(line):
            if int(match[2]):
                self.advance(int(match[1]) / int(match[2]))
        elif match := PACKAGE_TOTAL.match(line):
            self.total, self.done = int(match[1]), 0
        elif self.total and PACKAGE_STEP.match(line):
            self.done += 1
            self.advance(self.done / self.total)
        return self.fraction

    def advance(self, fraction):
        self.fraction = max(self.fraction, min(1.0, fraction))


def progress_bar(width, index, count, fraction):
    """Completed stages, plus the measured share of the current stage."""
    done = round(width * (index + fraction) / count)
    return "█" * done + "░" * (width - done)


class InstallationFailed(Exception):
    def __init__(self, title, lines):
        super().__init__(title)
        self.lines = lines


def duration_text(seconds):
    minutes, seconds = divmod(round(seconds), 60)
    return f"{minutes} min {seconds} s" if minutes else f"{seconds} s"


def installation(stages):
    """Show the installation stages and live backend output without fake timing,
    and return each stage's (title, seconds). On failure, the stage's last
    output lines are printed after the screen closes."""
    lines = []
    durations = []

    def render(screen):
        ui = Wizard(screen)
        state = {"progress": StageProgress()}

        def draw(index, title, line=""):
            if line:
                clean = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", line).strip()
                if clean:
                    lines.append(clean)
                state["progress"].update(clean)
            screen.erase()
            height, width = screen.getmaxyx()
            for y, row in enumerate(ui.logo, 2):
                ui.text(y, max(0, (width - len(row)) // 2), row, 2)
            panel_width = min(100, width - 4)
            x = (width - panel_width) // 2
            ui.box(12, x, min(16, height - 14), panel_width)
            ui.text(14, x + 3, tr('Step {step_number} of {step_count}', step_number=f'{min(index + 1, len(stages))}', step_count=f'{len(stages)}'), 1)
            ui.text(15, x + 3, title, 2)
            ui.text(18, x + 3, progress_bar(panel_width - 6, index, len(stages), state["progress"].fraction), 2)
            for offset, message in enumerate(lines[-max(1, min(6, height - 24)):]):
                ui.text(20 + offset, x + 3, message[:panel_width - 6])
            ui.text(height - 2, 2, tr('Installing the selected software. Profile additions may need the internet. Keep the computer powered on.'))
            screen.refresh()

        for index, (title, operation) in enumerate(stages):
            state["progress"] = StageProgress()
            draw(index, title)
            started = time.monotonic()
            try:
                operation(lambda line, index=index, title=title: draw(index, title, line))
            except Exception as error:
                raise InstallationFailed(title, [*lines[-20:], str(error)]) from error
            durations.append((title, time.monotonic() - started))
            state["progress"] = StageProgress()
            draw(index + 1, title)
    try:
        curses.wrapper(render)
    except InstallationFailed as failure:
        print(tr('\nInstallation stopped during: {failure}', failure=f'{failure}'), file=sys.stderr)
        print("\n".join(failure.lines), file=sys.stderr)
        raise failure.__cause__ from None
    return durations


def finished(seconds):
    """Completion screen with the installation time; True when the user chooses
    to power off now. The live system runs from the USB medium, so it must be
    removed only after power-off."""
    def render(screen):
        ui = Wizard(screen)
        while True:
            screen.erase()
            height, width = screen.getmaxyx()
            y = max(1, height // 2 - len(ui.logo) // 2 - 4)
            for row in ui.logo:
                ui.text(y, max(0, (width - len(row)) // 2), row, 2)
                y += 1
            for offset, (message, style) in enumerate((
                    (f"Eitr is installed (in {duration_text(seconds)}).", 2),
                    ("Press Enter to power off. Then remove the installation USB", 1),
                    ("and turn the computer on to reach the Eitr login.", 1),
                    ("Esc keeps this live session open.", 1))):
                ui.text(y + 2 + offset * 2, max(1, (width - len(message)) // 2), message, style)
            screen.refresh()
            key = screen.get_wch()
            if key in ("\n", "\r", curses.KEY_ENTER):
                return True
            if key == "\x1b":
                return False
    return curses.wrapper(render)


def preview(screen):
    """Render the interface only; never invoke installer or hardware commands."""
    ui = Wizard(screen)
    ui.preparation([("Preparing installer preview", lambda: None)])
    try:
        ui.choose(tr('Keyboard layout: PREVIEW ONLY'), [(label, label) for label in
                  ("English (US)", "English (US International)", "Portuguese (Brazil)",
                   "French", "German", "Spanish", "Dvorak", "Colemak")])
    except Cancelled:
        pass


if __name__ == "__main__":
    if sys.argv[1:] != ["--preview"]:
        raise SystemExit(tr('Use eitr-guided-install on the live ISO, or --preview for a safe UI preview.'))
    curses.wrapper(preview)
