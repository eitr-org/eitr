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


if __name__ == '__main__':
    wait_for_escape()
