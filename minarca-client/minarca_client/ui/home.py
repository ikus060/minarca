# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Mar 22, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from PySimpleGUI.PySimpleGUI import popup_get_file, popup_get_folder
from minarca_client.locale import _
from minarca_client.core import Backup
from minarca_client.core.compat import get_home
from minarca_client.core.config import Pattern, Settings
from minarca_client.core.exceptions import RunningError
from minarca_client.ui.theme import (BUTTON_LIST, BUTTON_SUCCESS, TEXT_DANGER,
                                     TEXT_DEFAULT, TEXT_HEADER1, TEXT_STRONG, TEXT_SUCCESS, TEXT_WARNING,
                                     pull_right, BUTTON_LINK)
from minarca_client.ui.widgets import (B, C, Dialog, HR, PatternList, T,
                                       show_yes_no, show_error)
import PySimpleGUI as sg
import threading
import webbrowser
import logging

logger = logging.getLogger(__name__)

PATTERN_LIST = 'pattern_list'
TOGGLE_PATTERN = 'toggle_pattern'
UNLINK = 'unlink'
HEADER = 'header'
LAST_BACKUP = 'last_backup'
START_STOP = 'start_stop'
FREQUENCY = 'frequency'
VIEWS = ['home', 'patterns', 'schedule']


