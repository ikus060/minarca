# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import ctypes
import functools
import locale
import os
from ctypes.wintypes import INT

import pywintypes
import win32api
import win32cred
import winerror
from win32com.shell import shell, shellcon
from win32con import OFN_ALLOWMULTISELECT, OFN_EXPLORER
from win32gui import GetOpenFileNameW, PyGetBufferAddressAndLen, SendMessage

from ._common import disable

# Icons
PWSTR = ctypes.c_wchar_p
TD_WARNING_ICON = PWSTR(0xFFFF)
TD_ERROR_ICON = PWSTR(0xFFFE)
TD_INFORMATION_ICON = PWSTR(0xFFFD)
TD_SHIELD_ICON = PWSTR(0xFFFC)

# Available Buttons
TDCBF_OK_BUTTON = 0x0001
TDCBF_YES_BUTTON = 0x0002
TDCBF_NO_BUTTON = 0x0004
TDCBF_CANCEL_BUTTON = 0x0008
TDCBF_RETRY_BUTTON = 0x0010
TDCBF_CLOSE_BUTTON = 0x0020

# Return code.
IDOK = 1
IDCANCEL = 2
IDABORT = 3
IDRETRY = 4
IDIGNORE = 5
IDYES = 6
IDNO = 7
IDCLOSE = 8
IDHELP = 9
IDTRYAGAIN = 10
IDCONTINUE = 11
IDTIMEOUT = 32000

_task_dialog = ctypes.WinDLL('comctl32.dll').TaskDialog
ref = ctypes.byref


def task_dialog(owner, title, main_instr, content, buttons, icon, inst=None):
    res = INT()
    hr = _task_dialog(owner, inst, title, main_instr, content, buttons, icon, ctypes.byref(res))
    if hr < 0:
        raise ctypes.WinError(hr)
    return res.value


async def _message_dialog(parent, title, message, detail, icon, buttons, success_result=None):
    owner = None
    if parent and parent.get_root_window():
        owner = parent.get_root_window().get_window_info().window
    func = functools.partial(
        task_dialog,
        owner=owner,
        title=title,
        main_instr=message,
        content=detail,
        buttons=buttons,
        icon=icon,
    )
    with disable(parent):
        # Show the dialog and wait for user input
        response = await asyncio.get_event_loop().run_in_executor(None, func)
    # Return response.
    return response == success_result


async def info_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        icon=TD_INFORMATION_ICON,
        buttons=TDCBF_OK_BUTTON,
    )


async def question_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        icon=TD_INFORMATION_ICON,
        buttons=TDCBF_YES_BUTTON | TDCBF_NO_BUTTON,
        success_result=IDYES,
    )


async def error_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        icon=TD_ERROR_ICON,
        buttons=TDCBF_OK_BUTTON,
    )


async def warning_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        icon=TD_WARNING_ICON,
        buttons=TDCBF_OK_BUTTON,
    )


async def file_dialog(parent, title, initial_directory=None, multiple_select=False):
    if initial_directory is None:
        initial_directory = os.getcwd()  # noqa: PTH109

    flags = OFN_EXPLORER
    if multiple_select:
        flags = flags | OFN_ALLOWMULTISELECT
    ext_filter = "All Files\0*.*\0"
    owner = None
    if parent and parent.get_root_window():
        owner = parent.get_root_window().get_window_info().window
    func = functools.partial(
        GetOpenFileNameW,
        hwndOwner=owner,
        InitialDir=str(initial_directory),
        File=None,
        Flags=flags,
        Title=title,
        MaxFile=2**16,
        Filter=ext_filter,
        DefExt=None,
    )

    with disable(parent):
        try:
            file_path, _, _ = await asyncio.get_event_loop().run_in_executor(None, func)
        except pywintypes.error as error:
            if error.winerror == 0:
                # Operation cancel by user.
                return None
            raise IOError from error

    # The return value is separated by NULLL byte
    paths = file_path.split("\0")

    if len(paths) == 1:
        # User selected a single file.
        # If multi select, return an array.
        return paths if multiple_select else paths[0]
    # User selected multiple file.
    return [os.path.join(paths[0], p) for p in paths[1:]]


async def folder_dialog(
    parent,
    title,
    initial_directory=None,
    multiple_select=False,  # Not supported in Window.
):
    # http://timgolden.me.uk/python/win32_how_do_i/browse-for-a-folder.html
    owner = 0
    if parent and parent.get_root_window():
        owner = parent.get_root_window().get_window_info().window

    def _set_start_folder(hwnd, msg, lp, data):
        if msg == shellcon.BFFM_INITIALIZED and data:
            data = str(data).encode(locale.getpreferredencoding(), errors='replace')
            address, _ = PyGetBufferAddressAndLen(data)
            SendMessage(hwnd, shellcon.BFFM_SETSELECTION, 1, address)

    BIF_NEWDIALOGSTYLE = 0x00000040
    func = functools.partial(
        shell.SHBrowseForFolder,
        owner,
        None,
        title,
        shellcon.BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE | shellcon.BIF_EDITBOX,
        _set_start_folder,
        initial_directory,  # 'data' param for the callback
    )

    with disable(parent):
        try:
            pidl, _, _ = await asyncio.get_event_loop().run_in_executor(None, func)
        except pywintypes.error as error:
            if error.winerror == 0:
                # Operation cancel by user.
                return None
            raise IOError from error
    if pidl is None:
        # Operation cancel by user.
        return None
    if multiple_select:
        return [shell.SHGetPathFromIDListW(pidl)]
    return shell.SHGetPathFromIDListW(pidl)


def username_password_dialog(parent, title, message, username=None):
    """
    Display message dialog to ask for username and password.
    """
    # https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-creduicmdlinepromptforcredentialsa
    owner = None
    if parent and parent.get_root_window():
        owner = parent.get_root_window().get_window_info().window

    username = username or win32api.GetUserName()
    uiinfo = {
        "Parent": owner,
        "MessageText": message,
        "CaptionText": title,
    }
    with disable(parent):
        # When excuted in secondary thread, it's not working.
        try:
            target, pwd, _ = win32cred.CredUIPromptForCredentials(
                TargetName=win32api.GetComputerName(),
                AuthError=0,
                UserName=username,
                Flags=win32cred.CREDUI_FLAGS_DO_NOT_PERSIST,
                Save=False,
                UiInfo=uiinfo,
            )
        except pywintypes.error as e:
            # Operation cancel by user.
            if e.winerror == winerror.ERROR_CANCELLED:
                return username, None
            raise
    return target, pwd
