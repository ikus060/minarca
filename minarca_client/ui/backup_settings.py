# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

from minarca_client.core import BackupInstance
from minarca_client.core.compat import IS_WINDOWS
from minarca_client.core.exceptions import BackupError, HttpAuthenticationError, RemoteRepositoryNotFound
from minarca_client.dialogs import question_dialog, warning_dialog
from minarca_client.locale import _
from minarca_client.ui.spinner_overlay import SpinnerOverlay  # noqa
from minarca_client.ui.utils import alias_property

if IS_WINDOWS:
    from minarca_client.dialogs import username_password_dialog


logger = logging.getLogger(__name__)

Builder.load_string(
    '''
<BackupSettings>:
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    SidePanel:
        is_remote: root.is_remote
        create: root.create
        text: _("Configure your backup settings for personalized data protection.")
        step: 3

    MDFloatLayout:

        CScrollView:
            size_hint: 1, 1
            pos_hint: {'right': 1}

            MDBoxLayout:
                orientation: "vertical"
                padding: "50dp"
                spacing: "25dp"
                adaptive_height: True

                CLabel:
                    text: _('Backup configuration')
                    font_style: "Title"
                    role: "small"
                    text_color: self.theme_cls.primaryColor

                CLabel:
                    text: root.error_message
                    text_color: self.theme_cls.onErrorColor
                    md_bg_color: self.theme_cls.errorColor
                    padding: ("15dp", "12dp")
                    display: root.error_message

                CLabel:
                    text: root.error_detail
                    text_color: self.theme_cls.errorColor
                    display: root.error_detail

                CDropDown:
                    name: _('Backup frequency')
                    value: root.schedule
                    on_value: root.schedule = self.value
                    data: root.schedule_choices

                CCheckbox:
                    text: _("Run whether the user's session is open or not")
                    display: root.show_run_if_logged_out
                    active: root.run_if_logged_out
                    on_active: root.run_if_logged_out = self.active

                CLabel:
                    text: _('Excluded Days of the Week')

                MDGridLayout:
                    cols: 4
                    padding: 0, 0, 0, "10dp"
                    spacing: "10dp"
                    adaptive_height: True

                    CCheckbox:
                        text: _('Monday')
                        active: root.ignore_weekday[0]
                        on_active: root.ignore_weekday[0] = self.active

                    CCheckbox:
                        text: _('Tuesday')
                        active: root.ignore_weekday[1]
                        on_active: root.ignore_weekday[1] = self.active

                    CCheckbox:
                        text: _('Wednesday')
                        active: root.ignore_weekday[2]
                        on_active: root.ignore_weekday[2] = self.active

                    CCheckbox:
                        text: _('Thrusday')
                        active: root.ignore_weekday[3]
                        on_active: root.ignore_weekday[3] = self.active

                    CCheckbox:
                        text: _('Friday')
                        active: root.ignore_weekday[4]
                        on_active: root.ignore_weekday[4] = self.active

                    CCheckbox:
                        text: _('Saturday')
                        active: root.ignore_weekday[5]
                        on_active: root.ignore_weekday[5] = self.active

                    CCheckbox:
                        text: _('Sunday')
                        active: root.ignore_weekday[6]
                        on_active: root.ignore_weekday[6] = self.active

                CDropDown:
                    name: _('Data Retention Duration')
                    value: root.keepdays
                    on_value: root.keepdays = self.value
                    data: root.keepdays_choices
                    # Make this field ReadOnly if user doesn't have permissions to change it.
                    disabled: root.is_remote and root.remoterole == 10 # USER_ROLE

                CDropDown:
                    name: _('Inactivity Notification Period')
                    value: root.maxage
                    on_value: root.maxage = self.value
                    data: root.maxage_choices

                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: "10dp"
                    adaptive_height: True
                    padding: (0, "30dp", 0 , 0)

                    CButton:
                        id: btn_cancel
                        text: _('Back') if root.create else _('Cancel')
                        on_release: root.cancel()
                        disabled: root.working
                        theme_bg_color: "Custom"
                        md_bg_color: self.theme_cls.inverseSurfaceColor

                    CButton:
                        id: btn_save
                        text: _('Next') if root.create else _('Save')
                        on_release: root.save()
                        disabled: root.working

                    Widget:

                    CButton:
                        id: btn_forget
                        style: "text"
                        text: _("Delete backup settings")
                        theme_text_color: "Custom"
                        text_color: self.theme_cls.errorColor
                        md_bg_color: self.theme_cls.backgroundColor
                        on_release: root.forget_instance()
                        display: not root.create

                        MDButtonIcon:
                            theme_icon_color: "Custom"
                            icon_color: self.theme_cls.errorColor
                            icon: "trash-can-outline"

        SpinnerOverlay:
            text: root.working
            display: bool(root.working)

'''
)


