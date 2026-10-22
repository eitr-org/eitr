#!/usr/bin/env python3
"""Your own wallpapers, themes and lockscreens, from Walker > Style.

  own.py wallpaper add [SOURCE]     copy a picture (file or https address) into your wallpapers
  own.py wallpaper delete PATH      confirm, then delete one of your wallpapers
  own.py wallpaper list             your wallpapers not already shown by the current theme
  own.py theme create               wizard: picture, light or dark, name; creates and applies it
  own.py theme colors ID            change a theme's colors, each change applied at once
  own.py theme delete ID            confirm, then delete one of your themes
  own.py lockscreen create          wizard: design, picture, accent, greeting, name
  own.py lockscreen delete VALUE    confirm, then delete one of your lockscreens

Everything stays in eitr_paths.own() on this computer; see eitr_own_style.
"""
import curses
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import cache, code, config as user_config
from eitr_i18n import mark, tr
from eitr_terminal import wait_for_escape
from eitr_wizard import Cancelled, Step, Wizard, collect
import eitr_own_style as own

OTHER = "other"
COLOR_LABELS = {"accent": mark("Accent"), "background": mark("Background"), "foreground": mark("Text"),
                "color1": mark("Red"), "color2": mark("Green"), "color3": mark("Yellow"), "color4": mark("Blue"),
                "color5": mark("Magenta"), "color6": mark("Cyan")}


def read_cache(name):
    try:
        return cache(name).read_text().strip()
    except OSError:
        return ""


def notify(title, body=""):
    if shutil.which("notify-send"):
        subprocess.run(["notify-send", title, body], check=False)


def confirm(question, action):
    """One Walker row: Enter confirms, Esc cancels."""
    answer = subprocess.run([str(code("walker/bin/walker")), "--dmenu", "--placeholder", question,
                             "--width", "600", "--minheight", "100"],
                            input=action + "\n", text=True, capture_output=True)
    return answer.returncode == 0 and answer.stdout.strip() == action


def theme_backgrounds():
    directory = user_config("theme/current/backgrounds")
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.iterdir() if path.suffix.lower() in own.SUFFIXES)


def picture_options(values=None):
    options = []
    current = read_cache("current-wallpaper")
    if current and Path(current).is_file():
        options.append((tr('Current wallpaper'), current))
    options += [(tr('{name} (yours)', name=path.name), str(path)) for path in own.wallpapers()]
    options += [(path.name, str(path)) for path in theme_backgrounds() if str(path) != current]
    options.append((tr('Another picture: a file or an https address'), OTHER))
    return options


def picture_steps(previous):
    return [
        Step('picture', tr('Picture'), default=previous.get('picture', ''), options=picture_options,
             description=tr('Your wallpapers, the current theme\'s wallpapers, or another picture.')),
        Step('location', tr('Other picture'), default=previous.get('location', ''), optional=True,
             validator=own.check_source,
             description=tr('Only for Another picture: a file such as ~/Pictures/lake.jpg or an https address. '
                            'Eitr downloads it and keeps a copy on this computer.')),
    ]


def chosen_picture(answers):
    if answers['picture'] != OTHER:
        return answers['picture']
    if not answers.get('location'):
        raise ValueError(tr('Enter the other picture\'s file or https address.'))
    return answers['location']


def ask(title, steps_for):
    """Collect answers, asking again (with the previous answers) until the picture is complete."""
    previous, note = {}, ''
    while True:
        answers = collect(note or title, steps_for(previous))
        try:
            return answers, chosen_picture(answers)
        except ValueError as error:
            previous, note = answers, str(error)


# Wallpapers

def add_wallpaper(source=None):
    if source is None:
        answers = collect(tr('Add your own wallpaper. Eitr keeps a copy only on this computer.'), [
            Step('source', tr('Picture'), validator=own.check_source,
                 description=tr('A file such as ~/Pictures/lake.jpg, or an https address. '
                                'Eitr downloads it (up to 50 MB) and checks that it is a picture.')),
        ])
        source = answers['source']
        print(tr('Adding the picture…'), flush=True)
    path = own.add_wallpaper(source)
    subprocess.run([sys.executable, str(code("walker/scripts/actions/wallpaper/transition.py")), "apply", str(path)],
                   check=False)
    notify(tr('Wallpaper added'), tr('{name} is in Style > Wallpaper and the wallpaper carousel.', name=path.name))
    return 0


