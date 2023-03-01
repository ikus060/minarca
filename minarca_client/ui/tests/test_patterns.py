'''
Created on Jul. 20, 2021

@author: ikus060
'''
import os
import tempfile
import tkinter
import unittest
import unittest.mock
from contextlib import contextmanager

from minarca_client.core.compat import IS_LINUX
from minarca_client.core.config import Pattern
from minarca_client.ui.home import HomeDialog

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@contextmanager
def home_dialog():
    cwd = os.getcwd()
    tmp = tempfile.TemporaryDirectory()
    os.chdir(tmp.name)
    os.environ['MINARCA_CONFIG_HOME'] = tmp.name
    os.environ['MINARCA_DATA_HOME'] = tmp.name
    os.environ['MINARCA_CHECK_LATEST_VERSION'] = 'False'

    def pump_events():
        while dlg.root.dooneevent(tkinter._tkinter.ALL_EVENTS | tkinter._tkinter.DONT_WAIT):
            pass

    dlg = HomeDialog()
    dlg.pump_events = pump_events
    dlg.set_active_view('patterns')
    dlg.pump_events()
    try:
        yield dlg
    finally:
        dlg.destroy()
        dlg.pump_events()
        os.chdir(cwd)
        tmp.cleanup()


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class PatternsViewTest(unittest.TestCase):
    def test_open_patterns(self):
        # Given a home dialog with default patterns
        with home_dialog() as dlg:
            # When showing the patterns view.
            # Then it contains the list of existing patterns.
            self.assertEqual(
                len(dlg.backup.get_patterns()),
                len(dlg.patterns_view.scrolled_frame.interior.winfo_children()[0].winfo_children()),
            )

    @unittest.mock.patch(
        'tkinter.filedialog.askopenfilenames', return_value=['/home/this_is_a_file', '/home/this_is_another_file']
    )
    def test_add_file_pattern(self, mock_askopenfilenames):
        # Given a home dialog with default patterns
        with home_dialog() as dlg:
            self.assertEqual(0, len(dlg.backup.get_patterns()))
            # When adding a new patterns
            dlg.patterns_view.add_file_pattern()
            dlg.pump_events()
            # Then the pattern is added in the widget.
            self.assertEqual(2, len(dlg.backup.get_patterns()))
            self.assertEqual(
                len(dlg.backup.get_patterns()),
                len(dlg.patterns_view.scrolled_frame.interior.winfo_children()[0].winfo_children()),
            )

    @unittest.mock.patch('tkinter.filedialog.askdirectory', return_value='/home/')
    def test_add_folder_pattern(self, mock_askdirectory):
        # Given a home dialog with default patterns
        with home_dialog() as dlg:
            self.assertEqual(0, len(dlg.backup.get_patterns()))
            # When adding a new patterns
            dlg.patterns_view.add_folder_pattern()
            dlg.pump_events()
            # Then the pattern is added in the widget.
            self.assertEqual(1, len(dlg.backup.get_patterns()))
            self.assertEqual(
                len(dlg.backup.get_patterns()),
                len(dlg.patterns_view.scrolled_frame.interior.winfo_children()[0].winfo_children()),
            )

    @unittest.mock.patch('tkinter.simpledialog.askstring', return_value='new-pattern')
    def test_add_custom_pattern(self, mock_askstring):
        # Given a home dialog with default patterns
        with home_dialog() as dlg:
            self.assertEqual(0, len(dlg.backup.get_patterns()))
            # When adding a new patterns
            dlg.patterns_view.add_custom_pattern()
            dlg.pump_events()
            # Then the pattern is added in the widget.
            self.assertEqual(1, len(dlg.backup.get_patterns()))
            self.assertEqual(
                len(dlg.backup.get_patterns()),
                len(dlg.patterns_view.scrolled_frame.interior.winfo_children()[0].winfo_children()),
            )

    def test_remove_pattern(self):
        # Given a home dialog with default patterns
        with home_dialog() as dlg:
            item1 = Pattern(True, 'new-pattern1', None)
            item2 = Pattern(True, 'new-pattern2', None)
            item3 = Pattern(True, 'new-pattern3', None)
            item4 = Pattern(True, 'new-pattern4', None)
            dlg.backup.set_patterns([item1, item2, item3, item4])
            dlg.patterns_view.data['patterns'] = dlg.backup.get_patterns()
            self.assertEqual(4, len(dlg.backup.get_patterns()))
            # When removing a pattern
            dlg.patterns_view.remove_pattern(item1)
            dlg.pump_events()
            # Then the pattern is added in the widget.
            self.assertEqual(3, len(dlg.backup.get_patterns()))
            self.assertEqual(
                len(dlg.backup.get_patterns()),
                len(dlg.patterns_view.scrolled_frame.interior.winfo_children()[0].winfo_children()),
            )

    def test_toggle_pattern(self):
        # Given a home dialog with default patterns
        with home_dialog() as dlg:
            item = Pattern(True, 'new-pattern', None)
            dlg.backup.set_patterns([item])
            dlg.patterns_view.data['patterns'] = dlg.backup.get_patterns()
            self.assertEqual(1, len(dlg.backup.get_patterns()))
            # When toggling a pattern
            dlg.patterns_view.toggle_pattern(item)
            dlg.pump_events()
            # Then the pattern is added in the widget.
            self.assertEqual(1, len(dlg.backup.get_patterns()))
            self.assertFalse(dlg.backup.get_patterns()[0].include)
