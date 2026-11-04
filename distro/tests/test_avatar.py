"""Profile pictures use temporary homes and mocked buses only."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from PIL import Image
import eitr_avatar as avatar

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'walker/tests'))
from home_isolation import setUpModule, tearDownModule


class AvatarTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.source = self.home / 'source.png'
        Image.new('RGB', (800, 400), 'red').save(self.source)
        for target, replacement in ((patch.object(Path, 'home', return_value=self.home), None),
                                     (patch.object(avatar, 'account', side_effect=RuntimeError('unavailable')), None)):
            target.start()
            self.addCleanup(target.stop)

    def test_default_and_clamped_crop(self):
        self.assertEqual(avatar.crop_box(800, 400), (200, 0, 600, 400))
        self.assertEqual(avatar.crop_box(800, 400, -30, 900, 800), (0, 0, 400, 400))
        for size in (0, -1, float('nan')):
            with self.assertRaises(ValueError):
                avatar.crop_box(800, 400, 0, 0, size)

    def test_atomic_png_permissions_and_stripped_metadata(self):
        image = Image.new('RGB', (800, 400), 'red')
        exif = image.getexif()
        exif[270] = 'private metadata'
        image.save(self.source, exif=exif)
        replace = os.replace
        with patch.object(avatar, 'set_icon') as set_icon, patch.object(avatar.os, 'replace', wraps=replace) as rename:
            avatar.save(self.source)
        face = self.home / '.face'
        self.assertEqual(face.stat().st_mode & 0o777, 0o644)
        self.assertEqual(Path(rename.call_args.args[0]).parent, face.parent)
        set_icon.assert_called_once_with(str(face))
        with Image.open(face) as result:
            self.assertEqual(result.size, (512, 512))
            self.assertEqual(result.format, 'PNG')
            self.assertEqual(result.info, {})
        self.assertFalse(list(self.home.glob('.face-*')))

    def test_exif_orientation_before_crop(self):
        image = Image.new('RGB', (80, 40), 'blue')
        exif = image.getexif(); exif[274] = 6
        image.save(self.source, exif=exif)
        self.assertEqual(avatar.load_image(self.source).size, (40, 80))

    def test_reject_non_images_dimensions_and_file_size(self):
        self.source.write_text('invalid')
        with self.assertRaises(ValueError):
            avatar.load_image(self.source)
        with self.source.open('wb') as output:
            output.truncate(40 * 1024 * 1024 + 1)
        with self.assertRaises(ValueError):
            avatar.load_image(self.source)
        Image.new('RGB', (12001, 1)).save(self.source)
        with self.assertRaises(ValueError):
            avatar.load_image(self.source)
        with patch.object(Image, 'open', side_effect=Image.DecompressionBombError):
            with self.assertRaises(ValueError):
                avatar.load_image(self.source)

    def test_service_failure_preserves_face_and_reports(self):
        with patch.object(avatar, 'set_icon', side_effect=RuntimeError('denied')):
            with self.assertRaisesRegex(RuntimeError, 'lockscreen'):
                avatar.save(self.source)
            self.assertTrue((self.home / '.face').is_file())
            with self.assertRaisesRegex(RuntimeError, 'retained'):
                avatar.remove()
            self.assertTrue((self.home / '.face').is_file())

    def test_remove_order(self):
        face = self.home / '.face'; face.write_bytes(b'picture')
        with patch.object(avatar, 'set_icon', side_effect=lambda filename: self.assertTrue(face.exists())) as update:
            avatar.remove()
        update.assert_called_once_with('')
        self.assertFalse(face.exists())

    def test_missing_iconfile_and_fallback(self):
        bus = Mock()
        bus.call_sync.return_value.unpack.return_value = (str(self.home / '.face'),)
        with patch.object(avatar, 'account', return_value=(bus, '/user')), patch.object(avatar, 'gio', return_value=(Mock(), Mock())):
            self.assertIsNone(avatar.status()['path'])
            (self.home / '.face').write_bytes(b'picture')
            self.assertEqual(avatar.status()['path'], str(self.home / '.face'))

    def test_accounts_service_system_bus_calls(self):
        Gio, GLib = Mock(), Mock()
        bus = Gio.bus_get_sync.return_value
        bus.call_sync.return_value.unpack.return_value = ('/users/mock',)
        with patch.object(avatar, 'gio', return_value=(Gio, GLib)), patch.object(avatar, 'account', wraps=avatar.account.__wrapped__ if hasattr(avatar.account, '__wrapped__') else self.original_account):
            avatar.set_icon('/mock/.face')
        Gio.bus_get_sync.assert_called_once_with(Gio.BusType.SYSTEM, None)
        self.assertEqual([call.args[3] for call in bus.call_sync.call_args_list], ['FindUserByName', 'SetIconFile'])
        self.assertTrue(all(call.args[-2] == 5000 for call in bus.call_sync.call_args_list))

    original_account = staticmethod(avatar.account)

    def test_browse_lists_folders_then_images_by_name(self):
        folder = self.home / 'Pictures'
        for name in ('beta', 'Alpha', '.hidden'):
            (folder / name).mkdir(parents=True)
        for name in ('b.JPG', 'a.png', 'notes.txt', '.secret.png'):
            (folder / name).write_bytes(b'')
        result = avatar.browse(str(folder))
        self.assertEqual([entry['name'] for entry in result['folders']], ['Alpha', 'beta'])
        self.assertEqual([entry['name'] for entry in result['images']], ['a.png', 'b.JPG'])
        self.assertEqual((result['folder'], result['parent'], result['truncated']), (str(folder), str(self.home), False))
        self.assertIsNone(avatar.browse('/')['parent'])
        with self.assertRaises(ValueError):
            avatar.browse(str(self.home / 'missing'))

    def test_browse_starts_in_pictures_and_caps_large_folders(self):
        with patch.object(avatar, 'gio', side_effect=ImportError):
            self.assertEqual(avatar.browse()['folder'], str(self.home))
            (self.home / 'Pictures').mkdir()
            self.assertEqual(avatar.browse()['folder'], str(self.home / 'Pictures'))
        with patch.object(avatar, 'BROWSE_LIMIT', 2):
            for index in range(3):
                (self.home / f'{index}.png').write_bytes(b'')
            result = avatar.browse(str(self.home))
        self.assertEqual((len(result['images']), result['truncated']), (2, True))

    def test_preview_is_small_upright_and_maps_back_to_the_original(self):
        image = Image.new('RGB', (3000, 1500), 'red')
        exif = Image.Exif()
        exif[0x0112] = 6
        image.save(self.source.with_suffix('.jpg'), exif=exif)
        with patch.dict(os.environ, {'XDG_CACHE_HOME': str(self.home / 'cache')}):
            result = avatar.preview(self.source.with_suffix('.jpg'))
        self.assertEqual((result['width'], result['height']), (1500, 3000))
        self.assertEqual((result['previewWidth'], result['previewHeight']), (512, 1024))
        self.assertTrue(result['preview'].startswith(str(self.home / 'cache')))
        with Image.open(result['preview']) as small:
            self.assertEqual(small.size, (512, 1024))
        self.assertEqual(result['path'], str(self.source.with_suffix('.jpg').resolve()))

    def test_status_does_not_load_pillow(self):
        with patch.object(avatar, 'imaging', side_effect=AssertionError('Pillow loaded')):
            self.assertIn('initial', avatar.status())

    def test_cli_json(self):
        for command, expected in ((['status'], True), (['save', '/missing'], False)):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = avatar.main(command)
            value = json.loads(output.getvalue())
            self.assertEqual(value['ok'], expected)
            self.assertEqual(code, 0 if expected else 1)
