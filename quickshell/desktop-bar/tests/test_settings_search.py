"""Production Settings search and reveal, with no live desktop services."""
from pathlib import Path
import tempfile
import unittest

from layout_render import BAR, copy_runtime, render_environment, render, capture_path


class SettingsSearchTests(unittest.TestCase):
    def test_search_reveal_and_fade_offscreen(self):
        with tempfile.TemporaryDirectory(prefix='settings-search-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            output = capture_path('SETTINGS_SEARCH', directory, 'search-dark.png').parent
            fixture = (BAR / 'tests/fixtures/settings/search.qml.in').read_text()
            (folder / 'fixture.qml').write_text(fixture.replace('OUTPUT', str(output)))
            code, log = render(folder / 'fixture.qml', render_environment(folder), 30)
            self.assertEqual(code, 0, log)
            self.assertIn('SEARCH_RENDER_OK', log)
            self.assertNotIn('FAIL!', log)
            self.assertNotIn('Binding loop', log)
            for name in ['search-dark', 'search-light', 'highlight-dark', 'highlight-light']:
                self.assertTrue((output / (name + '.png')).is_file(), name)
