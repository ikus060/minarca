# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging

import humanfriendly
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, DictProperty, ObjectProperty

from minarca_client.core import BackupInstance
from minarca_client.core.compat import watch_file
from minarca_client.dialogs import error_dialog, question_dialog
from minarca_client.locale import _
from minarca_client.ui.theme import CCard
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)

Builder.load_string(
    '''
<BackupCard>:
    orientation: "vertical"
    spacing: "20dp"
    focus_behavior: False
    adaptive_height: True

    MDBoxLayout:
        orientation: "horizontal"
        adaptive_height: True
        spacing: "10dp"

        Image:
            source: "remote-backup-64.png" if root.is_remote else "local-backup-64.png"
            fit_mode: "contain"
            size_hint: None, None
            size: "64dp", "64dp"

        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            adaptive_width: False
            minimum_width: 50
            pos_hint: {'center_y': .5}

            CLabel:
                text: _('Online backup') if root.is_remote else _('Local backup')
                text_color: self.theme_cls.primaryColor
                role: "small"

            CLabel:
                text: root.settings.repositoryname or _("No name") if root.settings else ""

        CLabel:
            text:  _('Paused') if root.settings and root.settings.pause_until else _('Active')
            adaptive_width: True
            pos_hint: {'center_y': .5}

        CSwitch:
            active: bool(root.settings and root.settings.pause_until is None)
            adaptive_width: True
            adaptive_height: True
            pos_hint: {'center_y': .5}
            on_active: root.toggle_pause(*args)

    MDBoxLayout:
        orientation: "vertical"
        spacing: "8dp"
        adaptive_height: True

        MDLinearProgressIndicator:
            value: root._disk_usage_pct
            max: 100
            size_hint_y: None
            height: "8dp"

        MDBoxLayout:
            orientation: "horizontal"
            adaptive_height: True

            CLabel:
                text: root.disk_used_text
                text_color: self.theme_cls.onSurfaceColor

            CLabel:
                text: root.disk_total_text
                text_color: self.theme_cls.onSurfaceColor
                halign: "right"

    MDList:
        padding: 0

        # Start / Stop backup
        CListItem:
            divider: True
            on_release: root.stop_start_backup()
            theme_bg_color: "Custom"
            md_bg_color: self.theme_cls.warningContainerColor if root.is_running else self.theme_cls.secondaryContainerColor

            MDListItemSupportingText:
                text: root.stop_start_text

            MDListItemTrailingIcon:
                icon: "stop" if root.is_running else "play"

        # Last Backup Status
        CListItem:
            divider: True
            on_release: root.backup_logs()
            theme_bg_color: "Custom"
            md_bg_color: self.theme_cls.backgroundColor if root.last_backup_success else self.theme_cls.warningContainerColor

            MDListItemSupportingText:
                text:  root.last_status_text

            MDListItemTrailingIcon:
                icon: "chevron-right" if root.last_backup_success else "alert-circle"
                icon_color: self.theme_cls.onSurfaceColor if root.last_backup_success else self.theme_cls.warningColor

        # Server connection
        CListItem:
            divider: True
            on_release: root.backup_connection()
            theme_bg_color: "Custom"
            md_bg_color: self.theme_cls.backgroundColor if root.test_connection_success else self.theme_cls.warningContainerColor

            MDListItemSupportingText:
                text:  root.backup_connection_text

            MDListItemTrailingIcon:
                icon: "chevron-right" if root.test_connection_success else "alert-circle"
                icon_color: self.theme_cls.onSurfaceColor if root.test_connection_success else self.theme_cls.warningColor

        # Backup settings
        CListItem:
            divider: True
            on_release: root.backup_settings()

            MDListItemSupportingText:
                text:  _('Backup configuration')

            MDListItemTrailingIcon:
                icon: "chevron-right"

        # Backup patterns
        CListItem:
            divider: True
            on_release: root.backup_patterns()

            MDListItemSupportingText:
                text:  _('File selection')

            MDListItemTrailingIcon:
                icon: "chevron-right"

        # Advance Backup patterns
        CListItem:
            divider: True
            on_release: root.backup_advance()

            MDListItemSupportingText:
                text:  _('Advance settings')

            MDListItemTrailingIcon:
                icon: "chevron-right"

        # Backup restore
        CListItem:
            divider: True
            on_release: root.backup_restore()

            MDListItemSupportingText:
                text:  _('Restore backup')

            MDListItemTrailingIcon:
                icon: "chevron-right"

'''
)


