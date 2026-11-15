"""The shipped zshrc puts nvm's default Node on PATH and loads nvm only on first use."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('zsh'), 'zsh required')
class NvmStartupTests(unittest.TestCase):
    def run_shell(self, home, script):
        environment = {'HOME': str(home), 'PATH': '/usr/bin:/bin', 'ZDOTDIR': str(home), 'TERM': 'dumb'}
        result = subprocess.run(['zsh', '-c', f'source {ROOT}/HOME_FILES/.zshrc 2>/dev/null; {script}'], stdin=subprocess.DEVNULL,
                                env=environment, text=True, capture_output=True, timeout=30)
        return result.stdout.split()

    def nvm_home(self, home):
        nvm = home / '.nvm'
        for name, target in (('default', 'lts/*'), ('lts/*', 'lts/test'), ('lts/test', 'v1.2.3')):
            (nvm / 'alias' / name).parent.mkdir(parents=True, exist_ok=True)
            (nvm / 'alias' / name).write_text(target + '\n')
        (nvm / 'nvm.sh').write_text('nvm() { echo real-nvm; }\nexport NVM_LOADED=yes\n')
        return nvm

    def test_default_version_is_on_path_without_loading_nvm(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            bin_dir = self.nvm_home(home) / 'versions/node/v1.2.3/bin'
            bin_dir.mkdir(parents=True)
            output = self.run_shell(home, f'print -r -- ${{path[(Ie){bin_dir}]}} ${{NVM_LOADED:-no}} $+functions[node]; nvm; print -r -- $NVM_LOADED')
            self.assertNotEqual(output[0], '0')
            self.assertEqual(output[1:], ['no', '0', 'real-nvm', 'yes'])

    def test_missing_default_version_loads_nvm_for_node(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.nvm_home(home)
            output = self.run_shell(home, 'print -r -- $+functions[node] ${NVM_LOADED:-no}; node --version </dev/null >/dev/null 2>&1; print -r -- $NVM_LOADED')
            self.assertEqual(output, ['1', 'no', 'yes'])


if __name__ == '__main__':
    unittest.main()