def list_wallpapers():
    for path in own.wallpapers(beside=user_config("theme/current/backgrounds")):
        print(path)
    return 0


def delete_wallpaper(path, ask_first=confirm):
    path = own.own_wallpaper(path)
    if not ask_first(tr('Delete this wallpaper? Enter deletes, Esc keeps it.'), tr('Delete {name}', name=path.name)):
        return 0
    if read_cache("current-wallpaper") == str(path):
        backgrounds = theme_backgrounds()
        if backgrounds:
            subprocess.run([sys.executable, str(code("walker/scripts/actions/wallpaper/transition.py")),
                            "apply", str(backgrounds[0])], check=False)
    path.unlink()
    return 0


# Themes

def apply_theme(identifier):
    return subprocess.run(["bash", str(code("walker/scripts/actions/style/apply.sh")), identifier],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0


def create_theme():
    modes = [(tr('Automatic: from the picture\'s brightness'), ''), (tr('Dark'), 'dark'), (tr('Light'), 'light')]

    def steps(previous):
        return picture_steps(previous) + [
            Step('mode', tr('Light or dark'), default=previous.get('mode', ''), options=modes,
                 description=tr('Automatic picks light for a bright picture and dark otherwise.')),
            Step('name', tr('Name'), default=previous.get('name', ''), validator=own.free_theme_name,
                 description=tr('For example: Lake at Dawn. Enter on the review creates the theme and applies it.')),
        ]
    answers, source = ask(tr('Create a theme from a picture. It stays on this computer.'), steps)
    print(tr('Creating the theme…'), flush=True)
    directory = own.create_theme(answers['name'], source, answers['mode'] or None, previous=read_cache("current-theme"))
    print(tr('Applying it…'), flush=True)
    apply_theme(directory.name)
    return edit_colors(directory.name)


class ColorEditor(Wizard):
    """A list of the theme's colors with swatches; each change is applied at once."""

    def __init__(self, screen, identifier):
        super().__init__(screen, (tr('Colors'),))
        self.identifier = identifier
        self.exact = curses.can_change_color() and curses.COLORS >= 64

    def swatch(self, y, x, color, slot):
        """A small block of the color: exact where the terminal allows it, else the nearest of 256."""
        channels = [int(color[index:index + 2], 16) for index in (1, 3, 5)]
        if self.exact:
            number = 32 + slot
            curses.init_color(number, *(round(channel * 1000 / 255) for channel in channels))
        elif curses.COLORS >= 256:
            levels = (0, 95, 135, 175, 215, 255)
            cube = [min(range(6), key=lambda level: abs(levels[level] - channel)) for channel in channels]
            number = 16 + 36 * cube[0] + 6 * cube[1] + cube[2]
        else:
            return
        curses.init_pair(32 + slot, number, number)
        self.text(y, x, "   ", 32 + slot)

    def run(self):
        selected, message = 0, ''
        name = own.clean_name((own.theme_dir(self.identifier) / "display-name").read_text())
        while True:
            colors = own.theme_colors(self.identifier)
            y, x = self.frame(tr('Colors of {name}', name=name), tr('Arrows: move  Enter: change  Esc: done'))
            self.text(y, x, tr('Each change applies at once. Text must stay readable on the background.'))
            for index, key in enumerate(own.EDITABLE):
                row = y + 2 + index
                self.swatch(row, x, colors[key], index)
                self.text(row, x + 4, f"{tr(COLOR_LABELS[key]):<14}{colors[key]}", 3 if index == selected else 1)
            self.text(y + 3 + len(own.EDITABLE), x, message, 2)
            self.screen.refresh()
            key = self.screen.get_wch()
            if key in ("\x1b", "\x03"):
                return
            if key in (curses.KEY_UP, curses.KEY_DOWN):
                selected = (selected + (1 if key == curses.KEY_DOWN else -1)) % len(own.EDITABLE)
            elif key in ("\n", "\r", curses.KEY_ENTER):
                color = own.EDITABLE[selected]
                try:
                    value = self.field(tr(COLOR_LABELS[color]),
                                       tr('Six hex digits, for example #2bb87a. Esc keeps the color.'),
                                       colors[color])
                except Cancelled:
                    continue
                try:
                    own.set_theme_color(self.identifier, color, value)
                except ValueError as error:
                    message = str(error)
                    continue
                self.frame(tr('Colors of {name}', name=name), tr('Applying…'))
                self.screen.refresh()
                message = tr('Applied.') if apply_theme(self.identifier) else tr('The theme could not be applied.')


def edit_colors(identifier):
    own.theme_dir(identifier)
    curses.wrapper(lambda screen: ColorEditor(screen, identifier).run())
    return 0


def delete_theme(identifier, ask_first=confirm):
    directory = own.theme_dir(identifier)
    name = (directory / "display-name").read_text().strip() or identifier
    if not ask_first(tr('Delete this theme? Enter deletes, Esc keeps it.'), tr('Delete {name}', name=name)):
        return 0
    if read_cache("current-theme") == identifier:
        apply_theme(own.fallback_theme(identifier))
    own.delete_theme(identifier)
    return 0


# Lockscreens

def lock_settings():
    specification = importlib.util.spec_from_file_location(
        "eitr_lock_settings", code("quickshell/lockscreen/scripts/settings.py"))
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def free_lockscreen_name(name):
    if own.LOCK_PREFIX + own.slug(name) in own.own_lockscreens():
        raise ValueError(tr('A lockscreen named {name} already exists.', name=f'{name}'))
    return name


def create_lockscreen():
    names = lock_settings().NAMES
    designs = [(names.get(design, design), design) for design in own.LOCK_DESIGNS]

    def steps(previous):
        return [Step('design', tr('Design'), default=previous.get('design', own.LOCK_DESIGNS[0]), options=designs,
                     description=tr('The layout your picture, color and greeting go into.'))] + picture_steps(previous) + [
            Step('accent', tr('Accent color'), default=previous.get('accent', ''), optional=True,
                 validator=lambda value: own.HEX.match(value if value.startswith('#') else '#' + value) is not None,
                 description=tr('Optional: six hex digits such as #2bb87a. Empty keeps the design\'s color.')),
            Step('greeting', tr('Greeting'), default=previous.get('greeting', ''), optional=True,
                 validator=lambda value: len(value) <= 80,
                 description=tr('Optional text under the clock, up to 80 characters.')),
            Step('name', tr('Name'), default=previous.get('name', ''), validator=free_lockscreen_name,
                 description=tr('Enter on the review creates the lockscreen and shows a preview.')),
        ]
    answers, source = ask(tr('Create a lockscreen with your own picture. It stays on this computer.'), steps)
    print(tr('Creating the lockscreen…'), flush=True)
    value = own.create_lockscreen(answers['name'], answers['design'], source, answers['accent'], answers['greeting'])
    notify(tr('Lockscreen created'), tr('Select it in Style > Lockscreen; Ctrl+P previews it.'))
    subprocess.Popen(["bash", str(code("quickshell/lockscreen/scripts/preview.sh")), value],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return 0


def delete_lockscreen(value, ask_first=confirm):
    found = own.lockscreen(value)
    if not ask_first(tr('Delete this lockscreen? Enter deletes, Esc keeps it.'), tr('Delete {name}', name=found['name'])):
        return 0
    settings = code("quickshell/lockscreen/scripts/settings.py")
    current = subprocess.run([sys.executable, str(settings), "current"], capture_output=True, text=True).stdout.strip()
    if current == value:
        subprocess.run([sys.executable, str(settings), "select", found['design']], check=False)
    own.delete_lockscreen(value)
    return 0


COMMANDS = {
    ("wallpaper", "add"): add_wallpaper, ("wallpaper", "delete"): delete_wallpaper, ("wallpaper", "list"): list_wallpapers,
    ("theme", "create"): create_theme, ("theme", "colors"): edit_colors, ("theme", "delete"): delete_theme,
    ("lockscreen", "create"): create_lockscreen, ("lockscreen", "delete"): delete_lockscreen,
}


def main(arguments):
    command = COMMANDS.get(tuple(arguments[:2]))
    if command is None or len(arguments) > 3:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    return command(*arguments[2:])


if __name__ == "__main__":
    interactive = sys.argv[1:3] in (["wallpaper", "add"], ["theme", "create"], ["lockscreen", "create"]) and len(sys.argv) == 3
    try:
        sys.exit(main(sys.argv[1:]))
    except (ValueError, OSError) as error:
        print(f'\n\033[1;31m✗\033[0m {error}', file=sys.stderr)
        if not interactive:
            notify(tr('Could not complete that'), f'{error}')
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        print(tr('\nCancelled.'))
        sys.exit(0)
