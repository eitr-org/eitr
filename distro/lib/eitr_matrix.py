#!/usr/bin/env python3
"""Rune rain: Elder Futhark runes falling down the terminal in the current theme's colours.

`eitr matrix` runs it; any key (Esc, q, Ctrl+C included) stops it and gives the
terminal back exactly as it was: the rain draws on the alternate screen with the
cursor hidden. Each frame rewrites only the cells whose colour step changes.
"""
import argparse
import os
from pathlib import Path
import random
import select
import shutil
import signal
import sys
import termios
import time
import tomllib
import tty

import eitr_paths

RUNES = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"
# EITR in runes; now and then one column spells it, lit in the accent.
SIGNATURE = "ᛖᛁᛏᚱ"
SIGNATURE_CHANCE = 0.02
SPEEDS = {"slow": 0.09, "normal": 0.055, "fast": 0.03}
# Colour steps from the leading rune to the end of the trail.
STEPS = 6
FALLBACK = {"background": "#000000", "foreground": "#d8e6dc", "accent": "#5fd75f"}


def theme_colours(theme=None):
    """Background, foreground and accent of the current theme; light themes fade toward their light background."""
    theme = Path(theme) if theme else eitr_paths.config("theme/current")
    try:
        colours = tomllib.loads((theme / "colors.toml").read_text())
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        colours = {}
    picked = {key: colours.get(key, value) for key, value in FALLBACK.items()}
    return picked if all(is_colour(value) for value in picked.values()) else dict(FALLBACK)


def is_colour(value):
    return isinstance(value, str) and len(value) == 7 and value.startswith("#") \
        and all(digit in "0123456789abcdefABCDEF" for digit in value[1:])


def rgb(text):
    return tuple(int(text[index:index + 2], 16) for index in (1, 3, 5))


def mix(first, second, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(first, second))


def palette(colours, truecolour=True):
    """Escape sequences per step: 0 is the leading rune, STEPS - 1 the faintest trail."""
    if not truecolour:
        return ["\x1b[1;97m", "\x1b[1;32m", "\x1b[0;32m", "\x1b[0;32m", "\x1b[2;32m", "\x1b[2;32m"][:STEPS]
    background, foreground, accent = (rgb(colours[key]) for key in ("background", "foreground", "accent"))
    head = mix(accent, foreground, 0.6)
    steps = [head] + [mix(accent, background, step / (STEPS - 1) * 0.85) for step in range(STEPS - 1)]
    return [f"\x1b[{'1;' if step < 2 else ''}38;2;{r};{g};{b}m" for step, (r, g, b) in enumerate(steps)]


