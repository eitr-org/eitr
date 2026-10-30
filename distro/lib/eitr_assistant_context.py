"""Offline, bounded Handbook reference data shared by assistant entry points."""
import re

from eitr_i18n import select_locale
from eitr_paths import code

BOOK = 'quickshell/desktop-bar/handbook/content'
# Common words and generic verbs (change, set, open...) carry no topic, so they never decide a section.
STOP_WORDS = set('a an and are as at be can do does for from get how i in is it me my of on or please the this to with you '
                 'change set open use make want need what where which why'.split())
PRIMER = """Eitr is a Norse-themed Arch Linux desktop running Hyprland, with its own
Quickshell desktop bar, Walker launcher backed by Elephant menus, and an offline
Eitr Handbook. The Handbook is the reference for this desktop; prefer its
instructions over generic Arch or Hyprland guesses.
Walker Main contains Development, Apps, Quick Actions, Tools, Learn, Install,
Plugins, Gaming, Settings and Power. Settings groups Connectivity, Devices &
Input, Language, Security, Style and System, with Control Center and Dotfiles.
Style controls themes, wallpapers and desktop appearance. Settings > System
contains Information, Maintenance, Update Channel, About and System Update.
Development contains AI assistants, Cloud, Git Accounts and editors.
Tools offers utilities; Learn contains shortcuts and the Handbook. The Control
Center opens common desktop settings and a disposable read-only quick chat.
User preferences live under ~/.config (or XDG_CONFIG_HOME). Machine-local Eitr
settings include eitr/ai.json and eitr/ai-accounts.json; monitor/input overrides
belong in hypr/local.lua. Packaged desktop code lives under /usr/share/eitr;
never assume a machine's connectors, hardware or accounts from shared defaults.
Stable and Testing are Eitr update channels; Testing previews Eitr packages,
while Arch updates still come from Arch. Use the documented Settings > System > System Update
workflow. Sudo needs the user's password; ask before destructive actions.
"""


def primer():
    """Read shortcut descriptions from Learn rather than maintaining another table."""
    try:
        from eitr_menu import shortcut_options
        lines = shortcut_options().splitlines()
    except OSError:
        lines = []
    shortcuts = []
    for line in lines:
        match = re.fullmatch(r'  (\S.*?)\s{2,}(.+)', line)
        if match:
            shortcuts.append(match.group(1) + ': ' + match.group(2))
    return PRIMER + '\nLearn shortcuts:\n' + '\n'.join(shortcuts)


def overview(*, locale=None):
    """Read the canonical welcome section, falling back if its translation is absent."""
    root = code(BOOK)
    locale = locale or select_locale()
    for path in (root / locale / 'getting-started.md', root / 'getting-started.md'):
        try:
            match = re.search(r'<!-- eitr-overview -->\s*(.*?)\s*<!-- /eitr-overview -->',
                              path.read_text(), re.S)
        except OSError:
            continue
        if match:
            return match.group(1)
    return ''


def tokens(text):
    return set(re.findall(r'[^\W_]+', text.casefold())) - STOP_WORDS


def excerpts(turns, *, locale=None, budget=7168):
    """Rank sections locally; fall back to English separately for each chapter."""
    root = code(BOOK)
    locale = locale or select_locale()
    # Only the latest two user turns provide retrieval context.
    query = tokens(' '.join([turn['text'] for turn in turns if turn['role'] == 'user'][-2:]))
    ranked = []
    for english in sorted(root.glob('*.md')):
        translated = root / locale / english.name
        path = translated if locale != 'en' and translated.is_file() else english
        try:
            text = path.read_text()
        except OSError:
            continue
        title = text.splitlines()[0].lstrip('# ')
        text = re.sub(r'<!-- eitr-overview -->.*?<!-- /eitr-overview -->', '', text, flags=re.S)
        for section in re.split(r'(?m)(?=^## )', text):
            heading = section.splitlines()[0].lstrip('# ') if section.strip() else ''
            score = len(query & tokens(section)) + 3 * len(query & tokens(heading + ' ' + title))
            if score:
                ranked.append((score, f'{english.stem}: {title}\n{section.strip()}'))
    selected = []
    remaining = max(0, budget)
    for _, section in sorted(ranked, key=lambda entry: entry[0], reverse=True)[:4]:
        encoded = section.encode('utf-8')[:max(0, remaining - 2)]
        clipped = encoded.decode('utf-8', errors='ignore')
        if clipped:
            selected.append(clipped)
            remaining -= len(clipped.encode('utf-8')) + 2
    return '\n\n'.join(selected)


def startup_instructions():
    root = code(BOOK)
    return (f'You are on Eitr. The offline Eitr Handbook at {root} '
            f'(locale folder: {root / select_locale()}, falling back to English) is the reference '
            'for how this desktop works. Read the relevant chapter before answering Eitr '
            'questions or changing its configuration. Settings and machine-local files live '
            'under ~/.config. Ask before destructive actions. Sudo needs the user’s password.')


def chat_excerpts(turns, *, locale=None, budget=7168):
    """Reserve the existing byte budget for the overview before ranked excerpts."""
    introduction = overview(locale=locale).encode('utf-8')[:max(0, budget)].decode('utf-8', errors='ignore')
    remaining = budget - len(introduction.encode('utf-8')) - 2
    relevant = excerpts(turns, locale=locale, budget=max(0, remaining))
    return '\n\n'.join(section for section in (introduction, relevant) if section)
