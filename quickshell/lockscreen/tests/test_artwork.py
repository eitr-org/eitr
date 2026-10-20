from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ArtworkTests(unittest.TestCase):
    def test_eight_designs_are_shipped(self):
        designs = {str(path.parent.relative_to(ROOT / 'themes')) for path in (ROOT / 'themes').rglob('Main.qml')}
        self.assertEqual(designs, {'clockwork/neo-orbital', 'clockwork/tape', 'girl-coffee',
                                  'girl-pillow', 'material-you', 'material-you-dark', 'nothing', 'theme-wallpaper'})
        self.assertFalse((ROOT / 'drafts').exists())

    def test_gallery_matches_retained_designs_in_alphabetical_order(self):
        gallery = (ROOT / 'design-gallery.qml').read_text()
        rows = re.findall(r'\{id: "([^"]+)", title: Eitr\.I18n\.tr\("([^"]+)"\)\}', gallery)
        designs = {str(path.parent.relative_to(ROOT / 'themes')) for path in (ROOT / 'themes').rglob('Main.qml')}
        self.assertEqual({design for design, title in rows}, designs)
        titles = [title for design, title in rows]
        self.assertEqual(titles, sorted(titles, key=str.casefold))

    def test_designs_do_not_load_fonts_or_videos(self):
        sources = [*(ROOT / 'themes').rglob('*.qml'), *(ROOT / 'imports/LockscreenComponents').glob('Eitr*.qml'), ROOT / 'imports/LockscreenComponents/MaterialYouDesign.qml']
        for path in sources:
            source = path.read_text()
            self.assertNotRegex(source, r'\b(FontLoader|FolderListModel|BackgroundVideo|VideoOutput|MediaPlayer)\s*\{', str(path))
        self.assertFalse(any(path.suffix.lower() in ('.mp4', '.ttf', '.otf') for path in (ROOT / 'themes').rglob('*')))

    def test_gallery_never_locks_or_authenticates(self):
        source = (ROOT / 'design-gallery.qml').read_text()
        self.assertNotIn('WlSessionLock', source)
        self.assertNotIn('PamContext', source)
        for method in ('login(user, password, session)', 'reboot()', 'powerOff()', 'suspend()'):
            self.assertIn('function ' + method + ' {}', source)

    def test_clockwork_hands_lock_focus_to_its_password_field(self):
        # The lock host calls forceActiveFocus() on the design's root item.
        source = (ROOT / 'imports/LockscreenComponents/EitrClockworkDesign.qml').read_text()
        self.assertIn('onActiveFocusChanged: if (activeFocus) password.forceActiveFocus()', source)

    def test_procedural_clock_digits_have_complete_bitmaps(self):
        source = (ROOT / 'imports/LockscreenComponents/EitrDotTime.qml').read_text()
        self.assertEqual(len(re.findall(r'"[01]{35}"', source)), 10)

    def test_reference_artwork_and_preview_assets_exist(self):
        for name in ('girl-coffee', 'girl-pillow'):
            self.assertTrue((ROOT / 'themes' / name / 'background.png').is_file(), name)
        for path in (ROOT / 'themes').rglob('Main.qml'):
            self.assertTrue((path.parent / 'preview.png').is_file(), str(path))

    def test_retained_raster_artwork_and_previews_are_4k(self):
        images = list((ROOT / 'themes').rglob('*.png'))
        self.assertTrue(images)
        for path in images:
            with path.open('rb') as image:
                header = image.read(24)
            self.assertEqual(header[:8], b'\x89PNG\r\n\x1a\n', str(path))
            self.assertEqual(struct.unpack('>II', header[16:24]), (3840, 2160), str(path))
        for name in ('material-you', 'material-you-dark'):
            image = ET.parse(ROOT / 'themes' / name / 'background.svg').getroot()
            self.assertEqual((image.get('width'), image.get('height')), ('3840', '2160'))

    def test_offscreen_preview_has_mock_authentication_only(self):
        source = (ROOT / 'references/render-preview.qml').read_text()
        for forbidden in ('WlSessionLock', 'PamContext', 'AuthAdapter'):
            self.assertNotIn(forbidden, source)
        for method in ('login(user, password, session)', 'reboot()', 'powerOff()', 'suspend()'):
            self.assertIn('function ' + method + ' {}', source)
