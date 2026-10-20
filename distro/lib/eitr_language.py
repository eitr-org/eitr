"""User-session message locale preference; applied by environment.d at login."""
import argparse
import os
import shlex
from pathlib import Path
import tempfile

from eitr_i18n import languages, select_locale, tr
from eitr_paths import config

LOCALES = {"en": "en_US.UTF-8", "pt_BR": "pt_BR.UTF-8", "es": "es_ES.UTF-8",
           "de": "de_DE.UTF-8", "fr": "fr_FR.UTF-8"}
HEADER = "# Managed by Eitr Language; message language only.\n"


def preference_path():
    return config("environment.d/90-eitr-language.conf")


def selected():
    try:
        contents = preference_path().read_text()
    except FileNotFoundError:
        return "system"
    for key, value in LOCALES.items():
        if contents == HEADER + "LC_MESSAGES=" + value + "\nLC_ALL=\n":
            return key
    raise ValueError("Eitr language preference was edited outside the picker; review it before changing it")


def save(locale):
    if locale != "system" and (locale not in languages() or locale not in LOCALES):
        raise ValueError("Unsupported language")
    selected()
    path = preference_path()
    if locale == "system":
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".eitr-language-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as output:
            output.write(HEADER + "LC_MESSAGES=" + LOCALES[locale] + "\nLC_ALL=\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def system_name(path=Path("/etc/locale.conf")):
    environment = {}
    for line in path.read_text().splitlines():
        tokens = shlex.split(line, comments=True)
        if not tokens:
            continue
        if len(tokens) != 1 or "=" not in tokens[0]:
            raise ValueError("Invalid locale assignment")
        key, value = tokens[0].split("=", 1)
        if key in ("LC_ALL", "LC_MESSAGES", "LANG"):
            environment[key] = value
    supported = languages()
    return supported[select_locale(environment, supported)]["nativeName"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("get", "set", "system-name"))
    parser.add_argument("key", nargs="?", choices=("locale",))
    parser.add_argument("locale", nargs="?")
    arguments = parser.parse_args()
    if arguments.action == "system-name":
        try:
            print(system_name())
        except (OSError, ValueError, KeyError, TypeError):
            return
    elif arguments.key is None:
        parser.error(tr("get and set require locale"))
    elif arguments.action == "get":
        print(selected())
    else:
        if arguments.locale is None:
            parser.error("set requires a locale")
        save(arguments.locale)
        import subprocess
        subprocess.run(["notify-send", tr("Language"), tr("Language saved. Sign out and back in to apply it.")], check=False)


if __name__ == "__main__":
    main()
