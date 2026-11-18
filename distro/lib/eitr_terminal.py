"""Shared terminal dismissal for Python and shell callers."""
import os
import sys
import termios
import tty

from eitr_i18n import tr


def wait_for_escape():
    print(tr('Press Esc to close.'), flush=True)
    if not sys.stdin.isatty():
        return
    descriptor = sys.stdin.fileno()
    previous = termios.tcgetattr(descriptor)
    try:
        tty.setraw(descriptor)
        while True:
            key = os.read(descriptor, 1)
            if key in (b'\x1b', b''):
                return
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)
        print()



def read_line_or_escape(prompt):
    """Read a terminal line, letting Escape dismiss without an extra Enter."""
    if not sys.stdin.isatty():
        return input(prompt)
    print(prompt, end='', flush=True)
    descriptor = sys.stdin.fileno()
    previous = termios.tcgetattr(descriptor)
    value = bytearray()
    try:
        tty.setraw(descriptor)
        while True:
            key = os.read(descriptor, 1)
            if key in (b'\x1b', b'\x03', b'\x04', b''):
                return None
            if key in (b'\r', b'\n'):
                return value.decode('utf-8', errors='replace')
            if key in (b'\x7f', b'\x08'):
                if value:
                    value.pop()
                    os.write(sys.stdout.fileno(), b'\b \b')
            elif key >= b' ':
                value.extend(key)
                os.write(sys.stdout.fileno(), key)
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)
        print()


def read_key():
    """One key press without Enter. An escape sequence, such as an arrow key, reads as Escape."""
    if not sys.stdin.isatty():
        return sys.stdin.readline()[:1] or '\x1b'
    descriptor = sys.stdin.fileno()
    previous = termios.tcgetattr(descriptor)
    try:
        tty.setraw(descriptor)
        key = os.read(descriptor, 1)
        termios.tcflush(descriptor, termios.TCIFLUSH)
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)
        print()
    return key.decode('utf-8', errors='replace') or '\x1b'


def confirm(question, marker='›'):
    """Enter continues; Escape, Ctrl+C or the end of input cancels; other keys do nothing."""
    print(f"{marker} {question} {tr('Enter: continue  Esc: cancel')} ", end='', flush=True)
    while True:
        key = read_key()
        if key in ('\r', '\n'):
            return True
        if key in ('\x1b', '\x03', '\x04', ''):
            return False


if __name__ == '__main__':
    # `eitr_terminal.py confirm QUESTION` exits 0 on Enter and 1 on Esc, for shell callers.
    if sys.argv[1:2] == ['confirm'] and len(sys.argv) == 3:
        raise SystemExit(0 if confirm(sys.argv[2]) else 1)
    wait_for_escape()
