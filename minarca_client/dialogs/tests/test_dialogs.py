import asyncio
import os
import unittest

import psutil
from parameterized import parameterized

from minarca_client.core.compat import IS_LINUX, IS_MAC, IS_WINDOWS
from minarca_client.dialogs import (
    error_dialog,
    file_dialog,
    folder_dialog,
    info_dialog,
    question_dialog,
    warning_dialog,
)

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
@unittest.skipIf(IS_MAC, 'mac dialogs are blocking it is not possible to close them programatically')
class MainDialogTest(unittest.IsolatedAsyncioTestCase):
    async def _close_dlg(self, title):
        await asyncio.sleep(0.5)
        if IS_WINDOWS:
            # Send a key "enter" to close the Window.
            import ctypes

            count = 0
            hwnd = None
            while not hwnd and count < 5:
                count += 1
                hwnd = ctypes.windll.user32.FindWindowW(None, title)
                await asyncio.sleep(0.5)
            if hwnd:
                WM_KEYDOWN = 0x0100
                ctypes.windll.user32.PostMessageW(hwnd, WM_KEYDOWN, 0x0D, 0)
            else:
                self.fail('fail to close dialog')

        elif IS_LINUX:
            # Kill the zenity process
            for proc in psutil.process_iter():
                if proc.name() == 'zenity':
                    proc.kill()
                    return
            self.fail('fail to close dialog')

    @parameterized.expand([error_dialog, warning_dialog, question_dialog, info_dialog])
    async def test_message_dialog(self, dlg):
        # Given a dialog
        coroutine = dlg(parent=None, title='test', message='test', detail='details')
        # When showing the dialog
        task = asyncio.create_task(coroutine)
        # Then no exception should be raised
        with self.assertRaises(asyncio.exceptions.InvalidStateError):
            task.exception()
        await self._close_dlg('test')

    async def test_file_dialog(self):
        coroutine = file_dialog(
            parent=None,
            title='test',
            filename='filename',
            initial_directory=None,
            multiple_select=True,
        )
        # When showing the dialog
        task = asyncio.create_task(coroutine)
        await self._close_dlg('test')
        # Then no exception should be raised
        with self.assertRaises(asyncio.exceptions.InvalidStateError):
            task.exception()

    @unittest.skipIf(IS_WINDOWS, 'cannot close dialog on Windows')
    async def test_folder_dialog(self):
        coroutine = folder_dialog(parent=None, title='test', initial_directory=None, multiple_select=True)
        # When showing the dialog
        task = asyncio.create_task(coroutine)
        await self._close_dlg('test')
        # Then no exception should be raised
        with self.assertRaises(asyncio.exceptions.InvalidStateError):
            task.exception()
