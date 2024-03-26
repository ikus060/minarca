# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
# Inspired from Kivy Plyer. Make use of executable
# available on the platform to open the proper dialog.
#
# Avoid importing GTK stuff directly as it fetch too much
# stuff during packaging.
import asyncio
import contextlib
import os


@contextlib.contextmanager
def _disable(parent):
    try:
        # Place Window on top of parent
        if parent and parent.get_root_window():
            # Disable the Window
            window = parent.get_root_window()
            window.children[0].disabled = True
        yield
    finally:
        # Restore state of parent window
        if parent and parent.get_root_window():
            window.children[0].disabled = False


async def _message_dialog(
    parent,
    title,
    message,
    detail,
    message_type,
    success_result=None,
):
    assert message_type in ['info', 'error', 'warning', 'question', 'file-selection']
    cmd = ['zenity']
    # Add message type
    cmd.append('--%s' % message_type)
    # Add options
    if title:
        cmd.append('--title=%s' % title)
    if message and detail:
        cmd.append('--text=<b>%s</b>\n%s' % (message, detail))
    else:
        cmd.append('--text=%s' % message)
    if parent and parent.get_parent_window():
        winfo = parent.get_parent_window().get_window_info().window
        cmd.append('--attach=%s' % winfo)
    with _disable(parent):
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


async def _file_dialog(parent, title, filename, initial_directory, multiple_select, directory=False):
    cmd = ['zenity']
    # Add message type
    cmd.append('--file-selection')
    if directory:
        cmd.append('--directory')
    if multiple_select:
        cmd.append('--multiple')
    if filename:
        cmd.append('--filename=%s' % filename)
    elif initial_directory:
        cmd.append('--filename=%s' % initial_directory)
    cmd.append('--separator=|')
    # Add options
    if title:
        cmd.append('--title=%s' % title)
    if parent and parent.get_parent_window():
        # Zenity --attach is deprecated. So dont use it.
        cmd.append('--modal')
    with _disable(parent):
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


async def file_dialog(parent, title, filename=None, initial_directory=None, multiple_select=False):
    return await _file_dialog(
        parent=parent,
        title=title,
        filename=filename,
        initial_directory=initial_directory,
        multiple_select=multiple_select,
    )


async def folder_dialog(
    parent,
    title,
    initial_directory=None,
    multiple_select=False,  # Not supported in Window.
):
    return await _file_dialog(
        parent=parent,
        title=title,
        filename=None,
        initial_directory=initial_directory,
        multiple_select=multiple_select,
        directory=True,
    )


def username_password_dialog(parent, title, message, username=None):
    return None, None
