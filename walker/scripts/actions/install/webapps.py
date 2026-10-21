#!/usr/bin/env python3
"""Web apps: launchers that open a site in its own browser window.

EITR ships no web apps or brand icons. The user names a site and its URL; the
site's own icon is downloaded at that moment, on the user's machine. Launchers
are ordinary desktop entries, so the Apps menu opens and removes them too.
"""
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

for parent in Path(__file__).resolve().parents:
    library = parent / 'lib'
    if not (library / 'eitr_paths.py').is_file():
        library = parent / 'distro/lib'
    if (library / 'eitr_paths.py').is_file():
        sys.path.insert(0, str(library))
        break
from eitr_paths import data as user_data
from eitr_wizard import Step, collect as collect_setup
from eitr_i18n import tr

APPLICATIONS = user_data("applications")
ICONS = user_data("eitr/webapps")
PREFIX = "eitr-webapp-"
MARKER = "X-Eitr-WebApp"
# Chromium-family browsers support app windows (--app); Firefox does not.
BROWSERS = ("google-chrome-stable", "chromium", "microsoft-edge-stable", "brave")
ICON_LIMIT = 2 * 1024 * 1024
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"


def slug(name):
    value = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not value:
        raise ValueError(tr('The name needs at least one letter or digit.'))
    return value[:48]


def clean_name(name):
    if any(ord(character) < 32 and not character.isspace() or ord(character) == 127 for character in name):
        raise ValueError(tr('The name must not contain control characters.'))
    name = " ".join(name.split())
    if not name or len(name) > 60:
        raise ValueError(tr('Use a name of 1 to 60 characters.'))
    return name


def clean_url(url):
    url = url.strip()
    if re.search(r"\s", url) or any(ord(character) < 32 or ord(character) == 127 for character in url) or "\\" in url:
        raise ValueError(tr('The URL must not contain spaces, control characters or backslashes.'))
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url):
        url = "https://" + url
    parts = urllib.parse.urlsplit(url)
    # --app treats javascript:, file: and data: as documents to run.
    if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
        raise ValueError(tr('Use an http or https address.'))
    if parts.username is not None or parts.password is not None:
        raise ValueError(tr('Do not put login credentials in the address.'))
    return url


def desktop_path(identifier):
    if not re.fullmatch(r"[a-z0-9-]{1,48}", identifier):
        raise ValueError(tr('Invalid web app ID'))
    return APPLICATIONS / f"{PREFIX}{identifier}.desktop"


def read_entry(path):
    values = {}
    for line in path.read_text().splitlines():
        if line.startswith("[") and line != "[Desktop Entry]":
            break
        key, separator, value = line.partition("=")
        if separator:
            values[key] = value
    return values


def apps():
    found = []
    for path in sorted(APPLICATIONS.glob(f"{PREFIX}*.desktop")):
        entry = read_entry(path)
        if entry.get(MARKER) == "true" and entry.get("X-Eitr-WebApp-URL"):
            found.append({"id": path.stem[len(PREFIX):], "name": entry.get("Name", path.stem),
                          "url": entry["X-Eitr-WebApp-URL"], "icon": entry.get("Icon", "web-browser"),
                          "path": str(path)})
    return sorted(found, key=lambda app: app["name"].casefold())


class IconLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.manifests = []

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        relation = (attributes.get("rel") or "").lower().split()
        if tag != "link" or not attributes.get("href"):
            return
        if "manifest" in relation:
            self.manifests.append(attributes["href"])
        elif "icon" in relation or "apple-touch-icon" in relation:
            preference = 2 if "apple-touch-icon" in relation else 1
            self.links.append((largest(attributes.get("sizes")), preference, attributes["href"]))


def largest(sizes):
    return max([int(size) for size in re.findall(r"(\d+)x\d+", sizes if isinstance(sizes, str) else "")] or [0])


def fetch(url, limit):
    request = urllib.request.Request(clean_url(url), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=10) as response:
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError(tr('too large'))
        return data, response.headers.get_content_type(), response.geturl()


def icon_candidates(url):
    candidates = []
    try:
        page, kind, final_url = fetch(url, 4 * ICON_LIMIT)
        if kind == "text/html":
            parser = IconLinks()
            parser.feed(page.decode("utf-8", "replace"))
            links = [(size, preference, urllib.parse.urljoin(final_url, href))
                     for size, preference, href in parser.links]
            for manifest_href in parser.manifests[:1]:
                manifest_url = urllib.parse.urljoin(final_url, manifest_href)
                try:
                    manifest = json.loads(fetch(clean_url(manifest_url), ICON_LIMIT)[0])
                    icons = manifest.get("icons", []) if isinstance(manifest, dict) else []
                    for icon in icons if isinstance(icons, list) else []:
                        if isinstance(icon, dict) and isinstance(icon.get("src"), str):
                            links.append((largest(icon.get("sizes")), 3, urllib.parse.urljoin(manifest_url, icon["src"])))
                except (OSError, ValueError, AttributeError):
                    pass
            candidates += [href for _, _, href in sorted(links, reverse=True)]
            url = final_url
    except (OSError, ValueError):
        pass
    origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
    candidates += [origin + "/apple-touch-icon.png", origin + "/favicon.ico"]
    return list(dict.fromkeys(candidates))


