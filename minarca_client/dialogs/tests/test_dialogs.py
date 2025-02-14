import asyncio
import os
import unittest
from pathlib import Path

from parameterized import parameterized

from minarca_client.core.compat import IS_WINDOWS
from minarca_client.dialogs import (
    error_dialog,
    file_dialog,
    folder_dialog,
    info_dialog,
    question_dialog,
    warning_dialog,
)


class AbstractDialogTest:
    def setUp(self):
        super().setUp()
        # Bind the function to be tested.
        self.error_dialog = error_dialog
        self.file_dialog = file_dialog
        self.folder_dialog = folder_dialog
        self.info_dialog = info_dialog
        self.question_dialog = question_dialog
        self.warning_dialog = warning_dialog

    @parameterized.expand(['error_dialog', 'warning_dialog', 'question_dialog', 'info_dialog'])
    async def test_message_dialog(self, dlg):
        dlg_func = getattr(self, dlg)
        # Given a dialog
        coroutine = dlg_func(parent=None, title='test', message='test', detail='details')
        # When showing the dialog
        await asyncio.gather(coroutine, self._close_dlg('test'))

    @parameterized.expand([None, os.getcwd(), Path.cwd()])
    async def test_file_dialog(self, initial_directory):
        dlg_func = getattr(self, 'file_dialog')
        coroutine = dlg_func(
            parent=None,
            title='test',
            initial_directory=initial_directory,
            multiple_select=True,
        )
        # When showing the dialog
        # Then no exception should be raised
        await asyncio.gather(coroutine, self._close_dlg('test'))

    @parameterized.expand([None, os.getcwd(), Path.cwd()])
    async def test_folder_dialog(self, initial_directory):
        dlg_func = getattr(self, 'folder_dialog')
        coroutine = dlg_func(parent=None, title='test', initial_directory=initial_directory, multiple_select=True)
        # When showing the dialog
        # Then no exception should be raised
        # On Windows, the dialog always has the same name.
        await asyncio.gather(coroutine, self._close_dlg('Browse for folder' if IS_WINDOWS else 'test'))


@unittest.skipIf(not IS_WINDOWS, 'Specific test for windows')
class WindowDialogTest(AbstractDialogTest, unittest.IsolatedAsyncioTestCase):
    async def _close_dlg(self, title):

        import ctypes

        limit = 5
        hwnd = None
        while not hwnd and limit > 0:
            await asyncio.sleep(0.5)
            limit -= 1
            hwnd = ctypes.windll.user32.FindWindowW(None, title)
        # If windows is not found raise an error
        if not hwnd:
            self.fail('cannot windows with title equals to %s' % title)

        # Send a key "enter" to close the Window. (working for message dialog)
        WM_KEYDOWN = 0x0100
        ctypes.windll.user32.PostMessageW(hwnd, WM_KEYDOWN, 0x0D, 0)
        await asyncio.sleep(0.1)
        hwnd = ctypes.windll.user32.FindWindowW(None, title)
        if not hwnd:
            return

        # If windows still exists, send a WM_CLOSE signal (working for file dialog)
        WM_CLOSE = 0x0010
        ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        await asyncio.sleep(0.1)
        hwnd = ctypes.windll.user32.FindWindowW(None, title)
        if not hwnd:
            return

        # If windows still exists, raise an error
        self.fail('fail to close dialog')
