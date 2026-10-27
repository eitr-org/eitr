"""The bar config stays private and independent of the interactive visualizer."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import configparser

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/cava-bar.py'
spec = importlib.util.spec_from_file_location('cava_bar', SCRIPT)
cava_bar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cava_bar)


class CavaBarTests(unittest.TestCase):
    def test_raw_config_and_atomic_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'eitr'
            target = cava_bar.write_config(directory)
            config = configparser.ConfigParser()
            config.read(target)
            self.assertEqual(config['general']['bars'], '4')
            self.assertEqual(config['general']['framerate'], '30')
            self.assertEqual(config['input']['method'], 'pipewire')
            self.assertEqual(config['output']['method'], 'raw')
            self.assertEqual(config['output']['raw_target'], '/dev/stdout')
            self.assertEqual(config['output']['data_format'], 'ascii')
            self.assertEqual(config['output']['ascii_max_range'], '100')
            self.assertEqual(config['output']['bar_delimiter'], '59')
            self.assertEqual(config['output']['frame_delimiter'], '10')
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            target.write_text('old config')
            cava_bar.write_config(directory)
            self.assertEqual(target.read_text(), cava_bar.CONFIG)
            self.assertEqual(list(directory.iterdir()), [target])

    def test_process_lifecycle_offscreen(self):
        import os
        import shutil
        import subprocess
        import sys
        if not shutil.which('quickshell'):
            self.skipTest('Quickshell required')
        root = SCRIPT.parents[3]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            fake = directory / 'cava'
            fake.write_text(f'#!{sys.executable}\n' + '''import os, signal, time
from pathlib import Path
log = Path(os.environ['CAVA_TEST_LOG'])
def record(message):
    with log.open('a') as stream:
        stream.write(message + '\\n')
def stop(signum, frame):
    record('stop')
    raise SystemExit(0)
signal.signal(signal.SIGTERM, stop)
record('start')
while True:
    print('0;25;50;100;', flush=True)
    time.sleep(.03)
''')
            fake.chmod(0o700)
            fixture = directory / 'shell.qml'
            fixture.write_text('''import Quickshell
import QtQuick
import "BAR"
ShellRoot {
    MediaStrip {
        id: strip
        foreground: "white"
        background: "black"
        players: [{identity: "Test", trackTitle: "Song", isPlaying: true}]
    }
    Timer {
        property int stage: 0
        interval: 300
        repeat: true
        running: true
        onTriggered: {
            if (stage === 0) {
                if (!strip.hasAudioFrame || strip.levels[2] !== .5) throw new Error("No audio frame");
                strip.enabled = false;
            } else if (stage === 1) {
                if (strip.hasAudioFrame) throw new Error("Hidden strip retained audio");
                strip.enabled = true;
            } else if (stage === 2) {
                if (!strip.hasAudioFrame) throw new Error("Audio did not restart");
                strip.players = [{identity: "Test", trackTitle: "Song", isPlaying: false}];
            } else {
                if (strip.hasAudioFrame || strip.cavaFailed) throw new Error("Pause cleanup failed");
                console.log("CAVA_LIFECYCLE_OK");
                Qt.quit();
            }
            stage++;
        }
    }
}'''.replace('BAR', SCRIPT.parents[1].as_uri()))
            log = directory / 'events'
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                               QML_IMPORT_PATH=str(root / 'quickshell'), EITR_CODE_ROOT=str(root),
                               XDG_CONFIG_HOME=temporary, XDG_CACHE_HOME=temporary,
                               XDG_RUNTIME_DIR=temporary, CAVA_TEST_LOG=str(log),
                               DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent',
                               PATH=temporary + os.pathsep + os.environ['PATH'])
            result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('CAVA_LIFECYCLE_OK', result.stdout + result.stderr)
            self.assertEqual(log.read_text().splitlines(), ['start', 'stop', 'start', 'stop'])

    def test_shared_consumers_and_failure_backoff(self):
        import os
        import shutil
        import subprocess
        import sys
        if not shutil.which('quickshell'):
            self.skipTest('Quickshell required')
        root = SCRIPT.parents[3]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            fake = directory / 'cava'
            fake.write_text(f'#!{sys.executable}\n' + '''import os, signal, time
from pathlib import Path
log = Path(os.environ['CAVA_TEST_LOG'])
def record(message):
    with log.open('a') as output:
        output.write(message + '\\n')
def stop(signum, frame):
    record('stop')
    raise SystemExit(0)
signal.signal(signal.SIGTERM, stop)
record('start')
if log.read_text().count('start') == 1:
    raise SystemExit(1)
while True:
    print('0;25;50;100;', flush=True)
    time.sleep(.03)
''')
            fake.chmod(0o700)
            fixture = directory / 'shell.qml'
            fixture.write_text('''import Quickshell
import QtQuick
import "BAR"
ShellRoot {
    SpectrumConsumer { id: first; active: true; bars: 4; frameRate: 30 }
    SpectrumConsumer { id: second; active: false; bars: 64; frameRate: 30; plugin: true; smoothing: true }
    Timer {
        interval: 1000; repeat: true; running: true
        property int stage: 0
        onTriggered: {
            if (stage === 0) {
                if (!SpectrumProvider.hasFrame || SpectrumProvider.consumers.length !== 1 || !first.audioActive)
                    throw new Error("Shared spectrum did not recover");
                if (SpectrumProvider.config.bars !== 4 || SpectrumProvider.config.fps !== 30 || SpectrumProvider.config.smoothing)
                    throw new Error("Media config changed");
                second.active = true;
                second.bars = 80; second.frameRate = 45;
                second.bars = 96; second.frameRate = 60;
                if (SpectrumProvider.config.bars !== 4 || !SpectrumProvider.hasFrame)
                    throw new Error("Reconfiguration was not debounced");
            } else if (stage === 1) {
                if (SpectrumProvider.config.bars !== 96 || SpectrumProvider.config.fps !== 60 || SpectrumProvider.config.smoothing)
                    throw new Error("Plugin requirements not selected");
                if (first.spectrum.length !== 4 || second.spectrum.length !== 96)
                    throw new Error("Counts were not resampled");
                second.active = false;
            } else if (stage === 2) {
                if (SpectrumProvider.config.bars !== 4 || SpectrumProvider.config.fps !== 30 || SpectrumProvider.config.smoothing)
                    throw new Error("Media config not restored");
                first.active = false;
            } else {
                if (SpectrumProvider.process.running || SpectrumProvider.consumers.length || SpectrumProvider.hasFrame)
                    throw new Error("Last consumer did not stop provider");
                console.log("SHARED_SPECTRUM_OK"); Qt.quit();
            }
            stage++;
        }
    }
}'''.replace('BAR', SCRIPT.parents[1].as_uri()))
            log = directory / 'events'
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                               QML_IMPORT_PATH=str(root / 'quickshell'), EITR_CODE_ROOT=str(root),
                               XDG_CONFIG_HOME=temporary, XDG_CACHE_HOME=temporary, XDG_STATE_HOME=temporary,
                               XDG_DATA_HOME=temporary, XDG_RUNTIME_DIR=temporary, CAVA_TEST_LOG=str(log),
                               DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent',
                               PATH=temporary + os.pathsep + os.environ['PATH'])
            result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('SHARED_SPECTRUM_OK', result.stdout + result.stderr)
            self.assertEqual(log.read_text().splitlines(), ['start', 'start', 'stop', 'start', 'stop', 'start', 'stop'])

    def test_unchanged_media_config(self):
        original = """[general]
bars = 4
framerate = 30
[input]
method = pipewire
source = auto
[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 100
bar_delimiter = 59
frame_delimiter = 10
"""
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(cava_bar.write_config(Path(temporary), 4, 30, 0).read_text(), original)

    def test_parameterized_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = cava_bar.write_config(Path(temporary), 128, 60, 1, 60)
            config = configparser.ConfigParser()
            config.read(path)
            self.assertEqual(config['general']['bars'], '128')
            self.assertEqual(config['general']['framerate'], '60')
            self.assertEqual(config['smoothing']['monstercat'], '1')
            self.assertEqual(config['smoothing']['noise_reduction'], '60')
            self.assertEqual(config['input']['source'], 'auto')
            for arguments in ((129, 60), (32, 61), (True, 30), (32, 0)):
                with self.assertRaises(ValueError):
                    cava_bar.write_config(Path(temporary), *arguments)
