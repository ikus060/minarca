# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 30, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from minarca_client.locale import _
from minarca_client.core.compat import IS_WINDOWS
from minarca_client.ui.theme import (MINARCA_ICON, TEXT_DEFAULT, TEXT_STRONG,
                                     TTK_THEME, pull_right)
import PySimpleGUI as sg
import logging
import os
import pkg_resources
import tkinter
import tkinter.messagebox


def _wrap(func, *default_args, **defaults_kwargs):
    """
    Wrapper around PySimpleUI widget to provide default attributes values and to support cascading style.
    """

    def _func(*args, **overrides):
        # Process cascading style passed as args.
        kwargs = defaults_kwargs.copy()
        style = overrides.pop('style', None)
        if style:
            if isinstance(style, dict):
                style = [style]
            for s in style:
                kwargs.update(s)
        kwargs.update(overrides)

        # handle pad_*
        if 'pad_left' in kwargs or 'pad_right' in kwargs or 'pad_top' in kwargs or 'pad_bottom' in kwargs:
            kwargs['pad'] = (((kwargs.pop('pad_left', 5), kwargs.pop(
                'pad_right', 5)), (kwargs.pop('pad_top', 3), kwargs.pop('pad_bottom', 3))))
        widget = func(*default_args, *args, **kwargs)
        return widget

    return _func


DOT = '\u2022'
ELLIPSIS = '\u2026'
TRASH = 'X' if IS_WINDOWS else chr(128465)  # trash unicode

BM = ButtonMenu = _wrap(sg.ButtonMenu, pad=(3, 3), **TEXT_DEFAULT)
HR = _wrap(sg.HorizontalSeparator, color='#bbbbbb', pad=(0, 25))
I = Input = _wrap(sg.InputText, **TEXT_DEFAULT)
P = Password = _wrap(sg.Input, password_char=DOT, **TEXT_DEFAULT)
C = Combo = _wrap(sg.Combo, **TEXT_DEFAULT)

Window = _wrap(
    sg.Window, _('Minarca Backup'),
    icon=MINARCA_ICON,
    debugger_enabled=os.environ.get('MINARCA_DEBUG', None),
    ttk_theme=TTK_THEME)


def show_info(parent, title, message, detail):
    assert parent and hasattr(parent, 'TKroot')
    tkinter.messagebox.showinfo(
        parent=parent.TKroot,
        title=title,
        message=message,
        detail=detail)


def show_warning(parent, title, message, detail):
    assert parent and hasattr(parent, 'TKroot')
    tkinter.messagebox.showwarning(
        parent=parent.TKroot,
        title=title,
        message=message,
        detail=detail)


def show_error(parent, title, message, detail):
    assert parent and hasattr(parent, 'TKroot')
    tkinter.messagebox.showerror(
        parent=parent.TKroot,
        title=title,
        message=message,
        detail=detail)


def show_yes_no(parent, title, message, detail, default='no'):
    assert parent and hasattr(parent, 'TKroot')
    return tkinter.messagebox.askyesno(
        parent=parent.TKroot,
        title=title,
        message=message,
        detail=detail,
        default=default)


def show_ok_cancel(parent, title, message, detail, default='cancel'):
    assert parent and hasattr(parent, 'TKroot')
    return tkinter.messagebox.askokcancel(
        parent=parent.TKroot,
        title=title,
        message=message,
        detail=detail,
        default=default)


class Button(sg.Button):
    """
    Custom button implementation to allow defining `cursor` as widget creation.
    """

    def __init__(self, *args, **kwargs):
        self._cursor = kwargs.pop('cursor', None)
        sg.Button.__init__(self, *args, **kwargs)

    def __setattr__(self, name, value):
        # Intercept when button is create.
        if name == 'TKButton' and value is not None and self._cursor:
            self.set_cursor(self._cursor)
        sg.Button.__setattr__(self, name, value)  # @UndefinedVariable


B = Button = _wrap(Button, pad=(3, 3), cursor='hand2', **TEXT_DEFAULT)


