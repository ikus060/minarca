# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import objc  # noqa
from AppKit import NSURL, NSAlert, NSOpenPanel

from minarca_client.locale import gettext as _

from ._common import disable

NSAlertStyleWarning = 0
NSAlertStyleInformational = 1
NSAlertStyleCritical = 2

NSAlertFirstButtonReturn = 1000
NSAlertSecondButtonReturn = 1001
NSAlertThirdButtonReturn = 1002


async def _message_dialog(
    parent, title, message, detail, alert_style, buttons=None, success_result=NSAlertFirstButtonReturn
):
    alert = NSAlert.alloc().init()
    alert.setMessageText_(message)
    alert.setInformativeText_(detail)
    if alert_style:
        alert.setAlertStyle_(alert_style)
    if buttons:
        for label in buttons:
            alert.addButtonWithTitle_(label)
    with disable(parent):
        ret = alert.runModal()
        # TODO support beginSheetModalForWindow.
        # Show the dialog and wait for user input
        # response = await asyncio.get_event_loop().run_in_executor(None, alert.runModal)
    # Return response.
    return ret == success_result


async def info_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        alert_style=NSAlertStyleInformational,
    )


async def question_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        alert_style=NSAlertStyleInformational,
        buttons=(_("Yes"), _("No")),
        success_result=NSAlertFirstButtonReturn,
    )


async def error_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent, title=title, message=message, detail=detail, alert_style=NSAlertStyleCritical
    )


async def warning_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent, title=title, message=message, detail=detail, alert_style=NSAlertStyleWarning
    )


async def _open_panel(parent, title, filename, initial_directory=None, multiple_select=False, open_file=True):
    panel = NSOpenPanel.openPanel()
    panel.setCanChooseDirectories_(not open_file)
    panel.setCanChooseFiles_(open_file)
    panel.setCanCreateDirectories_(True)
    # panel.setShowsHiddenFiles_(self.show_hidden)

    if title:
        panel.setTitle_(title)

    if initial_directory:
        url = NSURL.fileURLWithPath_(str(initial_directory))
        panel.setDirectoryURL_(url)

    if multiple_select:
        panel.setAllowsMultipleSelection_(True)

    ret = panel.runModal()
    if not ret:
        return None

    if multiple_select:
        return panel.filenames()
    else:
        return panel.filename()


async def file_dialog(parent, title, initial_directory=None, multiple_select=False):
    return await _open_panel(parent, title, initial_directory, multiple_select, open_file=True)


async def folder_dialog(
    parent,
    title,
    initial_directory=None,
    multiple_select=False,  # Not supported in Window.
):
    return await _open_panel(parent, title, None, initial_directory, multiple_select, open_file=False)
