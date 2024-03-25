# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
# Original source code taken from Toga projet.
import asyncio
import contextlib

import gi

gi.require_version('Gtk', '3.0')  # noqa
from gi.repository import Gtk  # noqa


@contextlib.contextmanager
def _place_dlg(parent, dlg):
    try:
        # Place Window on top of parent
        if parent and parent.get_root_window():
            window = parent.get_root_window()
            x = window.left
            y = window.top
            width = window.width
            height = window.height
            # Position Window relative to our GLX Window.
            dlg_width, dlg_height = dlg.get_size()
            dialog_x = x + width / 2 - dlg_width / 2
            dialog_y = y + height / 2 - dlg_height / 2
            dlg.set_position(Gtk.WindowPosition.NONE)
            dlg.move(int(dialog_x), int(dialog_y))
            # Disable the Window
            window.children[0].disabled = True
        yield
    finally:
        # Destroy dialog
        dlg.destroy()
        # Run GTK event loop to destroy the dialog.
        while Gtk.events_pending():
            Gtk.main_iteration()
        # Restore state of parent window
        if parent and parent.get_root_window():
            window.children[0].disabled = False


async def message_dialog(
    parent,
    title,  # Not used with GTK
    message,
    detail,
    message_type,
    buttons,
    success_result=None,
):
    dlg = Gtk.MessageDialog(
        parent=None,
        flags=0,
        message_type=message_type,
        buttons=buttons,
        text=message,
    )
    dlg.format_secondary_text(detail)
    with _place_dlg(parent, dlg):
        # Show the dialog and wait for user input
        response = await asyncio.get_event_loop().run_in_executor(None, dlg.run)
    # Return response.
    return response == success_result


async def info_dialog(parent, title, message, detail=None):
    return await message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
    )


async def question_dialog(parent, title, message, detail=None):
    return await message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        success_result=Gtk.ResponseType.YES,
    )


async def confirm_dialog(parent, title, message, detail=None):
    return await message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.OK_CANCEL,
        success_result=Gtk.ResponseType.OK,
    )


async def error_dialog(parent, title, message, detail=None):
    return await message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
    )


async def warning_dialog(parent, title, message, detail=None):
    return await message_dialog(
        parent=parent,
        title=title,
        message=message,
        detail=detail,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.OK,
    )


async def _file_dialog(parent, title, filename, initial_directory, file_types, multiple_select, action, ok_icon):
    dlg = Gtk.FileChooserDialog(
        parent=None,
        title=title,
        action=action,
    )
    dlg.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
    dlg.add_button(ok_icon, Gtk.ResponseType.OK)

    if filename:
        dlg.set_current_name(filename)

    if initial_directory:
        dlg.set_current_folder(str(initial_directory))

    if file_types:
        for file_type in file_types:
            filter_filetype = Gtk.FileFilter()
            filter_filetype.set_name("." + file_type + " files")
            filter_filetype.add_pattern("*." + file_type)
            dlg.add_filter(filter_filetype)

    if multiple_select:
        dlg.set_select_multiple(True)

    with _place_dlg(parent, dlg):
        # Show the dialog and wait for user input
        response = await asyncio.get_event_loop().run_in_executor(None, dlg.run)
        if response == Gtk.ResponseType.OK:
            if multiple_select:
                result = dlg.get_filenames()
            else:
                result = dlg.get_filename()
        else:
            result = None
    return result


async def file_dialog(parent, title, filename=None, initial_directory=None, file_types=None, multiple_select=False):
    return await _file_dialog(
        parent=parent,
        title=title,
        filename=filename,
        initial_directory=initial_directory,
        file_types=file_types,
        multiple_select=multiple_select,
        action=Gtk.FileChooserAction.OPEN,
        ok_icon=Gtk.STOCK_OPEN,
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
        file_types=None,
        multiple_select=multiple_select,
        action=Gtk.FileChooserAction.SELECT_FOLDER,
        ok_icon=Gtk.STOCK_OPEN,
    )


def username_password_dialog(parent, title, message, username=None):
    return None, None
