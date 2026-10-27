"""Shared console rendering and side-effect-free setup forms."""
from contextlib import redirect_stdout, redirect_stderr
import io
import sys
import curses
from dataclasses import dataclass
import importlib.util
import textwrap
import tomllib

from eitr_i18n import mark, tr
from eitr_paths import ROOT


class Cancelled(Exception):
    pass


class Back(Exception):
    pass


def filtered(options, query):
    return [item for item in options if query.casefold() in item[0].casefold()]


class Wizard:
    def __init__(self, screen, steps, root=ROOT):
        self.heading = tr('Setup steps')
        self.steps = steps
        self.root = root
        self.screen = screen
        self.step = 0
        self.body_width = max(1, screen.getmaxyx()[1] - 26)
        curses.curs_set(0)
        # Esc cancels at once; curses otherwise waits a second to tell it from arrow keys.
        curses.set_escdelay(25)
        curses.start_color()
        # Use the EITR identity theme, like the boot splash.
        palette = tomllib.loads((self.root / "themes/norse/colors.toml").read_text())
        for index, role in enumerate(("background", "foreground", "accent"), 1):
            rgb = [int(palette[role][offset:offset + 2], 16) for offset in (1, 3, 5)]
            if curses.can_change_color():
                curses.init_color((0, 7, 3)[index - 1], *(round(channel * 1000 / 255) for channel in rgb))
        background, foreground, accent = 0, 7, 3
        curses.init_pair(1, foreground, background)
        curses.init_pair(2, accent, background)
        curses.init_pair(3, background, accent)
        self.screen.bkgd(" ", curses.color_pair(1))
        self.logo = ["E I T R"]
        try:
            renderer = self.root / "fastfetch/eitr.py"
            spec = importlib.util.spec_from_file_location("eitr_logo", renderer)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.logo = module.terminal_logo(self.root / "fastfetch/assets/eitr-wordmark.png", 36, 12).removeprefix("$1").splitlines()
        except (ImportError, OSError, ValueError):
            pass

    def text(self, y, x, value, style=1):
        if not value:
            return
        height, width = self.screen.getmaxyx()
        if 0 <= y < height - 1 and 0 <= x < width - 1:
            limit = width - x - 1
            if getattr(self, 'body_x', None) is not None and x >= self.body_x:
                if y >= self.panel_bottom:
                    return
                limit = min(limit, self.body_x + self.body_width - x)
            value = tr(str(value))
            value = value if len(value) <= limit else value[:max(0, limit - 1)] + '…'
            if limit > 0:
                self.screen.addnstr(y, x, value, limit, curses.color_pair(style))

    def box(self, y, x, height, width):
        self.text(y, x, "┌" + "─" * (width - 2) + "┐", 2)
        for offset in range(1, height - 1):
            self.text(y + offset, x, "│", 2)
            self.text(y + offset, x + width - 1, "│", 2)
        self.text(y + height - 1, x, "└" + "─" * (width - 2) + "┘", 2)

    def frame(self, title, help_text=mark("Arrows: move  Enter: select  Type: search  Esc: back")):
        self.screen.erase()
        height, width = self.screen.getmaxyx()
        self.body_x = None
        if height < 24 or width < 80:
            self.text(1, 1, tr('Please enlarge the console to at least 80 columns and 24 rows.'))
            self.screen.refresh()
            self.panel_bottom = height - 3
            self.body_width = max(1, width - 4)
            return 3, 2
        compact = height < 30
        for y, row in enumerate(self.logo[:3] if compact else self.logo[:7], 1):
            self.text(y, max(0, (width - len(row)) // 2), row, 2)
        bar_width = 28
        progress = round(bar_width * self.step / len(self.steps))
        progress_y = 5 if compact else 9
        self.text(progress_y, (width - bar_width) // 2, "═" * progress, 2)
        self.text(progress_y, (width - bar_width) // 2 + progress, "─" * (bar_width - progress))
        start_y = 8 if compact else 12
        start_x = 2
        left_width = min(max(len(tr(self.heading)) + 4,
                             max(len(tr(name)) + 5 for name in self.steps)), width // 2 - 4)
        panel_height = height - start_y - 2
        right_x = start_x + left_width + 1
        right_width = width - right_x - 2
        self.box(start_y - 1, start_x - 1, panel_height, left_width)
        self.box(start_y - 1, right_x, panel_height, right_width)
        self.panel_bottom = start_y + panel_height - 2
        self.text(start_y, start_x + 1, self.heading, 2)
        for index, name in enumerate(self.steps):
            label = tr(name)
            available = left_width - 5
            label = label if len(label) <= available else label[:available - 1] + '…'
            self.text(start_y + 2 + index, start_x, f"{'>' if index == self.step else ' '} {label}",
                      2 if index == self.step else 1)
        self.body_x = right_x + 2
        self.body_width = right_width - 4
        self.text(start_y, self.body_x, title, 2)
        # Footer belongs to the screen, outside the content clipping rectangle.
        self.body_x = None
        self.text(height - 2, 2, help_text)
        self.body_x = right_x + 2
        return start_y + 2, self.body_x

    def choose(self, title, options, note="", details=None):
        """Pick one option; details(value) lists lines about the highlighted one."""
        query, selected = "", getattr(self, "choice_index", 0)
        while True:
            y, x = self.frame(title)
            for paragraph in note.splitlines():
                for line in textwrap.wrap(paragraph, self.body_width):
                    self.text(y, x, line)
                    y += 1
            if note:
                y += 1
            self.text(y, x, f"Search: {query}" if query else "Type to search")
            matches = filtered(options, query)
            selected = min(selected, max(0, len(matches) - 1))
            count = max(1, min(18, self.screen.getmaxyx()[0] - y - 6 - (3 if details else 0)))
            start = max(0, selected - count + 1)
            for index, (label, _) in enumerate(matches[start:start + count], start):
                self.text(y + 2 + index - start, x, label[:self.body_width], 3 if index == selected else 1)
            if not matches:
                self.text(y + 2, x, tr('No matches'))
            elif details:
                lines = details(matches[selected][1])
                for offset, line in enumerate(lines):
                    self.text(self.panel_bottom - len(lines) + offset, x, line[:self.body_width])
            self.screen.refresh()
            key = self.screen.get_wch()
            if key in getattr(self, "cancel_keys", ("\x1b",)):
                raise Cancelled
            if getattr(self, 'allow_back', False) and key in (curses.KEY_LEFT, '\t', curses.KEY_BTAB):
                raise Back
            if key in (curses.KEY_UP, curses.KEY_DOWN):
                selected = max(0, selected + (1 if key == curses.KEY_DOWN else -1))
            elif key in ("\n", "\r", curses.KEY_ENTER) and matches:
                return matches[selected][1]
            elif key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
                query, selected = query[:-1], 0
            elif isinstance(key, str) and key.isprintable():
                query, selected = query + key, 0

    def field(self, title, description, value="", secret=False, validator=None, invalid="Please enter a valid value."):
        error = ""
        while True:
            y, x = self.frame(title, tr('Enter: continue  Esc: back'))
            lines = [wrapped for paragraph in description.splitlines()
                     for wrapped in (textwrap.wrap(paragraph, self.body_width) or [''])]
            for offset, line in enumerate(lines):
                self.text(y + offset, x, line)
            entry = y + max(4, len(lines) + 1)
            self.text(entry, x, ("*" * len(value) if secret else value) + "_", 2)
            for offset, line in enumerate(textwrap.wrap(error, self.body_width)):
                self.text(entry + 2 + offset, x, line, 2)
            self.screen.refresh()
            key = self.screen.get_wch()
            if key in getattr(self, "cancel_keys", ("\x1b",)):
                raise Cancelled
            if key in ("\n", "\r", curses.KEY_ENTER):
                if value and (validator is None or validator(value)):
                    return value
                error = invalid
            elif key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
                value = value[:-1]
            elif isinstance(key, str) and key.isprintable() and len(value) < 256:
                value += key

    def password(self, title, description=None, validator=None, invalid=None):
        description = description or tr('Use at least 8 characters. Your input is hidden.')
        validator = validator or (lambda value: len(value) >= 8)
        while True:
            first = self.field(title, description, secret=True, validator=validator,
                               invalid=invalid or "Please enter a valid value.")
            second = self.field(title, tr('Repeat the password.'), secret=True)
            if first == second:
                return first
            self.choose(tr('Passwords did not match'), [(tr('Try again'), None)])


@dataclass
class Step:
    key: str
    label: str
    default: object = ''
    options: object = None
    validator: object = None
    secret: bool = False
    optional: bool = False
    description: str = ''
    question: str = ''
    password: bool = False


class SetupWizard(Wizard):
    """Navigate answers in memory; callers apply only a returned review."""

    def __init__(self, screen, title, steps):
        super().__init__(screen, tuple(step.label for step in steps) + (tr('Review'),))
        self.allow_back = True
        self.cancel_keys = ('\x1b', '\x03')
        self.title = title
        self.fields = steps
        self.values = {}

    def frame(self, title, help_text=None):
        return super().frame(title, help_text or tr('Enter: answer  Left / Tab: back  Esc: cancel'))

    def default(self, step):
        return step.default(self.values) if callable(step.default) else step.default

    def answer(self, step):
        if step.password:
            return self.password(step.question or step.label, step.description or None, step.validator)
        if step.options is not None:
            options = step.options(self.values) if callable(step.options) else step.options
            current = self.values.get(step.key, self.default(step))
            self.choice_index = next((index for index, (_, value) in enumerate(options) if value == current), 0)
            return self.choose(step.question or step.label, options, step.description)
        value = self.values.get(step.key, self.default(step))
        error = ''
        while True:
            y, x = self.frame(step.question or step.label)
            for offset, line in enumerate(textwrap.wrap(step.description, self.body_width)):
                self.text(y + offset, x, line)
            self.text(y + 4, x, ('*' * len(value) if step.secret else value) + '_', 2)
            self.text(y + 6, x, error, 2)
            self.screen.refresh()
            key = self.screen.get_wch()
            if key in ('\x1b', '\x03'):
                raise Cancelled
            if key in (curses.KEY_LEFT, '\t', curses.KEY_BTAB):
                self.values[step.key] = value
                raise Back
            if key in ('\n', '\r', curses.KEY_ENTER):
                try:
                    if not value and not step.optional:
                        raise ValueError(tr('Please enter a valid value.'))
                    if step.validator and (value or not step.optional):
                        valid = step.validator(value)
                        if valid is False:
                            raise ValueError(tr('Please enter a valid value.'))
                    return value
                except ValueError as failure:
                    error = str(failure)
            elif key in (curses.KEY_BACKSPACE, '\x7f', '\b'):
                value = value[:-1]
            elif isinstance(key, str) and key.isprintable() and len(value) < 4096:
                value += key

    def run(self):
        error = ''
        review_offset = 0
        while True:
            y, x = self.frame(self.title, tr('Arrows / Tab: move  Enter: answer  Esc: cancel'))
            if self.step < len(self.fields):
                step = self.fields[self.step]
                value = self.values.get(step.key, self.default(step))
                if step.options is not None:
                    options = step.options(self.values) if callable(step.options) else step.options
                    value = next((label for label, choice in options if choice == value), value)
                self.text(y, x, step.question or step.label, 2)
                self.text(y + 4, x, '*' * len(str(value)) if step.secret else str(value))
                for offset, line in enumerate(textwrap.wrap(step.description, self.body_width)):
                    self.text(y + 1 + offset, x, line)
            else:
                bottom = getattr(self, 'panel_bottom', self.screen.getmaxyx()[0] - 3)
                count = max(1, bottom - y - 4)
                review_lines = []
                for step in self.fields:
                    value = self.values.get(step.key, '')
                    if step.options is not None:
                        options = step.options(self.values) if callable(step.options) else step.options
                        value = next((label for label, choice in options if choice == value), value)
                    if step.secret:
                        value = '*' * len(str(value))
                    value = str(value) if value != '' else tr('(none)')
                    review_lines.extend(textwrap.wrap(f'{tr(step.label)}: {value}', self.body_width))
                review_offset = min(review_offset, max(0, len(review_lines) - count))
                for offset, line in enumerate(review_lines[review_offset:review_offset + count]):
                    self.text(y + offset, x, line)
                self.text(bottom - 2, x, tr('Enter: apply  Left: back  PgUp/PgDn: scroll  Esc: cancel'), 2)
            self.text(y + 1 if self.step < len(self.fields) else bottom - 1, x, error, 2)
            self.screen.refresh()
            key = self.screen.get_wch()
            if key in ('\x1b', '\x03'):
                raise Cancelled
            if self.step == len(self.fields) and key in (curses.KEY_NPAGE, curses.KEY_PPAGE):
                review_offset = max(0, min(len(review_lines) - 1, review_offset + (1 if key == curses.KEY_NPAGE else -1)))
            elif key in ('\t', curses.KEY_DOWN, curses.KEY_RIGHT):
                self.step = (self.step + 1) % len(self.steps)
            elif key in (curses.KEY_UP, curses.KEY_LEFT, curses.KEY_BTAB):
                self.step = (self.step - 1) % len(self.steps)
            elif key in ('\n', '\r', curses.KEY_ENTER):
                error = ''
                if self.step == len(self.fields):
                    missing = next((index for index, step in enumerate(self.fields)
                                    if step.key not in self.values), None)
                    if missing is None:
                        for index, field in enumerate(self.fields):
                            value = self.values[field.key]
                            try:
                                if not value and not field.optional and field.options is None:
                                    raise ValueError(tr('Please enter a valid value.'))
                                if field.validator and (value or not field.optional) and field.validator(value) is False:
                                    raise ValueError(tr('Please enter a valid value.'))
                            except ValueError as failure:
                                self.step, error = index, str(failure)
                                break
                        else:
                            return dict(self.values)
                        continue
                    self.step = missing
                else:
                    step = self.fields[self.step]
                    try:
                        answer = self.answer(step)
                    except Back:
                        continue
                    if self.values.get(step.key) != answer:
                        for dependent in self.fields[self.step + 1:]:
                            if callable(dependent.default) or callable(dependent.options):
                                self.values.pop(dependent.key, None)
                    self.values[step.key] = answer
                    self.step += 1


def collect(title, steps):
    """No filesystem, provider, or subprocess work happens during collection."""
    sys.stdout.flush()
    sys.stderr.flush()

    output, errors = io.StringIO(), io.StringIO()

    def run(screen):
        with redirect_stdout(output), redirect_stderr(errors):
            return SetupWizard(screen, title, steps).run()

    try:
        return curses.wrapper(run)
    except (Cancelled, KeyboardInterrupt):
        raise KeyboardInterrupt from None
    finally:
        sys.stdout.write(output.getvalue())
        sys.stderr.write(errors.getvalue())
        sys.stdout.flush()
        sys.stderr.flush()
