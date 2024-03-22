import asyncio
import os
import unittest

from parameterized import parameterized

from minarca_client.core.compat import IS_LINUX, IS_MAC
from minarca_client.ui.dialogs import (
    confirm_dialog,
    error_dialog,
    file_dialog,
    folder_dialog,
    info_dialog,
    username_password_dialog,
    warning_dialog,
)

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class MainDialogTest(unittest.IsolatedAsyncioTestCase):
    async def _kill_dlg(self):
        pass

    @parameterized.expand([error_dialog, warning_dialog, confirm_dialog, info_dialog])
    async def test_message_dialog(self, dlg):
        # Given a dialog
        coroutine = dlg(parent=None, title='test', message='test', detail='details')
        # When showing the dialog
        task = asyncio.create_task(coroutine)
        await asyncio.sleep(0.5)
        # Then no exception should be raised
        with self.assertRaises(asyncio.exceptions.InvalidStateError):
            task.exception()

    async def test_file_dialog(self):
        coroutine = file_dialog(
            parent=None,
            title='test',
            filename='filename',
            initial_directory=None,
            file_types=None,
            multiple_select=True,
        )
        # When showing the dialog
        task = asyncio.create_task(coroutine)
        await asyncio.sleep(0.5)
        # Then no exception should be raised
        with self.assertRaises(asyncio.exceptions.InvalidStateError):
            task.exception()

    async def test_folder_dialog(self):
        coroutine = folder_dialog(parent=None, title='test', initial_directory=None, multiple_select=True)
        # When showing the dialog
        task = asyncio.create_task(coroutine)
        await asyncio.sleep(0.5)
        # Then no exception should be raised
        with self.assertRaises(asyncio.exceptions.InvalidStateError):
            task.exception()

    @unittest.skipIf(IS_LINUX or IS_MAC, 'feature only implemented on Windows')
    async def test_username_password_dialog(self):
        coroutine = username_password_dialog(parent=None, title='test', message='message', username='myuser')
        # When showing the dialog
        task = asyncio.create_task(coroutine)
        await asyncio.sleep(0.5)
        # Then no exception should be raised
        with self.assertRaises(asyncio.exceptions.InvalidStateError):
            task.exception()
