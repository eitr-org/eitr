"""Styled prompts for the EITR task-terminal forms that need typing."""
import re

from eitr_paths import config
from eitr_i18n import tr


class Terminal:
    """Small styled prompts for the forms that need typing, in the theme's accent."""

    def __init__(self):
        accent = '#509475'
        try:
            match = re.search(r'^accent\s*=\s*"(#[0-9a-fA-F]{6})"', config('theme/current/colors.toml').read_text(), re.M)
            accent = match.group(1) if match else accent
        except OSError:
            pass
        red, green, blue = (int(accent[index:index + 2], 16) for index in (1, 3, 5))
        self.accent = f'\033[38;2;{red};{green};{blue}m'

    def title(self, text):
        return f'\n{self.accent}\033[1m{text}\033[0m'

    def bold(self, text):
        return f'\033[1m{text}\033[0m'

    def dim(self, text):
        return f'\033[2m{text}\033[0m'

    def ok(self, text):
        return f'\n{self.accent}✓\033[0m {text}'

    def ask(self, label, default='', hint=''):
        suffix = f' {self.dim("[" + default + "]")}' if default else ''
        if hint:
            print('  ' + self.dim(tr(hint)))
        return input(f'{self.accent}›\033[0m {tr(label)}{suffix} ').strip()



    def choose(self, label, options, default=1):
        """Numbered choice; returns the chosen option's index."""
        for number, option in enumerate(options, 1):
            print(f'  {self.accent}{number}\033[0m  {option}')
        answer = self.ask(label, str(default))
        if not answer:
            return default - 1
        if not answer.isdigit() or not 1 <= int(answer) <= len(options):
            raise ValueError(tr('Choose a number from 1 to {option_count}', option_count=f'{len(options)}'))
        return int(answer) - 1

    def confirm(self, question, default=True):
        answer = self.ask(question, 'Y/n' if default else 'y/N').casefold()
        return answer in ('y', 'yes') or (not answer and default)
