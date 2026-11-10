"""Verified local/HTTPS picture import and the user's wallpaper collection."""
import html
import html.parser
import io
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request

from eitr_i18n import tr
from eitr_paths import cache, own

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
MAX_BYTES = 50 * 1024 * 1024
MAX_PIXELS = 120_000_000
MIN_SIDE = 64
TIMEOUT = 20
FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

def clean_name(name):
    name = " ".join(str(name).split())
    if not name or len(name) > 40 or any(ord(character) < 32 or ord(character) == 127 for character in name):
        raise ValueError(tr('Use a name of 1 to 40 characters.'))
    return name


def slug(name):
    value = re.sub(r"[^a-z0-9]+", "-", clean_name(name).lower()).strip("-")[:40].strip("-")
    if not value:
        raise ValueError(tr('The name needs at least one letter or digit.'))
    return value


def check_source(source):
    """A local picture path or an https address; raises ValueError otherwise."""
    source = str(source).strip()
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", source):
        parts = urllib.parse.urlsplit(source)
        if parts.scheme.lower() != "https" or not parts.hostname:
            raise ValueError(tr('Use an https address or a file on this computer.'))
        if parts.username is not None or parts.password is not None:
            raise ValueError(tr('Do not put login credentials in the address.'))
        return source
    path = Path(source).expanduser()
    if not path.is_file():
        raise ValueError(tr('No picture file at {path}.', path=f'{path}'))
    return str(path.resolve())


class _HttpsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code_, message, headers, address):
        if urllib.parse.urlsplit(address).scheme.lower() != "https":
            raise ValueError(tr('The address redirected away from https.'))
        return super().redirect_request(request, response, code_, message, headers, address)


def download(url, opener=None):
    """The bytes at an https address, refusing anything larger than MAX_BYTES."""
    url = check_source(url)
    if not url.lower().startswith("https://"):
        raise ValueError(tr('Use an https address or a file on this computer.'))
    opener = opener or urllib.request.build_opener(_HttpsOnly())
    request = urllib.request.Request(url, headers={"User-Agent": "Eitr"})
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            length = response.headers.get("Content-Length")
            if length and length.isdigit() and int(length) > MAX_BYTES:
                raise ValueError(tr('The picture is larger than 50 MB.'))
            data = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as error:
        raise ValueError(tr('The site refused the download (HTTP {code}). {hint}', code=f'{error.code}',
                            hint=copy_image_hint())) from error
    except OSError as error:
        raise ValueError(tr('Could not download the picture: {error}', error=f'{error}')) from error
    if len(data) > MAX_BYTES:
        raise ValueError(tr('The picture is larger than 50 MB.'))
    return data


def picture_format(data):
    """The decoded picture's suffix; raises ValueError unless it is a whole JPEG, PNG or WebP."""
    from PIL import Image
    try:
        with Image.open(io.BytesIO(data)) as image:
            kind = image.format
            width, height = image.size
            if kind not in FORMATS:
                raise ValueError(tr('Use a JPEG, PNG or WebP picture.'))
            if width * height > MAX_PIXELS:
                raise ValueError(tr('The picture has too many pixels.'))
            if min(width, height) < MIN_SIDE:
                raise ValueError(tr('The picture is too small.'))
            image.load()
    except ValueError:
        raise
    except (OSError, SyntaxError, Image.DecompressionBombError) as error:
        raise ValueError(tr('This is not a picture Eitr can read.')) from error
    return FORMATS[kind]


def copy_image_hint():
    return tr('Open the picture itself, right-click it, choose Copy image address and paste that.')


class _PageImage(html.parser.HTMLParser):
    """The picture a web page offers for sharing (og:image or twitter:image)."""
    def __init__(self):
        super().__init__()
        self.image = None

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if tag == "meta" and not self.image and (values.get("property") or values.get("name") or "").lower() in (
                "og:image", "og:image:secure_url", "twitter:image"):
            self.image = (values.get("content") or "").strip() or None


def page_image(data, page):
    """The https address of a web page's main picture, or None."""
    if not data.lstrip()[:200].lower().startswith((b"<!doctype html", b"<html", b"<head", b"<meta", b"<!--")):
        return None
    parser = _PageImage()
    parser.feed(data.decode("utf-8", "replace"))
    if not parser.image:
        return None
    address = urllib.parse.urljoin(page, html.unescape(parser.image))
    return address if address.lower().startswith("https://") else None


def read_source(source, opener=None):
    source = check_source(source)
    if source.lower().startswith("https://"):
        data = download(source, opener)
        image = page_image(data, source)
        if image:
            # A page link: take the picture it offers, once, with the same checks.
            return download(image, opener)
        if data.lstrip()[:1] == b"<":
            raise ValueError(tr('That address is a web page, not a picture. {hint}', hint=copy_image_hint()))
        return data
    path = Path(source)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(tr('The picture is larger than 50 MB.'))
    return path.read_bytes()


def store_picture(source, directory, stem, opener=None):
    """Keep a verified copy of the picture in directory; returns its path."""
    data = read_source(source, opener)
    suffix = picture_format(data)
    directory = Path(directory)
    existing = same_picture(data, directory)
    if existing:
        return existing
    directory.mkdir(parents=True, exist_ok=True)
    target, number = directory / (stem + suffix), 2
    while target.exists():
        target, number = directory / f"{stem}-{number}{suffix}", number + 1
    descriptor, temporary = tempfile.mkstemp(prefix=".picture-", dir=directory)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(data)
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


def source_stem(source):
    name = Path(urllib.parse.urlsplit(source).path if "://" in source else source).stem
    try:
        return slug(name)
    except ValueError:
        return "wallpaper"


def pictures_in(directory):
    directory = Path(directory)
    if not directory.is_dir():
        return []
    return sorted((path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in SUFFIXES),
                  key=lambda path: (path.stem.casefold(), path.suffix))


def wallpapers(beside=None):
    """The user's own wallpapers; with beside (the current theme's backgrounds),
    leaving out pictures that theme already shows: a theme made from one keeps a copy."""
    mine = pictures_in(own("wallpapers"))
    try:
        identifier = cache("current-theme").read_text().strip()
    except OSError:
        identifier = ""
    if re.fullmatch(r"[a-z0-9-]{1,80}", identifier):
        mine += pictures_in(own("wallpapers") / "themes" / identifier)
    if beside is None:
        return mine
    shown = {(path.name, path.stat().st_size) for path in pictures_in(beside)}
    return [path for path in mine if (path.name, path.stat().st_size) not in shown]


def same_picture(data, directory):
    """A picture already in directory with exactly these bytes, or None."""
    for path in pictures_in(directory):
        if path.stat().st_size == len(data) and path.read_bytes() == data:
            return path
    return None


def add_wallpaper(source, opener=None, theme=""):
    directory = own("wallpapers")
    if theme:
        if not re.fullmatch(r"[a-z0-9-]{1,80}", theme):
            raise ValueError(tr('Not one of your themes'))
        directory = directory / "themes" / theme
    return store_picture(source, directory, source_stem(source), opener)


def own_wallpaper(path):
    """The path if it is one of the user's wallpapers, else ValueError."""
    path = Path(path)
    root = own("wallpapers").resolve()
    parent = path.resolve().parent
    themed = parent.parent == root / "themes" and re.fullmatch(r"[a-z0-9-]{1,80}", parent.name)
    if (parent != root and not themed) or not path.is_file() or path.is_symlink() or path.suffix.lower() not in SUFFIXES:
        raise ValueError(tr('Not one of your wallpapers'))
    return path