class Dialog():

    def close(self):
        """
        May be called to send a close signal to the window.
        """
        self.window.write_event_value(None, None)

    def create(self, *args, **kwargs):
        """
        Create the window.
        """
        self.window = Window(self._layout(), *args, **kwargs)

        # Display and interact with the Window using an Event Loop
        self.window.read(timeout=0)
        self._initialize()

    def _finalize(self):
        """
        Called before the window get destroyed.
        """
        pass

    def _initialize(self):
        """
        Called after the window get created.
        """
        pass

    def _handle_exception(self, e):
        """
        Called when an exception is catch in the main loop.
        """
        logging.exception("fatal error")
        show_error(
            self.window,
            _("Fatal error occurred"),
            _("Fatal error occurred"),
            _("A fatal problem occurred while executing this operation. This "
              "indicate a a problem with Minarca. It's recommended to close "
              "the application and try again."),
        )

    def _layout(self):
        """
        Called to create the layout.
        """
        return [[Text('Override _layout()')]]

    def _loop(self, event, values):
        """
        Call at regular interval in event loop.
        """
        pass

    def open(self, *args, **kwargs):
        """
        Open the dialog and start the event loop. This call return when the
        dialog is closed.
        """
        self.create(*args, **kwargs)
        while not self.window.TKrootDestroyed:
            try:
                self.pump_events()
            except Exception as e:
                self._handle_exception(e)

    def pump_events(self):
        event, values = self.window.read(timeout=100)
        # See if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED:
            self._finalize()
            self.window.close()
            return

        # Allow sub-classes to do something in event loop.
        self._loop(event, values)

        # Handle basic action using metadata callback.
        func = None
        element = self.window.find_element(event, silent_on_error=True)
        if element and element.metadata:
            if isinstance(element.metadata, tuple):
                func, args = element.metadata[0], element.metadata[1:]
            elif hasattr(element.metadata, '__call__'):
                func, args = element.metadata, []

        # Handle callback in a similar way
        if event == 'callback':
            if isinstance(values['callback'], tuple):
                func, args = values['callback'][0], values['callback'][1:]
            else:
                func, args = (values['callback'], [])

        if func:
            func(*args)


class PatternItem(sg.Column):

    def __init__(self, parent):
        assert parent
        self._parent = parent
        self._pattern = None
        self._label = T('', size=(35, 1), ellipsis='center', **TEXT_STRONG)
        self._toggle = B('', metadata=None)
        self._del = B(_(TRASH), tooltip=_('Remove'))

        self._column = sg.Column([
            [self._label, pull_right([[self._toggle, self._del]])],
            [HR()],
        ], visible=False, expand_x=True)
        sg.Column.__init__(self, [[self._column, sg.Canvas(size=(0, 0), pad=(0, 0))]], pad=(
            0, 0), expand_x=True, expand_y=False)

    def update(self, pattern):
        self._pattern = pattern
        btn_label = _('Included') if pattern and pattern.include else _(
            'Excluded')
        new_label = '' if pattern is None else pattern.comment or pattern.pattern
        new_tooltip = pattern.pattern if pattern else ''
        new_visible = pattern is not None
        # Update or save the new values within the item.
        self._label.update(value=new_label, tooltip=new_tooltip)
        if self.Widget is None:
            self._toggle.ButtonText = btn_label
            self._column._visible = new_visible
        else:
            self._toggle.update(text=btn_label)
            self._column.update(visible=new_visible)
        # Sets metadata.
        self._toggle.metadata = (self._parent.metadata, 'toggle', pattern)
        self._del.metadata = (self._parent.metadata, 'delete', pattern)


class PatternList(sg.Column):
    """
    Custom class to hold the logic related to adding and removing patterns from/to a Column widget.
    """
    _idx = 0

    def __init__(self, initial_capacity=5, handle_delete=None, handle_include=None, ** kwargs):
        self._items = [PatternItem(self) for unused in range(initial_capacity)]
        self._handle_delete = handle_delete
        self._handle_include = handle_include

        layout = [[sg.Canvas(size=(0, 0), pad=(0, 0))]]
        layout += [[item] for item in self._items]
        sg.Column.__init__(self, layout, scrollable=True,
                           vertical_scroll_only=True, **kwargs)

    def add(self, pattern):
        """
        Add a pattern to be displayed in the widget. Could be called before
        or after the widget creation.
        """
        if self._idx >= len(self._items):
            new_items = [PatternItem(self)
                         for unused in range(len(self._items))]
            self._items += new_items
            layout = [[item] for item in new_items]
            if self.Widget is not None:
                self.ParentForm.extend_layout(self, layout)
            else:
                for row in layout:
                    self.add_row(*row)
        self._items[self._idx].update(pattern=pattern)
        self._idx += 1
        if self.Widget is not None:
            self.ParentForm.visibility_changed()
            self.contents_changed()

    def index(self, pattern):
        """
        Get the index of a pattern.
        """
        for idx, item in enumerate(self._items):
            if item._pattern == pattern:
                return idx
        raise ValueError()

    def remove(self, pattern):
        """
        Used to remove the given pattern from the widget. `pattern`. Could be a
        pattern object or a pattern index. Could be
        call before or after the widget creation.
        """
        assert pattern
        idx = self.index(pattern)
        self._items[idx].update(pattern=None)
        if self.Widget is not None:
            self.ParentForm.visibility_changed()
            self.contents_changed()

    def set_pattern(self, idx, pattern):
        """
        Used to replace/update the the item at the given index.
        """
        assert 0 <= idx and idx < len(self._items)
        assert pattern
        self._items[idx].update(pattern=pattern)

    def set_patterns(self, patterns):
        """
        Used to set the list of pattern to be displayed in the widget. Could be
        call before or after the widget creation.
        """
        if len(self._items) < len(patterns):
            # Need to create more items.
            new_items = [PatternItem(self)
                         for unused in range(len(patterns) - len(self._items))]
            self._items += new_items
            layout = [[item] for item in new_items]
            if self.Widget is not None:
                self.ParentForm.extend_layout(self, layout)
            else:
                for row in layout:
                    self.add_row(*row)
        elif len(self._items) > len(patterns):
            # Need to hide other items.
            for item in self._items[len(patterns):]:
                item.update(pattern=None)
        # Update all the items.
        for idx, p in enumerate(patterns):
            self._items[idx].update(pattern=p)
        self._idx = len(patterns)

        # Refresh the widgets (if required).
        if self.Widget is not None:
            self.ParentForm.visibility_changed()
            self.contents_changed()