def save_icon(url, identifier, icon_url=""):
    """Download the site's icon as PNG (or SVG); None keeps the generic icon."""
    from PIL import Image
    ICONS.mkdir(parents=True, exist_ok=True)
    candidates = [clean_url(icon_url)] if icon_url else icon_candidates(url)
    for candidate in candidates:
        if urllib.parse.urlsplit(candidate).scheme not in ("http", "https"):
            continue
        try:
            data, kind, _ = fetch(candidate, ICON_LIMIT)
        except (OSError, ValueError):
            continue
        if kind == "image/svg+xml" or data.lstrip()[:5] in (b"<svg ", b"<?xml"):
            if b"<svg" in data[:4096]:
                target = ICONS / f"{identifier}.svg"
                target.write_bytes(data)
                return target
            continue
        try:
            with Image.open(io.BytesIO(data)) as image:
                image.load()
                if min(image.size) < 16:
                    continue
                image = image.convert("RGBA")
                image.thumbnail((256, 256))
                target = ICONS / f"{identifier}.png"
                image.save(target, "PNG")
                return target
        except (OSError, ValueError, Image.DecompressionBombError):
            continue
    return None


def desktop_value(value):
    return value.replace("\\", "\\\\").replace("\n", " ")


def create(name, url, icon_url="", icon_fetch=save_icon):
    name, url = clean_name(name), clean_url(url)
    identifier = slug(name)
    path = desktop_path(identifier)
    if path.exists():
        raise ValueError(tr('A web app named {name} already exists. Remove it first from Install > Web Apps.', name=f'{name}'))
    icon = icon_fetch(url, identifier, icon_url)
    script = Path(__file__).resolve()
    APPLICATIONS.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text("\n".join([
        "[Desktop Entry]",
        "Type=Application",
        f"Name={desktop_value(name)}",
        f"Comment={desktop_value(name)} web app",
        f"Exec=python3 {script} launch {identifier}",
        f"Icon={icon or 'web-browser'}",
        "Terminal=false",
        "Categories=Network;WebBrowser;",
        f"{MARKER}=true",
        f"X-Eitr-WebApp-URL={desktop_value(url)}",
        "",
    ]))
    temporary.replace(path)
    return path, icon


def remove(identifier):
    path = desktop_path(identifier)
    if not path.exists() or read_entry(path).get(MARKER) != "true":
        raise ValueError(tr('Not an EITR web app'))
    path.unlink()
    for suffix in (".png", ".svg"):
        (ICONS / f"{identifier}{suffix}").unlink(missing_ok=True)


def browser():
    return next((name for name in BROWSERS if shutil.which(name)), None)


def launch(identifier):
    entry = read_entry(desktop_path(identifier))
    if entry.get(MARKER) != "true":
        raise ValueError(tr('Not an EITR web app'))
    url = clean_url(entry["X-Eitr-WebApp-URL"])
    command = browser()
    if not command:
        subprocess.run(["notify-send", tr('Web app needs a Chromium-based browser'),
                        tr('Install one from Walker > Install > Browsers; Firefox cannot open app windows.')],
                       check=False)
        return 1
    os.execvp(command, [command, f"--app={url}"])


def interactive():
    answers = collect_setup(tr('Create a web app: a launcher that opens a site in its own window.'), [
        Step('name', tr('Name'), description=tr('For example: Netflix'), validator=clean_name),
        Step('url', tr('Address'), description=tr('For example: {example}', example='netflix.com'), validator=clean_url),
        Step('icon', tr('Icon address'), description=tr('Optional; press Enter to detect it.'), optional=True, validator=clean_url),
    ])
    name, url, icon_url = (answers[key] for key in ('name', 'url', 'icon'))
    print(tr('\nFetching the icon…'), flush=True)
    path, icon = create(name, url, icon_url)
    if not browser():
        print(tr('Install Chrome, Chromium, Edge or Brave from Install > Browsers to open it.'))
    message = f"{clean_name(name)} is in your apps." + ("" if icon else " The site has no usable icon; a generic one is used.")
    subprocess.run(["notify-send", tr('Web app created'), message], check=False)
    return 0


def main(arguments):
    command = arguments[0] if arguments else ""
    if command == "create" and len(arguments) == 1:
        return interactive()
    if command == "create" and len(arguments) == 3:
        if not browser():
            raise ValueError(tr('Install Chrome, Chromium, Edge or Brave from Install > Browsers to open it.'))
        _, icon = create(arguments[1], arguments[2])
        message = f"{clean_name(arguments[1])} is in your apps." + ("" if icon else " The site has no usable icon; a generic one is used.")
        subprocess.run(["notify-send", tr('Web app created'), message], check=False)
        return 0
    if command == "list" and len(arguments) == 1:
        print(json.dumps(apps()))
        return 0
    if command == "launch" and len(arguments) == 2:
        return launch(arguments[1])
    if command == "remove" and len(arguments) == 2:
        remove(arguments[1])
        return 0
    print('Usage: webapps.py create [NAME URL] | list | launch ID | remove ID', file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
