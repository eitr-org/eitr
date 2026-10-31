"""Shared terminal dismissal for Python and shell callers."""
import os
import sys
import termios
import tty

from eitr_i18n import tr


def wait_for_escape(hint=True, close_on_q=False):
    if hint:
        print(tr('Press Esc to close.'), flush=True)
    if not sys.stdin.isatty():
        return
    closing = {b'\x1b', b''} | ({b'q', b'Q'} if close_on_q else set())
    descriptor = sys.stdin.fileno()
    previous = termios.tcgetattr(descriptor)
    try:
        tty.setraw(descriptor)
        while True:
            key = os.read(descriptor, 1)
            if key in closing:
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


if __name__ == '__main__':
    # About passes --no-hint --close-on-q: it closes with Esc or Q without saying so.
    wait_for_escape(hint='--no-hint' not in sys.argv[1:], close_on_q='--close-on-q' in sys.argv[1:])