class BackupSettings(MDBoxLayout):
    create = BooleanProperty(False)
    is_remote = BooleanProperty(True)
    schedule = NumericProperty(24)
    keepdays = NumericProperty(-1)
    maxage = NumericProperty(3)
    ignore_weekday = ListProperty([False, False, False, False, False, True, True])
    remoterole = NumericProperty(None)
    working = StringProperty()
    error_message = StringProperty("")
    error_detail = StringProperty("")
    show_run_if_logged_out = BooleanProperty(IS_WINDOWS)
    run_if_logged_out = BooleanProperty(False)

    _load_task = None
    _save_task = None
    _forget_task = None
    _run_if_logged_out_task = None

    def __init__(self, backup=None, instance=None, create=False):
        """Edit or create backup configuration for the given instance"""
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        # Initialise the state.
        self.backup = backup
        self.instance = instance
        self.create = create
        self.is_remote = instance.is_remote()
        self.run_if_logged_out = bool(IS_WINDOWS and self.backup.scheduler.run_if_logged_out)

        # Also check user role if user is allowed to change the retention period.
        settings = self.instance.settings
        if settings.remoterole is not None:
            self.remoterole = settings.remoterole
        # Load settings from local values
        if settings.schedule is not None:
            self.schedule = settings.schedule
        if settings.ignore_weekday is not None:
            self.ignore_weekday = [i in settings.ignore_weekday for i in range(0, 7)]
        if settings.maxage is not None:
            self.maxage = settings.maxage
        if settings.keepdays is not None:
            self.keepdays = settings.keepdays
        # Then load remote settings asynchronously if remote.
        if not create and instance.is_remote():
            self.working = _('Please wait. Loading backup settings...')
            self._load_task = asyncio.create_task(self._load())

        # Create the view
        super().__init__()

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._load_task:
            self._load_task.cancel()
        if self._save_task:
            self._save_task.cancel()
        if self._forget_task:
            self._forget_task.cancel()
        if self._run_if_logged_out_task:
            self._run_if_logged_out_task.cancel()

    @alias_property()
    def schedule_choices(self):
        return {-1: _("Manual"), 1: _("Hourly"), 6: _("Four times a day"), 12: _("Twice a day"), 24: _("Once a day")}

    @alias_property()
    def maxage_choices(self):
        return dict(
            [
                (0, _('Never')),
                (1, _('1 day')),
                (2, _('2 days')),
                (3, _('3 days')),
                (4, _('4 days')),
                (5, _('5 days')),
                (6, _('6 days')),
                (7, _('1 week')),
                (14, _('2 weeks')),
                (21, _('3 weeks')),
                (28, _('4 weeks')),
                (31, _('1 month')),
            ]
        )

    @alias_property()
    def keepdays_choices(self):
        return dict(
            [
                (-1, _("Forever")),
                (1, _("1 day")),
                (2, _("2 days")),
                (3, _("3 days")),
                (4, _("4 days")),
                (5, _("5 days")),
                (6, _("6 days")),
                (7, _("1 week")),
                (14, _("2 weeks")),
                (21, _("3 weeks")),
                (30, _("1 month")),
                (60, _("2 months")),
                (90, _("3 months")),
                (120, _("4 months")),
                (150, _("5 months")),
                (180, _("6 months")),
                (210, _("7 months")),
                (240, _("8 months")),
                (270, _("9 months")),
                (300, _("10 months")),
                (330, _("11 months")),
                (365, _("1 year")),
                (730, _("2 years")),
                (1095, _("3 years")),
                (1460, _("4 years")),
                (1825, _("5 years")),
            ]
        )

    async def _load(self):
        try:
            # Get settings from remote server
            await self.instance.load_remote_settings()
            # Update properties accordingly.
            settings = self.instance.settings
            if settings.ignore_weekday is not None:
                self.ignore_weekday = [i in settings.ignore_weekday for i in range(0, 7)]
            if settings.maxage is not None:
                self.maxage = settings.maxage
            if settings.keepdays is not None:
                self.keepdays = settings.keepdays
            if settings.remoterole is not None:
                self.remoterole = settings.remoterole
        except HttpAuthenticationError as e:
            logger.warning(str(e))
            self.error_message = _('Unable to retrieve settings from remote server.')
            self.error_detail = _(
                "This issue may arise due to the remote server being out-of-date. You may edit the settings, however, some settings will not be synchronized with the remote server. If this problem persists, we recommend contacting your administrator for further assistance."
            )
        except BackupError as e:
            logger.warning(str(e))
            self.error_message = str(e)
        except Exception as e:
            logger.exception('unknown exception')
            self.error_message = _('Unable to retrieve configuration from remote server.')
            self.error_detail = _("An error occurred during the connection.\n\nDetails: %s") % str(e)
        else:
            self.error_message = ""
            self.error_detail = ""
        finally:
            self.working = ''

    def cancel(self):
        if self.create:
            # In create mode, return backup to pattern view.
            App.get_running_app().set_active_view('backup_patterns.BackupPatterns', instance=self.instance, create=True)
        else:
            # Otherwise, go to dashboard view.
            App.get_running_app().set_active_view('dashboard.DashboardView')

    def save(self):
        if self.working:
            # Operation should not be accessible if already working.
            return
        self.working = _('Please wait. Saving settings...')
        self._save_task = asyncio.create_task(self._save())

    async def _save(self):
        try:
            # In create mode, save change and go to backup settings.
            t = self.instance.settings
            t.schedule = self.schedule
            t.ignore_weekday = [idx for idx, value in enumerate(self.ignore_weekday) if value]
            t.maxage = self.maxage
            t.keepdays = self.keepdays
            # Asynchronously start backup when creating.
            if self.create:
                self.instance.start_backup(force=True)
            # Asynchronously push settings to remote server.
            if self.instance.is_remote():
                # Wait only if repository is getting created.
                wait = self.create
                await self.instance.save_remote_settings(wait=wait)
            # Finnaly save the changes.
            t.save()
            # Make sure a task scheduler is created at this point.
            self.backup.schedule_job(replace=False)
            # Redirect user to dashboard.
            App.get_running_app().set_active_view('dashboard.DashboardView')

        except RemoteRepositoryNotFound as e:
            logger.warning('fail to save settings remotely', exc_info=1)
            await warning_dialog(
                parent=self,
                title=_('Repository not found'),
                message=_('A problem occured while trying to save the backup settings.'),
                detail=str(e),
            )
        except HttpAuthenticationError:
            ret = await question_dialog(
                parent=self,
                title=_('Authentication failed'),
                message=_('Your settings could not be saved to remote server. Do you want to continue ?'),
                detail=_(
                    'This issue may arise due to the remote server being out-of-date. You have the option to proceed, however, some settings will not be synchronized with the remote server. If this problem persists, we recommend contacting your administrator for further assistance.'
                ),
            )
            if ret:
                # Finnaly save the changes.
                t.save()
                # Redirect user to dashboard.
                App.get_running_app().set_active_view('dashboard.DashboardView')
        except TimeoutError:
            logger.warning('fail to save settings remotely', exc_info=1)
            await warning_dialog(
                parent=self,
                title=_('Save Settings timeout'),
                message=_('A problem occured while trying to save the backup settings.'),
                detail=_(
                    'The operation timeout. Check your internet connection and verify if the remote server is online. If the problem persist contact your administrator.'
                ),
            )
        except Exception as e:
            logger.exception('problem occured while saving backup settings')
            await warning_dialog(
                parent=self,
                title=_('Cannot save settings'),
                message=_(
                    'An unknown problem occured while trying to save the backup settings. If the problem persist contact your administrator.'
                ),
                detail=str(e),
            )
        finally:
            self.working = ''

    def forget_instance(self):
        assert not self.create

        async def _forget_instance():
            # In edit mode, confirm operation, destroy the configuration and go to dashboard.
            ret = await question_dialog(
                parent=self,
                title=_('Are you sure?'),
                message=_('Are you sure you want to forget these backup settings?'),
                detail=_('If you forget these settings, the backup will no longer run on schedule.'),
            )
            if not ret:
                # Operation cancel by user.
                return
            self.instance.forget()
            App.get_running_app().set_active_view('dashboard.DashboardView')

        # Prompt in a different thread.
        self._forget_task = asyncio.create_task(_forget_instance())

    def on_run_if_logged_out(self, widget, value):
        """
        Called to toggle the "run_if_logged_out" settings.
        """
        # This is only applicable to Windows scheduler.
        if not IS_WINDOWS:
            return

        # Do nothing is values are the same
        current_value = self.backup.scheduler.run_if_logged_out
        if value == current_value:
            return

        async def _run_if_logged_out():
            try:
                if not value:
                    # If disable, re-schedule the tasks with default settings.
                    self.backup.schedule_job()
                else:
                    # If enabled, prompt user for password.
                    username, password = username_password_dialog(
                        parent=self, title=_('Windows Credentials'), message=_('Enter credentials for local machine:')
                    )
                    if username and password:
                        self.backup.schedule_job(run_if_logged_out=(username, password))
            except Exception as e:
                message = _('Cannot apply your changes.')
                detail = str(e)
                await warning_dialog(
                    parent=self,
                    title=_('Backup Configuration'),
                    message=message,
                    detail=detail,
                )
            finally:
                self.run_if_logged_out = bool(self.backup.scheduler.run_if_logged_out)

        self._run_if_logged_out_task = asyncio.create_task(_run_if_logged_out())
