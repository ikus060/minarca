# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import os
import shutil
import unittest

import psutil

from minarca_client.core.compat import IS_LINUX
from minarca_client.dialogs._dialogs_linux_zenity import (
    error_dialog,
    file_dialog,
    folder_dialog,
    info_dialog,
    question_dialog,
    warning_dialog,
)

from .test_dialogs import AbstractDialogTest

DISPLAY = os.environ.get('DISPLAY', False)
ZENITY = shutil.which('zenity')


@unittest.skipIf(not (IS_LINUX and DISPLAY and ZENITY), 'required Linux, a display and zenity')
class ZenityMainDialogTest(AbstractDialogTest, unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        super().setUp()
        # Bind the function to be tested.
        self.error_dialog = error_dialog
        self.file_dialog = file_dialog
        self.folder_dialog = folder_dialog
        self.info_dialog = info_dialog
        self.question_dialog = question_dialog
        self.warning_dialog = warning_dialog

    async def _close_dlg(self, title):
        # Search for zenity window.
        limit = 5
        proc = None
        while proc is None and limit > 0:
            await asyncio.sleep(0.5)
            limit -= 1
            # Loop trough process.
            for p in psutil.process_iter():
                if p.name() == 'zenity':
                    proc = p
        # If windows is not found raise an error
        if not proc:
            self.fail('cannot window with title equals to %s' % title)

        # Kill the zenity process
        proc.kill()
