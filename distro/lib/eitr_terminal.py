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


if __name__ == '__main__':
    wait_for_escape()
