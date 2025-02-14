# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
# Inspired from Kivy Plyer. Make use of executable
# available on the platform to open the proper dialog.
#
# Avoid importing KDE stuff directly as it fetch too much
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
    assert message_type in ["info", "error", "warning", "question"]

    cmd = ["kdialog"]
    type_map = {
        "info": ["--msgbox", f"{message}\n{detail}" if detail else message],
        "error": ["--detailederror", message, detail] if detail else ["--error", message],
        "warning": ["--detailedsorry", message, detail] if detail else ["--sorry", message, detail],
        "question": ["--yesno", f"{message}\n{detail}" if detail else message],
    }
    cmd.extend(type_map[message_type])

    if title:
        cmd.append(f"--title={title}")

    if parent and parent.get_parent_window():
        winfo = parent.get_parent_window().get_window_info().window
        cmd.append(f"--attach={winfo}")

    with disable(parent):
        proc = await asyncio.create_subprocess_exec(*cmd)
        response = await proc.wait()

    return response == success_result


async def info_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type="info",
    )


async def question_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type="question",
        success_result=0,
    )


async def error_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type="error",
    )


async def warning_dialog(parent, title, message, detail=None):
    return await _message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type="warning",
    )


async def _file_dialog(parent, title, initial_directory, multiple_select, directory=False):
    cmd = ["kdialog"]

    # Define dialog type
    if directory:
        cmd.append("--getexistingdirectory")
    else:
        if multiple_select:
            cmd.append("--multiple")
            cmd.append("--separate-output")
        cmd.append("--getopenfilename")

    if initial_directory:
        cmd.append(initial_directory)

    if title:
        cmd.append(f"--title={title}")

    if parent and parent.get_parent_window():
        winfo = parent.get_parent_window().get_window_info().window
        cmd.append('--attach=%s' % winfo)

    with disable(parent):
        proc = await asyncio.create_subprocess_exec(cmd[0], *cmd[1:], stdout=asyncio.subprocess.PIPE)
        stdout, _unused = await proc.communicate()
        stdout = os.fsdecode(stdout).strip()

        # If multiple files selected, split by newline
        if multiple_select and stdout:
            return stdout.split("\n")
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
    multiple_select=False,  # Not supported by KDialog.
):
    return await _file_dialog(
        parent=parent,
        title=title,
        initial_directory=initial_directory,
        multiple_select=multiple_select,
        directory=True,
    )
