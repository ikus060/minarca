# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Mar 22, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from minarca_client.locale import _
from minarca_client.core import Backup, RepositoryNameExistsError
from minarca_client.core.exceptions import HttpAuthenticationError
from minarca_client.ui.theme import TEXT_HEADER1, TEXT_SMALL, TEXT_STRONG
from minarca_client.ui.widgets import (B, Dialog, I, P, Spin, T, show_error,
                                       show_warning, show_yes_no)
import PySimpleGUI as sg
import logging
import threading

logger = logging.getLogger(__name__)


_COL_WIDTH = 35


class SetupDialog(Dialog):

    def _get_default_repository_name(self):
        """
        Return a default value for the repository name.
        """
        try:
            import socket
            hostname = socket.gethostname()
        except Exception:
            import platform
            hostname = platform.node()
        return hostname.split('.')[0]

    def _layout(self):

        left = [
            [T(_("Welcome to Minarca !"),
                justification='c', **TEXT_HEADER1)],
            [T(_("To configure Minarca to backup your data, you must provide "
                 "the URL of a Minara server. This information should be "
                 "provided by your system administrator."),
               size=(_COL_WIDTH + 5, 5), justification='c')]
        ]
        right = [
            [T(_("Remote Minarca server"),
               size=(_COL_WIDTH, 1), background_color='#ebebeb', **TEXT_STRONG)],
            [I(size=(_COL_WIDTH, 1), key='remoteurl',
               metadata=self._validate_form, enable_events=True)],
            [T(_('e.g.: https://www.minarca.net/'),
               background_color='#ebebeb', **TEXT_SMALL)],
            # Username
            [T(_("Username"),
               size=(_COL_WIDTH, 1), background_color='#ebebeb', **TEXT_STRONG)],
            [I(size=(_COL_WIDTH, 1), key='username',
               metadata=self._validate_form, enable_events=True)],
            # Password
            [T(_("Password"),
               size=(_COL_WIDTH, 1), background_color='#ebebeb', **TEXT_STRONG)],
            [P(size=(_COL_WIDTH, 1),
               key='password', metadata=self._validate_form, enable_events=True)],
            # Repository name
            [T(_("Repository name"),
               size=(_COL_WIDTH, 1), background_color='#ebebeb', **TEXT_STRONG)],
            [I(size=(_COL_WIDTH, 1), key='repository_name',
               default_text=self._get_default_repository_name(),
               metadata=self._validate_form,
               enable_events=True, pad_bottom=20)],
            # Error message
            [T('', size=(_COL_WIDTH, 1), key='error',
               background_color='#ebebeb', **TEXT_SMALL)],
            # Submit
            [B(_('Submit'), size=(7, 1), key='submit', metadata=self._link_start, disabled=True, bind_return_key=True),
             B(_('Cancel'), size=(7, 1), key='quit', metadata=self.close),
             Spin(key='spin', size=32, background_color='#ebebeb', visible=False)],
        ]

        layout = [[
            sg.Column(left, justification='c', element_justification='c'),
            sg.Column([[sg.Column(right, pad=(19, 19), background_color='#ebebeb')]],
                      background_color='#ebebeb'),
        ]]

        return layout

    def _link(self, remoteurl, username, password, repository_name, force):
        """
        This function should be called in a separate thread to avoid blocking the UI.
        """
        try:
            backup = Backup()
            backup.link(
                remoteurl=remoteurl,
                username=username,
                password=password,
                repository_name=repository_name,
                force=force)
            self.window.write_event_value('callback', self._link_end)
        except RepositoryNameExistsError:
            logger.info('repository name `%s` already exists' %
                        repository_name)
            self.window.write_event_value('callback', self._link_end)
            self.window.write_event_value(
                'callback', self._prompt_link_force)
            return
        except (HttpAuthenticationError) as e:
            self.window.write_event_value('callback', self._link_end)
            self.window.write_event_value('callback', (
                show_warning,
                self.window,
                _('Invalid connection information !'),
                _('Invalid connection information !'),
                _("The information you have entered for the connection to Minarca are invalid.\n\n%s" % str(e))
            ))
            return
        except Exception as e:
            logger.exception('fail to connect')
            self.window.write_event_value('callback', self._link_end)
            self.window.write_event_value('callback', (
                show_error,
                self.window,
                _('Failed to connect to remote server'),
                _('Failed to connect to remote server'),
                _("An error occurred during the connection to Minarca "
                  "server.\n\nDetails: %s" % str(e))
            ))
            return

        # Link completed - Close Window.
        self.close()

    def _link_end(self):
        """
        Call back function when the linking process is completed.
        """
        self.window['spin'].update(visible=False)
        self.window.set_cursor('')

    def _link_start(self, force=False):
        # Start spinning wheel
        self.window['spin'].update(visible=True)
        # Set wait cursor
        self.window.set_cursor('exchange')
        # Start background thread.
        self._thread = threading.Thread(target=self._link, daemon=True, kwargs={
            'remoteurl': self.window['remoteurl'].get(),
            'username': self.window['username'].get(),
            'password': self.window['password'].get(),
            'repository_name': self.window['repository_name'].get(),
            'force': force}).start()

    def _loop(self, event, values):
        # Update animation
        self.window['spin'].update_animation()

    def _prompt_link_force(self):
        button_idx = show_yes_no(
            self.window,
            title=_('Repository name already exists'),
            message=_('Do you want to replace the existing repository ?'),
            detail=_("The repository name you have entered already exists on "
                     "the remote server. If you continue with this repository, "
                     "you will replace it's content using this computer. "
                     "Otherwise, you must enter a different repository name.")
        )
        if not button_idx:
            # Operation cancel by user
            return
        self._link_start(force=True)

    def _validate_form(self):
        """
        Check if the input is valid. Return None if the form is valid.
        Return a message if the form is invalid.
        """
        error = None
        if (not self.window['username'].get()
            or not self.window['password'].get()
                or not self.window['remoteurl'].get()):
            error = _("Enter authentication information.")
        elif not self.window['repository_name'].get():
            error = _(
                "Enter a valid repository name to represent this computer in Minarca.")
        # Update the window status.
        self.window['error'].update(value=error or _(
            'Click Submit button to start connecting.'))
        self.window['submit'].update(
            disabled=bool(error))
