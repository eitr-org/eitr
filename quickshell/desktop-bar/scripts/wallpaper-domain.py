"""How bright the wallpaper is where the bar sits, so the Blur and Clear appearances can pick
readable text. For each monitor it takes the picture the monitor really shows (Hyprpaper's
active file, ultrawide variants included; else the saved wallpaper), fits it like Hyprpaper's
cover mode, and averages the colour of a strip along each screen edge, split into the bar's
three regions (start, middle, end). Results are cached by file and size, so a read after the
first costs two small commands."""
import json
import os
from pathlib import Path
import subprocess
import threading

from PIL import Image, ImageOps

# The width the picture is reduced to before measuring; plenty for averages.
SAMPLE_WIDTH = 240
# How far the strip reaches into the screen, in screen pixels: a bar plus its margin.
STRIP_DEPTH = 56
EDGES = ('top', 'bottom', 'left', 'right')


def run_json(command):
    try:
        return json.loads(subprocess.run(command, capture_output=True, text=True, timeout=4, check=True).stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def active_wallpapers():
    """Monitor name to the file Hyprpaper shows, or {} while it does not answer."""
    try:
        output = subprocess.run(['hyprctl', 'hyprpaper', 'listactive'], capture_output=True, text=True, timeout=4)
    except (OSError, subprocess.SubprocessError):
        return {}
    active = {}
    for line in output.stdout.splitlines():
        monitor, separator, path = line.partition(': ')
        if separator and path.strip().startswith('/'):
            active[monitor.strip()] = path.strip()
    return active


def saved_wallpaper():
    home = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config')
    try:
        return json.loads((home / 'eitr/appearance.json').read_text()).get('wallpaper') or ''
    except (OSError, ValueError):
        return ''


def hex_colour(pixel):
    return '#%02x%02x%02x' % tuple(int(channel) for channel in pixel[:3])


def edge_regions(path, width, height):
    """{edge: [start, middle, end]} average colours of the strip along each screen edge."""
    with Image.open(path) as picture:
        picture = picture.convert('RGB')
        sample_height = max(1, round(SAMPLE_WIDTH * height / width))
        fitted = ImageOps.fit(picture, (SAMPLE_WIDTH, sample_height), Image.Resampling.BILINEAR)
    across = max(1, round(STRIP_DEPTH * SAMPLE_WIDTH / width))
    boxes = {'top': (0, 0, SAMPLE_WIDTH, across), 'bottom': (0, sample_height - across, SAMPLE_WIDTH, sample_height),
             'left': (0, 0, across, sample_height), 'right': (SAMPLE_WIDTH - across, 0, SAMPLE_WIDTH, sample_height)}
    result = {}
    for edge, box in boxes.items():
        strip = fitted.crop(box)
        size = (3, 1) if edge in ('top', 'bottom') else (1, 3)
        averaged = strip.resize(size, Image.Resampling.BOX)
        result[edge] = [hex_colour(averaged.getpixel((index, 0) if size[0] == 3 else (0, index))) for index in range(3)]
    return result


class WallpaperDomain:
    def __init__(self):
        self.lock = threading.Lock()
        self.cache = {}

    def measure(self, path, width, height):
        try:
            stat = Path(path).stat()
        except OSError:
            return None
        key = (path, stat.st_mtime_ns, stat.st_size, width, height)
        with self.lock:
            if key in self.cache:
                return self.cache[key]
        try:
            regions = edge_regions(path, width, height)
        except (OSError, ValueError, Image.DecompressionBombError):
            return None
        with self.lock:
            if len(self.cache) > 16:
                self.cache.clear()
            self.cache[key] = regions
        return regions

    def read(self, topic):
        monitors = run_json(['hyprctl', 'monitors', '-j']) or []
        active, fallback = active_wallpapers(), saved_wallpaper()
        result = {}
        for monitor in monitors:
            name = monitor.get('name')
            width, height = monitor.get('width') or 0, monitor.get('height') or 0
            if monitor.get('transform', 0) % 2:
                width, height = height, width
            path = active.get(name) or fallback
            if not name or not width or not height or not path:
                continue
            regions = self.measure(path, width, height)
            if regions:
                result[name] = {'wallpaper': path, 'edges': regions}
        return {'monitors': result}