class HomeDialog(Dialog):

    def __init__(self):
        self.backup = Backup()

    def _finalize(self):
        """
        Called before windows get destroyed to stop the watchdog thread.
        """
        self._stop_event.set()
        self._thread.join()

    def _get_backup_health_text(self):
        """
        Return a human description of backup health base on configuration and last result.
        """
        lastresult = self.backup.get_status('lastresult')
        if lastresult == 'SUCCESS':
            return _('Backup is healthy'), TEXT_SUCCESS
        elif lastresult == 'FAILURE':
            return _('Backup failed'), TEXT_WARNING
        elif lastresult == 'RUNNING':
            return _('Backup in progress'), TEXT_SUCCESS
        elif lastresult == 'STALE':
            return _('Backup is stale'), TEXT_DANGER
        elif lastresult == 'INTERRUPT':
            return _('Backup was interrupted'), TEXT_WARNING
        elif lastresult == 'UNKNOWN':
            return _('No backup yet'), TEXT_DEFAULT
        else:
            return _('Backup is not healthy'), TEXT_DANGER

    def _get_frequencies(self):
        """
        Return the list of available frequency.
        """
        return [
            (Settings.HOURLY, _('Hourly')),
            (Settings.DAILY, _('Daily')),
            (Settings.WEEKLY, _('Weekly')),
            (Settings.MONTHLY, _('Monthly')),
        ]

    def _get_frequency_label(self, value):
        """
        Return the label associated with the value.
        """
        for item in self._get_frequencies():
            if item[0] == value:
                return item[1]
        return None

    def _get_frequency_value(self, label):
        """
        Return the value associated with the label.
        """
        for item in self._get_frequencies():
            if item[1] == label:
                return item[0]
        return None

    def _get_last_backup_text(self):
        """
        Return text to be displayed for "last backup" with appropriate style.
        """
        status = self.backup.get_status()
        lastresult = status['lastresult']
        lastdate = status['lastdate']
        details = status['details']
        if lastresult == 'SUCCESS':
            return _('Complete successfully on %s. No background jobs using system resources.') % lastdate, TEXT_SUCCESS
        elif lastresult == 'FAILURE':
            return _('Last backup failed on %s for the following reason: %s\nNo background jobs using system resources.') % (lastdate, details), TEXT_WARNING
        elif lastresult == 'RUNNING':
            return _('Backup is currently running in background and using system resources.'), TEXT_SUCCESS
        elif lastresult == 'STALE':
            return _('Was started in background on %s, but is currently stale an may use system resources.') % lastdate, TEXT_WARNING
        elif lastresult == 'INTERRUPT':
            return _('Was interrupted on %s. May be caused by loss of connection, computer standby or manual interruption.\nNo background jobs using system resources.') % lastdate, TEXT_WARNING
        elif lastresult == 'UNKNOWN':
            return _('Initial backup need to be started. You may take time to configure your parameters and start your initial backup manually.\nNo background jobs using system resources.'), TEXT_DEFAULT
        raise ValueError()

    def _get_remote_text(self):
        settings = self.backup.get_settings()
        return str(settings.get('remoteurl', '')), '%s @ %s::%s' % (settings.get('username', ''), settings.get('remotehost', ''), settings.get('repositoryname', ''))

    def _get_start_stop_text(self):
        lastresult = self.backup.get_status('lastresult')
        if lastresult in ['RUNNING', 'STALE']:
            return _('Stop backup')
        else:
            return _('Start backup')

    def _handle_add_file(self):
        filenames = popup_get_file(
            message=_('Select file(s) to be include or exclude from backup.'),
            no_window=True,
            multiple_files=True,
            initial_folder=get_home(),
        )
        if not filenames:
            # Operation cancel by user
            return
        # Check if the file is already in the pattern list.
        patterns = self.backup.get_patterns()
        existing_filenames = [p.pattern for p in patterns]
        for fn in filenames:
            if fn in existing_filenames:
                continue
            p = Pattern(True, fn, None)
            patterns.append(p)
            # Add pattern to the list.
            self.window[PATTERN_LIST].add(p)

        # Save the pattern file
        self.backup.set_patterns(patterns)

    def _handle_add_folder(self):
        folder = popup_get_folder(
            message=_('Select folder(s) to be include or exclude from backup.'),
            no_window=True,
            initial_folder=get_home(),
        )
        if not folder:
            # Operation cancel by user
            return
        # Check if the file is already in the pattern list.
        patterns = self.backup.get_patterns()
        existing_filenames = [p.pattern for p in patterns]
        if folder in existing_filenames:
            return
        p = Pattern(True, folder, None)
        patterns.append(p)
        # Add pattern to the list.
        self.window[PATTERN_LIST].add(p)

        # Save the pattern file
        self.backup.set_patterns(patterns)

    def _handle_add_pattern(self):
        pass

    def _handle_default_pattern(self):
        """
        This handler is called to restore defaults pattern list.
        """
        # Prompt the user to confirm
        btn = show_yes_no(
            self.window,
            _('Are you sure ?'),
            _('Are you sure you want to restore the default file specification ?'),
            _('This action will replace all your custom templates with the predefined file specification for your operating system.'))
        if not btn:
            # Operation cancel by user
            return
        # Restore patterns.
        patterns = self.backup.get_patterns()
        patterns.defaults()
        self.backup.set_patterns(patterns)
        # Update widget
        self.window[PATTERN_LIST].set_patterns(patterns)

    def _handle_delete_pattern(self, pattern=None):
        """
        This handler is called to remove the given pattern from the pattern list.
        """
        assert pattern
        patterns = self.backup.get_patterns()
        if pattern in patterns:
            patterns.remove(pattern)
            self.backup.set_patterns(patterns)
            self.window[PATTERN_LIST].remove(pattern)

    def _handle_frequency(self):
        """
        Handler called when user select a new schedule.
        """
        # From the selected label, get the real value.
        schedule_label = self.window[FREQUENCY].get()
        value = self._get_frequency_value(schedule_label)
        # Store the settings
        self.backup.schedule(value)

    def _handle_pattern_list(self, action=None, pattern=None):
        """
        This handler is called whenever the user click on Included/Excluded or
        "X" to delete a pattern.
        """
        assert action
        assert pattern
        if action == 'delete':
            self._handle_delete_pattern(pattern)
        else:
            self._handle_toggle_pattern(pattern)

    def _handle_remote_url(self):
        """
        Handler called when user click on the URL link for minarca remote server.
        """
        remote_url = self.backup.get_remote_url()
        webbrowser.open(remote_url)

    def _handle_show_home(self):
        self._show('home')

    def _handle_show_patterns(self):
        self._show('patterns')

    def _handle_show_schedule(self):
        self._show('schedule')

    def _handle_start_stop_backup(self):
        """
        This handler is called to start/stop backup processing.
        """
        try:
            self.backup.start(True, fork=True)
        except RunningError:
            self.backup.stop()
        except Exception:
            logger.exception('fail to start backup')
            show_error(
                self.window,
                _("Fail to start backup !"),
                _("Fail to start backup !"),
                _("A fatal error occurred when trying to start the backup process. This usually indicate a problem with the installation. Try re-installing Minarca Backup.")
            )

    def _handle_toggle_pattern(self, pattern=None):
        assert pattern
        patterns = self.backup.get_patterns()
        if pattern in patterns:
            new_pattern = Pattern(not pattern.include,
                                  pattern.pattern, pattern.comment)
            idx = patterns.index(pattern)
            patterns[idx] = new_pattern
            self.backup.set_patterns(patterns)
            # Update widget
            idx = self.window[PATTERN_LIST].index(pattern)
            self.window[PATTERN_LIST].set_pattern(idx, new_pattern)

    def _handle_unlink(self):
        """
        Called to un register this agent from minarca server.
        """
        return_code = show_yes_no(
            self.window,
            _('Are you sure ?'),
            _('Are you sure you want to disconnect this Minarca agent ?'),
            _('If you disconnect this computer, this Minarca agent will erase its identity and will no longer run backup on schedule.'))
        if not return_code:
            # Operation cancel by user.
            return

        self.backup.unlink()
        self.window.close()

    def _initialize(self):
        """
        Called after window creation to start the watchdog thread.
        """
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._watch_status, daemon=True)
        self._thread.start()

    def _layout(self):
        left = [
            [B(_('Home'),
               metadata=self._handle_show_home,
               **BUTTON_LIST)],
            [B(_('Select files'),
               metadata=self._handle_show_patterns,
               **BUTTON_LIST)],
            [B(_('Schedule'),
               metadata=self._handle_show_schedule,
               **BUTTON_LIST)]]
        left_column_style = {
            'expand_x': True,
            'expand_y': True,
            'pad': (5, 5),
        }
        return [[
            # Left column
            sg.Column(left, vertical_alignment='top', pad=(5, 5)),
            # Right Column
            sg.Column(self._layout_home(),
                      key='home', **left_column_style),
            sg.Column(self._layout_patterns(),
                      key='patterns', visible=False, **left_column_style),
            sg.Column(self._layout_schedule(),
                      key='schedule', visible=False, **left_column_style),
        ]]

    def _layout_home(self):
        """
        Generate the layout for the Home view.
        """
        header_text, header_style = self._get_backup_health_text()
        start_stop_text = self._get_start_stop_text()
        last_backup_text, last_backup_style = self._get_last_backup_text()
        remote_text, remote_tooltip = self._get_remote_text()
        return [
            # Header
            [T(header_text, key=HEADER, size=(18, 1), style=[header_style, TEXT_HEADER1]),
             pull_right([[B(start_stop_text, key=START_STOP, size=(15, 2), pad=(0, 0), metadata=self._handle_start_stop_backup, **BUTTON_SUCCESS)]])],
            [HR()],
            # Last Backup
            [T(_('Last backup'), size=(15, 1), **TEXT_STRONG),
             pull_right(T(last_backup_text, key=LAST_BACKUP, size=(40, 4), justification='right', **last_backup_style))],
            [HR()],
            # Remote
            [T(_('Remote'), size=(15, 1), **TEXT_STRONG),
             pull_right(B(remote_text, tooltip=remote_tooltip, metadata=self._handle_remote_url, **BUTTON_LINK))],
            [sg.Column([[
                B(_('Disconnect'), pad=(0, 0), metadata=self._handle_unlink)
            ]], pad=(0, 0), justification='right')],
        ]

    def _layout_patterns(self):
        """
        Generate the layout for the Files views used to include and exclude files.
        """
        pattern_list = PatternList(
            key=PATTERN_LIST,
            expand_x=True, expand_y=True,
            metadata=self._handle_pattern_list)
        pattern_list.set_patterns(self.backup.get_patterns())
        return [
            [T(_('Select files'), **TEXT_HEADER1)],
            [T(_('Select file and folder to include or exclude from backup.'), wrap=True)],
            [B(_('Add File'), metadata=self._handle_add_file),
             B(_('Add Folder'), metadata=self._handle_add_folder),
             B(_('Add Pattern'), metadata=self._handle_add_pattern),
             B(_('Restore defaults'), metadata=self._handle_default_pattern)],
            [pattern_list],
        ]

    def _layout_schedule(self):
        """
        Generate the layout for the schedule view.
        """
        # Get the value selected by user.
        schedule_value = self.backup.get_settings('schedule')
        selected_label = self._get_frequency_label(schedule_value)
        labels = [f[1] for f in self._get_frequencies()]
        return [
            [T(_('Schedule'), **TEXT_HEADER1)],
            [T(_('Select how often you want your backup to be performed.'), wrap=True)],
            [HR()],
            [T(_('Frequency'), size=(15, 1), **TEXT_STRONG),
             pull_right(C(
                 values=labels,
                 default_value=selected_label,
                 key=FREQUENCY,
                 size=(12, 1),
                 readonly=True,
                 enable_events=True,
                 metadata=self._handle_frequency))],
            [HR()],
        ]

    def open(self):
        """
        Open the dialog and start the event loop.
        """
        return Dialog.open(self, margins=(0, 0), size=(970, 500))

    def _show(self, view_name):
        assert view_name in VIEWS
        for name in VIEWS:
            visible = name == view_name
            self.window[name].update(visible=visible)
            if visible:
                self.window[name].expand(expand_x=True, expand_y=True)

    def _update_status(self):
        """
        Update all the widget with the new status.
        """
        # Get status values.
        header_text, header_style = self._get_backup_health_text()
        start_stop_text = self._get_start_stop_text()
        last_backup_text, last_backup_style = self._get_last_backup_text()
        # Update status.
        self.window[HEADER].update(
            value=header_text,
            **header_style)
        self.window[START_STOP].update(
            text=start_stop_text)
        self.window[LAST_BACKUP].update(
            value=last_backup_text,
            **last_backup_style)

    def _watch_status(self):
        """
        Used to watch the status file and trigger an update whenever the status changes.
        """
        last_status = self.backup.get_status()
        while not self._stop_event.wait(timeout=.5):
            status = self.backup.get_status()
            if last_status != status:
                self.window.write_event_value('callback', self._update_status)
