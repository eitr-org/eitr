"""Full-resolution canonical GLSL references for Qt's shaderless offscreen backend."""
import json
import os
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'desktop-bar/shaders/aurora.frag'


class AuroraReference:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.executable = self.directory / 'render-aurora'
        self.cache = {}
        self.metrics = []

    def render(self, settings, width, height):
        light = settings.get('themeMode') == 'light'
        accent = settings.get('accent', '#a3bd79')
        colors = ['#c2ee5a', '#3fe39a', '#e04fc3', '#9b5ce6']
        if settings.get('eitrTheme') is False:
            palette = settings.get('palette') or [accent] * 4
            colors = [accent, palette[1], palette[3], palette[2]]
        key = (width, height, light, *colors)
        if key in self.cache:
            return self.cache[key]
        if not self.executable.exists():
            flags = shlex.split(subprocess.check_output(
                ['pkg-config', '--cflags', '--libs', 'Qt6Gui', 'egl', 'gl'], text=True))
            subprocess.run(['c++', '-std=c++17', '-O2', '-fPIC', '-pie',
                            str(Path(__file__).with_name('render-aurora.cpp')), '-o', str(self.executable),
                            *flags], check=True, capture_output=True, text=True, timeout=60)
        output = self.directory / f'aurora-{len(self.cache)}.png'
        environment = dict(os.environ, LIBGL_ALWAYS_SOFTWARE='1',
                           __EGL_VENDOR_LIBRARY_FILENAMES='/usr/share/glvnd/egl_vendor.d/50_mesa.json',
                           MESA_SHADER_CACHE_DIR=str(self.directory / 'mesa-cache'))
        command = [str(self.executable), str(SOURCE), str(output), str(width), str(height), '0',
                   '0.58' if light else '0.72', *colors, '1']
        if light:
            command.append(colors[3])
        result = subprocess.run(command, env=environment, check=True, capture_output=True, text=True, timeout=60)
        self.metrics.append({'width': width, 'height': height, 'light': light, 'measurement': result.stdout.strip()})
        self.cache[key] = output.as_uri()
        return self.cache[key]

    def write_report(self, destination):
        import hashlib
        report = {'method': 'Canonical GLSL executed by surfaceless Mesa software OpenGL, then composed by offscreen Qt.',
                  'shader': 'quickshell/desktop-bar/shaders/aurora.frag',
                  'shader_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  'references': self.metrics}
        Path(destination).write_text(json.dumps(report, indent=2) + '\n')
