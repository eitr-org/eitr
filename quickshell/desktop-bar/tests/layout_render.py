"""Shared inert runtime, capture paths and process checks for layout fixtures."""
import os
from pathlib import Path
import shutil
import subprocess

BAR = Path(__file__).resolve().parents[1]
EDGES = ('top', 'bottom', 'left', 'right')
CORNERS = ('square', 'rounded', 'extra-rounded')


def layout_fixture(name):
    return (BAR / 'tests/fixtures/layout' / (name + '.qml.in')).read_text()


def copy_runtime(folder):
    for source in BAR.rglob('*'):
        if source.suffix in ('.qml', '.js') or source.name in ('qmldir', 'corner-styles.json'):
            destination = folder / source.relative_to(BAR)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source, destination)


def render_environment(directory):
    return dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                QML_IMPORT_PATH=str(BAR.parent), EITR_CODE_ROOT=str(BAR.parents[1]), HOME=str(directory),
                **{name: str(directory) for name in ('XDG_CONFIG_HOME', 'XDG_STATE_HOME',
                   'XDG_CACHE_HOME', 'XDG_DATA_HOME', 'XDG_RUNTIME_DIR')},
                DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')


def capture_path(kind, directory, filename):
    folder = Path(os.environ.get('EITR_' + kind + '_RENDERS', directory))
    folder.mkdir(parents=True, exist_ok=True)
    return folder / filename


def render(path, environment, timeout):
    try:
        result = subprocess.run(['quickshell', '--no-color', '-p', str(path)], env=environment,
                                text=True, capture_output=True, timeout=timeout)
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired as error:
        return None, str(error.stdout) + str(error.stderr)
