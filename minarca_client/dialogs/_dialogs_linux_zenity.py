# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
# Inspired from Kivy Plyer. Make use of executable
# available on the platform to open the proper dialog.
#
# Avoid importing GTK stuff directly as it fetch too much
# stuff during packaging.
import asyncio
import os

from ._common import disable


async def _message_dialog(
    parent,
    title,
    message,
    detail,
    message_type,
    success_result=None,
):
    assert message_type in ['info', 'error', 'warning', 'question']
    cmd = ['zenity']
    # Add message type
    cmd.append('--%s' % message_type)
    # Add options
    if title:
        cmd.append('--title=%s' % title)
    if message and detail:
        cmd.append('--text=<b>%s</b>\n\n%s' % (message, detail))
        cmd.append('--width=520')
    else:
        cmd.append('--text=%s' % message)
    if parent and parent.get_parent_window():
        cmd.append('--modal')
    with disable(parent):
        proc = await asyncio.create_subprocess_exec(cmd[0], *cmd[1:])
        response = await proc.wait()
    return response == success_result


async def info_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type='info',
    )


async def question_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type='question',
        success_result=0,
    )


async def error_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type='error',
    )


async def warning_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type='warning',
    )


async def _file_dialog(parent, title, initial_directory, multiple_select, directory=False):
    cmd = ['zenity']
    # Add message type
    cmd.append('--file-selection')
    if directory:
        cmd.append('--directory')
    if multiple_select:
        cmd.append('--multiple')
    if initial_directory:
        cmd.append('--filename=%s' % initial_directory)
    cmd.append('--separator=|')
    # Add options
    if title:
        cmd.append('--title=%s' % title)
    if parent and parent.get_parent_window():
        # Zenity --attach is deprecated. So dont use it.
        cmd.append('--modal')
    with disable(parent):
        proc = await asyncio.create_subprocess_exec(cmd[0], *cmd[1:], stdout=asyncio.subprocess.PIPE)
        stdout, _unused = await proc.communicate()
        # Use FS encoding
        stdout = os.fsdecode(stdout)
        # Zenity output a newline
        stdout = stdout.strip('\n')
        # If multi select, always return a list of files.
        if multiple_select:
            return stdout.split('|') if stdout else None
        return stdout if stdout else None


async def file_dialog(parent, title, initial_directory=None, multiple_select=False):
    return await _file_dialog(
        parent=parent,
        title=title,
        initial_directory=initial_directory,
        multiple_select=multiple_select,
    )


async def folder_dialog(
    parent,
    title,
    initial_directory=None,
    multiple_select=False,
):
    return await _file_dialog(
        parent=parent,
        title=title,
        initial_directory=initial_directory,
        multiple_select=multiple_select,
        directory=True,
    )
