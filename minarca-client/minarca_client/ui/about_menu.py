# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging

from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivymd.uix.navigationdrawer.navigationdrawer import MDNavigationDrawer, MDNavigationDrawerDivider

from minarca_client import __version__
from minarca_client.core.compat import open_file_with_default_app
from minarca_client.core.latest import LatestCheck, LatestCheckFailed
from minarca_client.locale import _
from minarca_client.ui.theme import CLabel, CListItem
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)

Builder.load_string(
    '''
<BackupInstanceLabel>:
    text: root.repositoryname
    text_color: self.theme_cls.primaryColor
    padding: 0,0,0,10

<RepositoriesItem>:
    MDListItemSupportingText:
        text: _('Browse')

    MDListItemTrailingIcon:
        icon: "chevron-right"

<SettingsItem>:
    MDListItemSupportingText:
        text: _('Settings')

    MDListItemTrailingIcon:
        icon: "chevron-right"

<HelpItem>:
    MDListItemSupportingText:
        text: _('Get Help')

    MDListItemTrailingIcon:
        icon: "chevron-right"

<AboutMenu>:
    radius: 0
    drawer_type: "modal"
    anchor: "right"
    orientation: "vertical"
    theme_bg_color: "Custom"
    background_color: self.theme_cls.surfaceColor
    padding: 20

    MDNavigationDrawerMenu:
        id: drawer_menu

        CListItem:

            MDListItemSupportingText:
                text: _("Help")

            MDListItemTrailingIcon:
                icon: "chevron-right"

        CListItem:

            MDListItemSupportingText:
                text:  _("Website")

            MDListItemTrailingIcon:
                icon: "chevron-right"

    Image:
        source: "minarca-72.png"
        fit_mode: "contain"
        size_hint: None, None
        height: "72dp"
        width: self.height * self.image_ratio
        pos_hint: {'center_x': .5}

    CLabel:
        text: _('Minarca Agent')
        halign: "center"
        font_style: "Title"
        padding: 0,20,0,0

    CLabel:
        text: _('Version %s') % root.version
        halign: "center"

    CLabel:
        text_color: self.theme_cls.primaryColor
        text: root.update_available_text
        halign: "center"
        padding: 0,10,0,0

    CButton:
        text: _('Update now')
        display: root.update_available
        on_release: root.download_latest()
        role: "small"
        pos_hint: {'center_x': 0.5}

    CLabel:
        text: _('Copyright © 2024 IKUS Software')
        halign: "center"
        padding: 0,30,0,0
        role: "small"
'''
)


#
# Create specific widget class to simplify widget creation on update.
#
class BackupInstanceLabel(CLabel):
    instance = ObjectProperty()

    @alias_property(bind=['instance'])
    def repositoryname(self):
        if self.instance is None:
            return ""
        settings = self.instance.settings
        if self.instance.is_remote():
            return (_("%s on %s") % (settings.repositoryname, settings.remoteurl)).capitalize()
        elif self.instance.is_local() and settings.localcaption:
            return (_("%s on %s") % (settings.repositoryname, settings.localcaption)).capitalize()
        return settings.repositoryname


class RepositoriesItem(CListItem):
    instance = ObjectProperty()

    def on_release(self):
        if self.instance is None:
            return
        url = self.instance.get_repo_url("browse")
        open_file_with_default_app(url)


class SettingsItem(CListItem):
    def on_release(self):
        if self.instance is None:
            return
        url = self.instance.get_repo_url("settings")
        open_file_with_default_app(url)


class HelpItem(CListItem):
    instance = ObjectProperty()

    def on_release(self):
        if self.instance is None:
            return
        url = self.instance.get_help_url()
        open_file_with_default_app(url)


class AboutMenu(MDNavigationDrawer):
    version = __version__
    latest_check = None
    backup = ObjectProperty()
    checking_for_update = BooleanProperty(True)
    update_available = BooleanProperty()
    latest_version = StringProperty()
    _task = None
    _check_update_task = None

    def __init__(self, *args, **kwargs):
        self.latest_check = LatestCheck()
        super().__init__(*args, **kwargs)
        # Trigger check for update on startup.
        self._check_update_task = asyncio.create_task(self._check_latest_version_task())

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self):
        """On destroy, make sure to delete task."""
        if self._check_update_task:
            self._check_update_task.cancel()
        if self._task:
            self._task.cancel()

    def on_backup(self, widget, backup):
        """When backup get assigned, update the menu items."""
        if self._task:
            self._task.cancel()
        self.refresh_menu_items()
        if backup is not None:
            self._task = asyncio.create_task(self._watch_instances_task(backup))

    def refresh_menu_items(self):
        # Clear existing updates
        drawer_menu = self.ids.drawer_menu
        drawer_menu.ids.menu.clear_widgets()
        if self.backup is None:
            return
        # Aka, refresh the button list.
        for instance in self.backup:
            # Label
            label = BackupInstanceLabel()
            label.instance = instance
            drawer_menu.add_widget(label)
            # Browser online or local
            repo = RepositoriesItem()
            repo.instance = instance
            drawer_menu.add_widget(repo)
            # Options specific for remote.
            if instance.is_remote():
                # Online settings
                settings_btn = SettingsItem()
                settings_btn.instance = instance
                drawer_menu.add_widget(settings_btn)
                # Oneline Help.
                help_btn = HelpItem()
                help_btn.instance = instance
                drawer_menu.add_widget(help_btn)
            drawer_menu.add_widget(MDNavigationDrawerDivider())

    @alias_property(bind=['update_available', 'checking_for_update', 'latest_version'])
    def update_available_text(self):
        if self.checking_for_update:
            return _('Checking for updates...')
        elif self.update_available is None:
            return _('Unable to verify update availability at this time.')
        elif self.update_available and self.latest_version:
            return _('New version %s available') % self.latest_version
        else:
            return _('Current version is up-to-date')

    def download_latest(self):
        """Called when user click to update."""
        url = self.latest_check.get_download_url()
        open_file_with_default_app(url)

    async def _check_latest_version_task(self):
        # Query latest version.
        self.checking_for_update = True
        try:

            def _task():
                update_available = not self.latest_check.is_latest()
                latest_version = self.latest_check.get_latest_version()
                return update_available, latest_version

            self.update_available, self.latest_version = await asyncio.get_event_loop().run_in_executor(None, _task)
        except LatestCheckFailed:
            pass
        finally:
            self.checking_for_update = False

    async def _watch_instances_task(self, backup):
        """
        Watch changes to instances.
        """
        try:
            async for unused in backup.awatch():
                self.refresh_menu_items()
        except Exception:
            logger.exception('problem occur while watching backup instances')