class Column:
    def __init__(self, rows, random_source):
        self.random = random_source
        self.reset(rows, start_above=True)

    def reset(self, rows, start_above=False):
        self.head = -self.random.randint(0, rows) if start_above else -self.random.randint(0, rows // 2)
        self.length = self.random.randint(max(4, rows // 4), max(5, rows))
        self.every = self.random.choice((1, 1, 2, 2, 3))
        self.signature = self.random.random() < SIGNATURE_CHANCE


class Rain:
    """The rain on a COLUMNS×ROWS grid; frame() returns the escape text for one tick."""

    def __init__(self, columns, rows, colours, truecolour=True, random_source=None):
        self.random = random_source or random.Random()
        self.columns, self.rows = columns, rows
        self.colours = palette(colours, truecolour)
        self.signature_colour = palette(colours, truecolour)[1]
        # Runes sit in every other cell, like the original rain's spaced columns.
        self.lanes = [Column(rows, self.random) for _ in range(max(1, columns // 2))]
        self.glyphs = {}
        self.tick = 0

    def step_for(self, distance, length):
        if distance == 0:
            return 0
        return min(STEPS - 1, 1 + (distance - 1) * (STEPS - 1) // max(1, length))

    def cell(self, lane, row, text):
        return f"\x1b[{row + 1};{lane * 2 + 1}H{text}"

    def frame(self):
        out = []
        for index, column in enumerate(self.lanes):
            if self.tick % column.every:
                continue
            column.head += 1
            head = column.head
            # The new leading rune, then every trail cell whose colour step changes.
            if 0 <= head < self.rows:
                if column.signature and 0 <= head - self.rows // 3 < len(SIGNATURE):
                    glyph = SIGNATURE[head - self.rows // 3]
                else:
                    glyph = self.random.choice(RUNES)
                self.glyphs[(index, head)] = glyph
                out.append(self.cell(index, head, self.colours[0] + glyph))
            for distance in range(1, column.length + 1):
                row = head - distance
                if not 0 <= row < self.rows:
                    continue
                step = self.step_for(distance, column.length)
                if step != self.step_for(distance - 1, column.length) or distance == 1:
                    glyph = self.glyphs.get((index, row), " ")
                    in_signature = column.signature and 0 <= row - self.rows // 3 < len(SIGNATURE)
                    colour = self.signature_colour if in_signature and step < STEPS - 2 else self.colours[step]
                    out.append(self.cell(index, row, colour + glyph))
            tail = head - column.length - 1
            if 0 <= tail < self.rows:
                self.glyphs.pop((index, tail), None)
                out.append(self.cell(index, tail, " "))
            # Now and then a rune in the trail changes, like the original rain.
            if column.length > 2 and self.random.random() < 0.15:
                row = head - self.random.randint(2, column.length)
                if 0 <= row < self.rows and (index, row) in self.glyphs:
                    glyph = self.random.choice(RUNES)
                    self.glyphs[(index, row)] = glyph
                    step = self.step_for(head - row, column.length)
                    out.append(self.cell(index, row, self.colours[step] + glyph))
            if tail >= self.rows:
                column.reset(self.rows)
        self.tick += 1
        return "".join(out) + "\x1b[0m"


ENTER = "\x1b[?1049h\x1b[?25l\x1b[2J"
LEAVE = "\x1b[0m\x1b[2J\x1b[?25h\x1b[?1049l"


def run(speed="normal", seconds=None, stdin=None, stdout=None):
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    if not stdin.isatty() or not stdout.isatty():
        raise SystemExit("eitr matrix needs a terminal.")
    colours = theme_colours()
    # The Linux text console has no 24-bit colour; everything else Eitr ships does.
    truecolour = os.environ.get("TERM") != "linux"
    descriptor = stdin.fileno()
    saved = termios.tcgetattr(descriptor)
    resized = {"pending": False}

    def on_resize(*_):
        resized["pending"] = True

    def on_stop(*_):
        raise KeyboardInterrupt

    previous = {signal.SIGWINCH: signal.signal(signal.SIGWINCH, on_resize),
                signal.SIGTERM: signal.signal(signal.SIGTERM, on_stop),
                signal.SIGHUP: signal.signal(signal.SIGHUP, on_stop)}
    deadline = time.monotonic() + seconds if seconds else None
    try:
        tty.setcbreak(descriptor)
        stdout.write(ENTER)
        size = shutil.get_terminal_size()
        rain = Rain(size.columns, size.lines, colours, truecolour)
        while deadline is None or time.monotonic() < deadline:
            if resized["pending"]:
                resized["pending"] = False
                size = shutil.get_terminal_size()
                stdout.write("\x1b[2J")
                rain = Rain(size.columns, size.lines, colours, truecolour)
            stdout.write(rain.frame())
            stdout.flush()
            ready, _, _ = select.select([descriptor], [], [], SPEEDS[speed])
            if ready:
                os.read(descriptor, 64)
                break
    except KeyboardInterrupt:
        pass
    finally:
        stdout.write(LEAVE)
        stdout.flush()
        termios.tcsetattr(descriptor, termios.TCSADRAIN, saved)
        for number, handler in previous.items():
            signal.signal(number, handler)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="eitr matrix", description="Elder Futhark runes falling in the theme's colours; any key stops it.")
    parser.add_argument("--speed", choices=sorted(SPEEDS), default="normal")
    parser.add_argument("--seconds", type=float, help="stop by itself after this many seconds")
    arguments = parser.parse_args(argv)
    if arguments.seconds is not None and arguments.seconds <= 0:
        parser.error("--seconds must be positive")
    return run(arguments.speed, arguments.seconds)


if __name__ == "__main__":
    sys.exit(main())
