"""Drive the shared wizard without curses initialization or a terminal."""
import curses
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from home_isolation import setUpModule, tearDownModule
from eitr_wizard import Cancelled, SetupWizard, Step, Wizard, STEPS


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
        self.assertIs(installer.Wizard, Wizard)
        self.assertEqual(installer.STEPS, STEPS)
        self.assertEqual(STEPS, ('Keyboard', 'Disk', 'Install type', 'Hostname', 'Username', 'Password', 'Encryption', 'Review'))
        wizard = self.wizard([], ['\n', '\x7f', 'e', '\n'])
        self.assertEqual(Wizard.field(wizard, 'Hostname', '', '-', validator=installer.valid_hostname), 'e')
        wizard.screen.get_wch.side_effect = ['\n', '\t', '\n']
        self.assertEqual(wizard.review(['User: alex'], 'Warning'), 'cancel')
        self.assertEqual(wizard.review(['User: alex'], 'Warning'), 'install')

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