class BackupCard(CCard):
    instance = ObjectProperty(None)
    settings = ObjectProperty(None)
    status = ObjectProperty(None)
    is_remote = BooleanProperty(True)
    disk_usage = DictProperty({'used': 0, 'total': -1})
    test_connection = ObjectProperty(None)
    in_transition = BooleanProperty(False)

    _status_task = None
    _settings_task = None
    _disk_usage_task = None
    _test_connection_task = None
    _pause_task = None
    _stop_start_task = None

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self):
        """On destroy, make sure to delete task."""
        if self._status_task:
            self._status_task.cancel()
        if self._settings_task:
            self._settings_task.cancel()
        if self._disk_usage_task:
            self._disk_usage_task.cancel()
        if self._test_connection_task:
            self._test_connection_task.cancel()
        if self._pause_task:
            self._pause_task.cancel()
        if self._stop_start_task:
            self._stop_start_task.cancel()

    async def _watch_status(self, instance):
        # Asynchronously watch the status files for changes.
        """
        Special implementation of awatch forcing update after 5 seconds of inativity when running.
        """
        try:
            status = instance.status
            async for unused in watch_file(self.instance.status_file, timeout=status.RUNNING_DELAY):
                self.status.reload()
                self.in_transition = False
                self.property('status').dispatch(self)
        except Exception:
            logger.exception('problem occured while watching status')

    async def _watch_settings(self, instance):
        # Asynchronously watch the status files for changes.
        try:
            async for unused in watch_file(self.instance.config_file):
                self.settings.reload()
                self.property('settings').dispatch(self)
        except Exception:
            logger.exception('problem while watching settings')

    async def _get_disk_usage(self, instance):
        # Get disk usage in different thread since connection error might block request.
        try:
            value = await instance.get_disk_usage()
        except Exception:
            # Network issue or dis not connected.
            logger.warning('problem while retrieving disk usage', exc_info=1)
            value = None
        # Update state.
        if value:
            self.disk_usage = {'used': value[0], 'total': value[1]}
        else:
            self.disk_usage = {'used': 0, 'total': 0}

    @alias_property(bind=['disk_usage'])
    def _disk_usage_pct(self):
        try:
            if self.disk_usage['total'] != 0:
                return int(self.disk_usage['used'] / self.disk_usage['total'] * 100)
        except Exception:
            pass
        return 0

    async def _test_connection(self, instance):
        # Test connectivity with remote server every 5 secs
        try:
            await instance.test_connection()
            self.test_connection = True
        except Exception as e:
            # Exception raise - either server is not responding or disk is not connected.
            self.test_connection = e

    def on_instance(self, widget, instance):
        assert isinstance(instance, BackupInstance)
        # Destroy previous task
        self._cancel_tasks()
        # Schedule update asynchronously.
        self._status_task = asyncio.create_task(self._watch_status(instance))
        self._settings_task = asyncio.create_task(self._watch_settings(instance))
        self._disk_usage_task = asyncio.create_task(self._get_disk_usage(instance))
        self._test_connection_task = asyncio.create_task(self._test_connection(instance))
        # Update status
        self.instance = instance
        self.is_remote = self.instance.is_remote()
        self.status = instance.status
        self.settings = instance.settings

    @alias_property(bind=['disk_usage'])
    def disk_used_text(self):
        used = self.disk_usage.get('used', 0)
        total = self.disk_usage.get('total', 0)
        if total < 0:
            return _('Calculating disk usage')  # Initial value
        elif total == 0:
            return _('Cannot determine disk usage')
        return _('Used space %s') % humanfriendly.format_size(used, binary=1)

    @alias_property(bind=['disk_usage'])
    def disk_total_text(self):
        total = self.disk_usage.get('total', 0)
        humanfriendly.format_size(total)
        if total <= 0:
            return ""
        return _('Total space %s') % humanfriendly.format_size(total, binary=1)

    @alias_property(bind=['status', 'in_transition'])
    def stop_start_text(self):
        if self.in_transition:
            return _('Stopping...') if self.is_running else _('Starting...')
        else:
            if self.is_running:
                action = self.instance.status.action
                if action == 'restore':
                    return _('Stop Restore')
                return _('Stop Backup')
            else:
                return _('Start Backup now')

    @alias_property(bind=['status'])
    def last_status_text(self):
        """Return the last backup description."""
        if self.status and self.status.lastdate:
            value = self.status.lastdate.strftime("%a, %d %b %Y %H:%M")
        else:
            return _('No backup yet')
        action = self.instance.status.action
        if action == 'backup':
            if self.is_running:
                return _('Backup in progress...')
            return _('Last backup: %s') % value
        elif action == 'restore':
            if self.is_running:
                return _('Restore in progress...')
            return _('Last restore: %s') % value
        return ""

    @alias_property(bind=['is_remote', 'test_connection'])
    def backup_connection_text(self):
        if self.test_connection_success:
            # When success, display a label
            return _('Server connection') if self.is_remote else _('Local connection')
        else:
            # Otherwise display a description mesafe.
            return str(self.test_connection)

    @alias_property(bind=['status'])
    def last_backup_success(self):
        """Return corresponding icon depending of the last backup status."""
        return self.status and self.status.current_status in ['SUCCESS', 'RUNNING']

    @alias_property(bind=['status'])
    def last_backup_tooltip(self):
        status = self.status
        if status is None:
            return None
        return status.details

    @alias_property(bind=['status'])
    def is_running(self):
        return self.status and self.status.current_status in ['RUNNING', 'STALE']

    @alias_property(bind=['test_connection'])
    def test_connection_success(self):
        # Success if test server is None (undefined) or True
        return self.test_connection is None or self.test_connection is True

    def toggle_pause(self, widget, value):
        """Called to toggle backup pause feature. Will confirm with user before."""
        # Check if value changed
        cur_value = self.instance.settings.pause_until is None
        if value == cur_value:
            # Do nothing.
            return

        # If backup curently pause, unpause
        if self.instance.settings.pause_until:
            self.instance.pause(delay=0)
            self.property('settings').dispatch(self)
            return

        async def _pause():
            # Confirm with user
            ret = await question_dialog(
                parent=self,
                title=_('Pause Backup Job Confirmation'),
                message=_('Are you sure you want to pause the backup job?'),
                detail=_(
                    'Pausing the backup job will temporarily suspend the ongoing backup process for the next 24 hours. This action may affect the availability of recent data restore points and introduce delays in the backup schedule. Please confirm your intention before proceeding.'
                ),
            )
            self.instance.pause(delay=24 if ret else 0)
            self.property('settings').dispatch(self)

        self._pause_task = asyncio.create_task(_pause())

    def stop_start_backup(self):
        async def _task():
            if not self.instance.is_running():
                self.in_transition = True
                try:
                    self.instance.start_backup(force=True)
                except Exception as e:
                    logger.exception('fail to start backup')
                    await error_dialog(
                        paremt=self,
                        title=_("Start Backup"),
                        message=_("A problem occurred when trying to start the backup process."),
                        detail=_(
                            "This usually indicate a problem with the installation. Try re-installing Minarca Backup."
                        )
                        + '\n'
                        + str(e),
                    )
            else:
                self.in_transition = True
                try:
                    self.instance.stop()
                except Exception as e:
                    logger.exception('fail to stop')
                    await error_dialog(
                        parent=self,
                        title=_("Stop process"),
                        message=_("A problem occurred when trying to stop the process."),
                        detail=str(e),
                    )

        self._stop_start_task = asyncio.create_task(_task())

    def backup_logs(self):
        App.get_running_app().set_active_view('backup_logs.BackupLogs', instance=self.instance)

    def backup_connection(self):
        if self.is_remote:
            App.get_running_app().set_active_view(
                'backup_connection_remote.BackupConnectionRemote', instance=self.instance
            )
        else:
            App.get_running_app().set_active_view(
                'backup_connection_local.BackupConnectionLocal', instance=self.instance
            )

    def backup_settings(self):
        App.get_running_app().set_active_view('backup_settings.BackupSettings', instance=self.instance)

    def backup_patterns(self):
        App.get_running_app().set_active_view('backup_patterns.BackupPatterns', instance=self.instance)

    def backup_restore(self):
        App.get_running_app().set_active_view('backup_restore_date.BackupRestoreDate', instance=self.instance)

    def backup_advance(self):
        App.get_running_app().set_active_view('backup_advance.BackupAdvanceSettings', instance=self.instance)
