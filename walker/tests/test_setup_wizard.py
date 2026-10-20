"""Drive the shared wizard without curses initialization or a terminal."""
import curses
import io
import sys
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from home_isolation import setUpModule, tearDownModule
import eitr_wizard
from eitr_wizard import Cancelled, SetupWizard, Step


class SetupWizardTests(unittest.TestCase):
    def wizard(self, steps, keys):
        wizard = object.__new__(SetupWizard)
        wizard.fields = steps
        wizard.steps = tuple(step.label for step in steps) + ('Review',)
        wizard.values = {}
        wizard.title = 'Setup'
        wizard.step = 0
        wizard.screen = Mock()
        wizard.screen.getmaxyx.return_value = (40, 100)
        wizard.screen.get_wch.side_effect = keys
        wizard.frame = Mock(return_value=(14, 26))
        wizard.text = Mock()
        wizard.body_width = 70
        wizard.panel_bottom = 33
        return wizard

    def test_blank_text_is_not_translated_or_drawn(self):
        wizard = object.__new__(SetupWizard)
        wizard.screen = Mock()
        with patch.object(eitr_wizard, 'tr') as translate:
            wizard.text(1, 1, '')
        translate.assert_not_called()
        wizard.screen.addnstr.assert_not_called()

    def test_output_is_flushed_before_curses_and_replayed_only_after_teardown(self):
        output, errors = io.StringIO(), io.StringIO()

        def wrapper(callback):
            result = callback(object())
            self.assertEqual(output.getvalue(), 'before')
            self.assertEqual(errors.getvalue(), '')
            return result

        def run():
            print('during')
            print('diagnostic', file=sys.stderr)
            return {'name': 'example'}

        with patch.object(eitr_wizard.sys, 'stdout', output), \
                patch.object(eitr_wizard.sys, 'stderr', errors), \
                patch.object(eitr_wizard.curses, 'wrapper', side_effect=wrapper), \
                patch.object(eitr_wizard, 'SetupWizard') as constructor:
            output.write('before')
            constructor.return_value.run.side_effect = run
            self.assertEqual(eitr_wizard.collect('Setup', []), {'name': 'example'})
        self.assertEqual(output.getvalue(), 'beforeduring\n')
        self.assertEqual(errors.getvalue(), 'diagnostic\n')

    def test_review_requires_all_answers_and_can_revisit_any_step(self):
        wizard = self.wizard([Step('name', 'Name'), Step('scope', 'Scope')], [
            curses.KEY_RIGHT, curses.KEY_RIGHT, '\n',
            '\n', 'a', '\n', '\n', 'b', '\n',
            curses.KEY_LEFT, curses.KEY_LEFT, '\n', 'c', '\n',
            curses.KEY_RIGHT, '\n'])
        self.assertEqual(wizard.run(), {'name': 'ac', 'scope': 'b'})

    def test_text_validation_default_and_secret_review(self):
        wizard = self.wizard([Step('token', 'Token', default='a', secret=True,
                                   validator=lambda value: len(value) >= 2)],
                              ['\n', '\n', 'b', '\n', '\n'])
        self.assertEqual(wizard.run(), {'token': 'ab'})
        rendered = [str(call.args[2]) for call in wizard.text.call_args_list]
        self.assertIn('Token: **', rendered)
        self.assertNotIn('ab', rendered)
        self.assertIn('Please enter a valid value.', rendered)

    def test_optional_empty_and_filterable_choice(self):
        wizard = self.wizard([Step('optional', 'Optional', optional=True),
                               Step('choice', 'Choice', options=[('Alpha', 1), ('Beta', 2)])],
                              ['\n', '\n', '\n', 'b', '\n', '\n'])
        self.assertEqual(wizard.run(), {'optional': '', 'choice': 2})

    def test_review_uses_short_names_and_explicit_empty_value(self):
        wizard = self.wizard([Step('icon', 'Icon address', optional=True,
                                   question='Where is the icon?', description='Optional example')],
                             ['\n', '\n', '\n'])
        self.assertEqual(wizard.run(), {'icon': ''})
        rendered = [str(call.args[2]) for call in wizard.text.call_args_list]
        self.assertIn('Icon address: (none)', rendered)
        self.assertNotIn('Where is the icon?: ', rendered)

    def test_layout_bounds_for_every_language_and_terminal_size(self):
        root = Path(__file__).resolve().parents[2]
        for locale in ('en', 'pt_BR', 'es', 'de', 'fr'):
            for height, width in ((35, 110), (24, 80)):
                with self.subTest(locale=locale, size=(width, height)), \
                        patch.dict('os.environ', {'LC_ALL': '', 'LC_MESSAGES': locale}), \
                        patch.object(eitr_wizard, 'curses') as terminal:
                    terminal.color_pair.return_value = 0
                    terminal.can_change_color.return_value = False
                    screen = Mock()
                    screen.getmaxyx.return_value = (height, width)
                    wizard = SetupWizard(screen, 'A very long dashboard title ' * 8,
                                         [Step(str(index), 'Author name') for index in range(8)])
                    wizard.frame(wizard.title)
                    wizard.text(15, wizard.body_x, 'Long content ' * 40)
                    for call in screen.addnstr.call_args_list:
                        row, column, value, limit, _ = call.args
                        self.assertLess(row, height - 1)
                        self.assertLessEqual(column + len(value), width - 1)
                        self.assertLessEqual(len(value), limit)
                        if column == wizard.body_x and row >= 8:
                            self.assertLessEqual(column + len(value), wizard.body_x + wizard.body_width)
                    self.assertGreaterEqual(wizard.body_width, 30)
                    self.assertTrue(any('…' in call.args[2] for call in screen.addnstr.call_args_list))

    def test_cancel_at_navigation_field_choice_and_review(self):
        for keys in (['\x1b'], ['\n', '\x1b'], ['\n', 'a', '\n', '\x1b'], ['\x03']):
            with self.subTest(keys=keys):
                wizard = self.wizard([Step('name', 'Name')], keys)
                with self.assertRaises(Cancelled):
                    wizard.run()
        wizard = self.wizard([Step('choice', 'Choice', options=[('Alpha', 1)])], ['\n', '\x1b'])
        with self.assertRaises(Cancelled):
            wizard.run()

    def test_installer_uses_shared_renderer_and_preserves_order_and_validation(self):
        root = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location('wizard_installer', root / 'distro/archinstall/installer-ui.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        Wizard = installer.Wizard
        STEPS = installer.STEPS
        self.assertEqual(STEPS, ('Keyboard', 'Disk', 'Install type', 'Hostname', 'Username', 'Password', 'Encryption', 'Review'))
        wizard = self.wizard([], ['\n', '\x7f', 'e', '\n'])
        self.assertEqual(Wizard.field(wizard, 'Hostname', '', '-', validator=installer.valid_hostname), 'e')
        wizard.screen.get_wch.side_effect = ['\n', '\t', '\n']
        self.assertEqual(Wizard.review(wizard, ['User: alex'], 'Warning'), 'cancel')
        self.assertEqual(Wizard.review(wizard, ['User: alex'], 'Warning'), 'install')

    def test_installer_collect_keeps_original_sequence_and_review(self):
        root = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location('collect_installer', root / 'distro/archinstall/installer-ui.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        disk = dict(path='/dev/vda', model='Test', details=['Empty'], size=1024 ** 3,
                    free=0, alongside=False, alongside_reason='No space')
        with patch.object(installer, 'Wizard') as constructor, \
                patch.object(installer, 'automatic_timezone', return_value='UTC'), \
                patch.object(installer.Path, 'read_text', return_value='en_US.UTF-8 UTF-8'), \
                patch.object(installer, 'output', side_effect=['us\nde', 'vda 1G']), \
                patch.object(installer.subprocess, 'run') as command:
            wizard = constructor.return_value
            wizard.step = 0
            wizard.choose.side_effect = ['us', disk, 'erase', False]
            wizard.field.side_effect = ['eitr', 'alex', '/dev/vda']
            wizard.password.return_value = 'test-password'
            wizard.review.return_value = 'install'
            answers = installer.collect(object(), [], lambda: [('Test', disk)])
        self.assertEqual([call.args[0] for call in wizard.choose.call_args_list],
                         ['Keyboard layout', 'Install on which disk?', 'How should Eitr use /dev/vda?', 'Disk encryption'])
        self.assertIs(wizard.field.call_args_list[0].kwargs['validator'], installer.valid_hostname)
        self.assertIs(wizard.field.call_args_list[1].kwargs['validator'], installer.valid_username)
        self.assertIn('ERASE /dev/vda: Test', wizard.review.call_args.args[0])
        self.assertIn('Encryption: DISABLED', wizard.review.call_args.args[0])
        self.assertEqual(answers['username'], 'alex')
        self.assertEqual(answers['password'], 'test-password')
        self.assertFalse(answers['encrypted'])
        self.assertTrue(wizard.field.call_args.kwargs['validator']('/dev/vda'))
        self.assertFalse(wizard.field.call_args.kwargs['validator']('/dev/vdb'))
        command.assert_called_once()