class Spin(sg.Image):
    """
    Widget to display a spinning wheel.
    """

    def __init__(self, *args, size=32, **kwargs):
        self._filename = pkg_resources.resource_filename(
            __name__, 'images/spin_%s.gif' % size)
        sg.Image.__init__(self, self._filename, *args, **kwargs)

    def update_animation(self):
        if self._visible:
            sg.Image.update_animation(
                self, self._filename, time_between_frames=100)


class Text(sg.Text):
    """
    Text widget supporting text ellipsis and allow updates before and
    after widget creation.
    """

    def __init__(self, *args, **kwargs):
        self._ellipsis = kwargs.pop('ellipsis', None)
        self._wrap = kwargs.pop('wrap', False)
        sg.Text.__init__(self, *args, **kwargs)
        # Keep reference to the original value.
        self._text = self.DisplayText
        self._tooltip = self.Tooltip
        # Replace them if required by ellipsis.
        self.DisplayText = self._get_text(self.DisplayText)
        if self._tooltip is None and self.DisplayText != self._text:
            self.Tooltip = self._text

    def _get_text(self, value):
        """
        Return the text to be displayed on the widget considering the size of
        the widget and the ellipsis option.
        """
        x, unused = self.Size
        if self._ellipsis and x and len(value) > x:
            if self._ellipsis in ['prefix', 'start']:
                return ELLIPSIS + value[-x:]
            elif self._ellipsis in ['middle', 'center']:
                return value[0:int(x / 2)] + ELLIPSIS + value[-int(x / 2):]
            else:
                return value[0:x] + ELLIPSIS
        return value

    def update(self, value=None, background_color=None, text_color=None, font=None, visible=None, tooltip=None):
        # Update tooltip
        if tooltip is not None:
            self.set_tooltip(tooltip)
        # Update text
        if value is not None:
            self._text = value
            value = self.DisplayText = self._get_text(value)
            if self._tooltip is None and self.DisplayText != self._text:
                self.Tooltip = self._text
        # Support update even if widget is not created.
        if self.Widget is None:
            return
        sg.Text.update(self, value=value, background_color=background_color,
                       text_color=text_color, font=font, visible=visible)

    def set_tooltip(self, tooltip_text):
        """
        Sets the tooltip text to the given string arguments or None to indicate the uses of default tool tip to be used.
        """
        self._tooltip = tooltip_text

        # Determine the tooltip to be displayed.
        if self._tooltip is not None:
            self.Tooltip = self._tooltip
        elif self._tooltip is None and self.DisplayText != self._text:
            self.Tooltip = self._text

        # Support update even if widget is not created.
        if self.Widget is None:
            return

        sg.Text.set_tooltip(self, self.Tooltip)

    def __setattr__(self, name, value):
        sg.Text.__setattr__(self, name, value)  # @UndefinedVariable
        # Intercept when widget is create.
        if name == 'Widget' and value is not None and self._wrap:
            value.bind('<Configure>', lambda e: value.config(wraplen=value.winfo_width()))


T = Text = _wrap(Text, pad=(0, 0), **TEXT_DEFAULT)
