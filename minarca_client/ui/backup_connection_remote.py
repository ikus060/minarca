# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

from minarca_client.core.compat import get_default_repositoryname
from minarca_client.core.exceptions import BackupError, ConfigureBackupError, RepositoryNameExistsError
from minarca_client.dialogs import question_dialog
from minarca_client.locale import _
from minarca_client.ui.spinner_overlay import SpinnerOverlay  # noqa
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)

Builder.load_string(
    '''
<BackupConnectionRemote>:
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    SidePanel:
        is_remote: True
        create: root.create
        text: _("Provide your login details to configure remote backup.")
        step: 1

    MDFloatLayout:

        MDScrollView:
            size_hint: 1, 1
            pos_hint: {'right': 1}

            MDBoxLayout:
                orientation: "vertical"
                padding: "50dp"
                spacing: "25dp"
                adaptive_height: True

                MDBoxLayout:
                    orientation: "vertical"
                    padding: 0, 0, 0, "15dp"
                    spacing: "15dp"
                    adaptive_height: True

                    CLabel:
                        text: _("Server connexion")
                        font_style: "Title"
                        role: "small"
                        text_color: self.theme_cls.primaryColor

                    CButton:
                        text: _('Reset server connexion')
                        on_release: root.reset()
                        role: "small"
                        theme_bg_color: "Custom"
                        md_bg_color: self.theme_cls.secondaryColor
                        theme_text_color: "Custom"
                        text_color: self.theme_cls.onSecondaryColor
                        display: not root.edit

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

                CTextField:
                    id: repositoryname
                    name: _("Backup name")
                    text: root.repositoryname
                    on_text: root.repositoryname = self.text
                    disabled: not root.edit or root.working

                CTextField:
                    id: remoteurl
                    name: _("Address (IP or domain)")
                    text: root.remoteurl
                    on_text: root.remoteurl = self.text
                    disabled: not root.edit or root.working

                CTextField:
                    id: remoteurl
                    name: _("Username")
                    text: root.username
                    on_text: root.username = self.text
                    disabled: not root.edit or root.working

                CTextField:
                    id: password
                    name: _("Password")
                    text: root.password
                    password: True
                    password_mask: "\u2022"
                    on_text: root.password = self.text
                    disabled: not root.edit or root.working
                    on_text_validate: root.save()

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
                        id: btn_next
                        text: _('Next') if root.create else _('Save')
                        on_release: root.save()
                        opacity: 1 if root.edit else 0
                        disabled: not root.valid or root.working or not root.edit

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


class BackupConnectionRemote(MDBoxLayout):
    edit = BooleanProperty(True)
    create = BooleanProperty(False)
    repositoryname = StringProperty("")
    remoteurl = StringProperty("")
    username = StringProperty("")
    password = StringProperty("")
    working = StringProperty()
    error_message = StringProperty("")
    error_detail = StringProperty("")

    _test_connection_task = None
    _create_remote_task = None
    _forget_task = None

    def __init__(self, backup=None, create=False, instance=None):
        assert backup is not None
        assert create or instance is not None
        self.backup = backup
        self.instance = instance
        self.create = create
        if self.instance is None:
            # If creating a new repo, provide default values
            self.edit = True
            self.repositoryname = get_default_repositoryname()
        else:
            # If editing a repo, fill values with existing settings.
            self.edit = False
            self.repositoryname = self.instance.settings.repositoryname
            self.remoteurl = self.instance.settings.remoteurl
            self.username = self.instance.settings.username
            self.password = '******'
        super().__init__()
        # Check connection to server when editing
        if not create:
            self._test_connection_task = asyncio.create_task(self._test_connection(instance))

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._test_connection_task:
            self._test_connection_task.cancel()
        if self._create_remote_task:
            self._create_remote_task.cancel()
        if self._forget_task:
            self._forget_task.cancel()

    async def _test_connection(self, instance):
        # Test connectivity with remote server.
        try:
            await instance.test_connection()
        except Exception as e:
            # Show error message.
            self.error_detail = str(e)

    @alias_property(bind=['repositoryname', 'remoteurl', 'username', 'password'])
    def valid(self):
        """
        Used to check if the data is valid according to the current step.
        """
        return self.repositoryname and self.remoteurl and self.username and self.password

    def reset(self):
        # When user click on Reset server connexion. Let enable editing.
        self.edit = True
        self.password = ''

    def cancel(self):
        # When operation is cancel by user, redirect it.
        app = App.get_running_app()
        if self.create:
            app.set_active_view('BackupCreate')
        else:
            app.set_active_view('DashboardView')

    def save(self):
        if not self.valid or self.working:
            # Operation should not be accessible if not valid.
            return
        coro = self._create_remote(
            remoteurl=self.remoteurl,
            username=self.username,
            password=self.password,
            repositoryname=self.repositoryname,
        )
        self.working = _('Please wait. Initializing backup on remote server...')
        self._create_remote_task = asyncio.create_task(coro)

    def forget_instance(self):
        assert not self.create

        async def _forget_instance():
            # In edit mode, confirm operation, destroy the configuration and go to dashboard.
            ret = await question_dialog(
                parent=self,
                title=_('Are you sure ?'),
                message=_('Are you sure you want to forget this backup settings?'),
                detail=_('If you forget this settings, the backup will no longer run on schedule.'),
            )
            if not ret:
                # Operation cancel by user.
                return
            self.instance.forget()
            App.get_running_app().set_active_view('DashboardView')

        # Prompt in a different thread.
        self._forget_task = asyncio.create_task(_forget_instance())

    async def _create_remote(self, remoteurl, username, password, repositoryname, force=False):
        # Support IP or Domain name.
        remoteurl = remoteurl if remoteurl.startswith('http') else 'https://' + remoteurl
        try:
            # Create new instance if none exists yet.
            # Asynchronously link to Minarca Server
            self.instance = await self.backup.configure_remote(
                remoteurl=remoteurl,
                username=username,
                password=password,
                repositoryname=repositoryname,
                force=force,
                instance=self.instance,
            )
        except RepositoryNameExistsError as e:
            logger.warning(str(e))
            # If repo already exists remotely, ask to replace it.
            ret = await question_dialog(
                parent=self,
                title=_('Repository name already exists'),
                message=_('Do you want to replace the existing repository ?'),
                detail=_(
                    "The repository name you have entered already exists on "
                    "the remote server. If you continue with this repository, "
                    "you will replace it's content using this computer. "
                    "Otherwise, you must enter a different repository name."
                ),
            )
            if ret:
                await self._create_remote(remoteurl, username, password, repositoryname, force=True)
        except ConfigureBackupError as e:
            logger.warning(str(e))
            self.error_message = e.message
            self.error_detail = e.detail
        except BackupError as e:
            logger.warning(str(e))
            self.error_message = _('Failed to establish connectivity with remote server.')
            self.error_detail = str(e)
        except Exception as e:
            logger.exception('unknown exception')
            self.error_message = _('Unknown problem occured when connecting to the remote server.')
            self.error_detail = _("An error occurred during the connection to Minarca server.\n\nDetails: %s") % str(e)
        else:
            self.error_message = ""
            self.error_detail = ""
            # On success, go to next step
            app = App.get_running_app()
            if self.create:
                app.set_active_view('BackupPatterns', instance=self.instance, create=self.create)
            else:
                app.set_active_view('DashboardView')
        finally:
            self.working = ''
