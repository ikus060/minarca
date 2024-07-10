# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging
import os

import humanfriendly
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDListItem

from minarca_client.core.compat import IS_LINUX, IS_WINDOWS, get_default_repositoryname
from minarca_client.core.disk import LocationInfo, get_location_info, list_disks
from minarca_client.core.exceptions import ConfigureBackupError, LocalDestinationNotFound, RepositoryNameExistsError
from minarca_client.dialogs import folder_dialog, question_dialog, warning_dialog
from minarca_client.locale import _
from minarca_client.ui.spinner_overlay import SpinnerOverlay  # noqa
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)


Builder.load_string(
    '''
<LocationItem>:
    divider:
    adaptive_height: True
    theme_bg_color: "Custom"
    md_bg_color: self.theme_cls.secondaryContainerColor if root.selected else self.theme_cls.surfaceColor

    MDListItemLeadingIcon:
        icon_color: self.theme_cls.primaryColor if root.check_criterias else self.theme_cls.onSurfaceColor
        icon: "alert-circle-outline" if root.check_criterias else "harddisk"

    MDListItemHeadlineText:
        text: root.title

    MDListItemSupportingText:
        text: root.details

    MDListItemTertiaryText:
        theme_text_color: "Custom"
        text_color: self.theme_cls.primaryColor
        text: root.check_criterias or " "


<BackupConnectionLocal>:
    id: backup_connection_local
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    SidePanel:
        is_remote: False
        create: root.create
        text: _("Select an location to be used for backing up your data.")
        step: 1

    MDRelativeLayout:

        MDBoxLayout:
            orientation: "vertical"
            padding: "50dp"
            spacing: "25dp"

            MDBoxLayout:
                orientation: "vertical"
                padding: 0, 0, 0, "15dp"
                spacing: "15dp"
                adaptive_height: True

                CLabel:
                    text: _("Target location")
                    font_style: "Title"
                    role: "small"
                    text_color: self.theme_cls.primaryColor

                CButton:
                    text: _('Reset target location')
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

            CBoxLayout:
                orientation: "horizontal"
                spacing: "10dp"
                display: root.edit
                adaptive_height: True

                CButton:
                    id: btn_refresh
                    text: _('Refresh')
                    on_release: root.refresh_locations()
                    role: "small"
                    theme_bg_color: "Custom"
                    md_bg_color: self.theme_cls.secondaryColor
                    theme_text_color: "Custom"
                    text_color: self.theme_cls.onSecondaryColor

                CButton:
                    id: btn_browse
                    text: _('Browse')
                    on_release: root.select_custom_location()
                    role: "small"
                    theme_bg_color: "Custom"
                    md_bg_color: self.theme_cls.secondaryColor
                    theme_text_color: "Custom"
                    text_color: self.theme_cls.onSecondaryColor

            CCard:
                orientation: "vertical"
                padding: "1dp"

                CLabel:
                    text: _("No external drive has been detected for data backup. Plug in your external drive and click on the refresh button to update this list. If your device is not on the list, check its connectivity and make sure it's switched on.")
                    size_hint_x: 1
                    halign: "center"
                    padding: "20dp", "50dp", "20dp", "50dp"
                    display: not root.sorted_locations

                RecycleView:
                    viewclass: "LocationItem"
                    data: root.sorted_locations

                    RecycleBoxLayout:
                        spacing: "1dp"
                        padding: "0dp"
                        default_size: None, "88dp"
                        default_size_hint: 1, None
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height

            MDBoxLayout:
                orientation: "horizontal"
                spacing: "10dp"
                adaptive_height: True

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


class LocationItem(MDListItem):
    location_info = ObjectProperty()
    selected = BooleanProperty()
    on_location_item_release = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def remove_widget(self, widget, *args, **kwargs):
        super().remove_widget(widget, *args, **kwargs)

    def on_release(self):
        if callable(self.on_location_item_release):
            self.on_location_item_release(self)
        return super().on_release()

    @alias_property(bind=['location_info'])
    def title(self):
        if not self.location_info:
            return ""
        # When user select a subdirectory in a mountpoint, let display the path.
        if self.location_info.relpath != '.':
            return _("%s on %s") % (self.location_info.relpath, self.location_info.caption)
        return self.location_info.caption

    @alias_property(bind=['location_info'])
    def details(self):
        if not self.location_info:
            return ""
        # When size cannot be detected, it's because the disk is not connected.
        if self.location_info.size is None and self.location_info.free is None:
            return str(LocalDestinationNotFound())
        size = humanfriendly.format_size(self.location_info.size)
        free = humanfriendly.format_size(self.location_info.free)
        fstype = self.location_info.fstype or ""
        text = _("%s Drive with %s available space") % (size, free)
        if fstype:
            text += _(" \u2022 Format %s") % fstype
        return text

    @alias_property(bind=['location_info'])
    def check_criterias(self):
        if not self.location_info:
            return ""
        # Check disk criteria.
        if self.location_info.removable is False:
            return _("Make sure to use a removable storage device for backups to avoid data loss.")
        elif self.location_info.fstype in ['vfat', 'FAT32', 'msdos']:
            return _("FAT32 file system is not recommended for backup.")
        if IS_LINUX and self.location_info.fstype in ['ntfs']:
            return _("NTFS is not recommended for backup on Linux.")
        elif self.location_info.free and self.location_info.free <= 250 * 1000 * 1000 * 1000:
            # Warn if the disk space available is less then 250 GiB.
            return _("Available disk space at this location is limited.")
        return ""


class BackupConnectionLocal(MDBoxLayout):
    working = StringProperty()
    edit = BooleanProperty(True)
    create = BooleanProperty(False)
    repositoryname = StringProperty("")
    removable_locations_loading = BooleanProperty(False)
    locations = ListProperty([])
    selected_location = ObjectProperty(None, allownone=True)
    error_message = StringProperty("")
    error_detail = StringProperty("")

    _create_local_task = None
    _refresh_locations_task = None
    _select_custom_location_task = None
    _forget_task = None

    def __init__(self, backup=None, create=False, instance=None):
        self.backup = backup
        self.instance = instance
        self.create = create
        # Allow editing when creating new repo.
        self.edit = self.instance is None
        super().__init__()
        # Refresh locations on creation
        self.refresh_locations()
        if self.instance is None:
            # Define default repo name on creation
            self.repositoryname = get_default_repositoryname()
        else:
            self.repositoryname = instance.settings.repositoryname

    @alias_property(bind=['locations', 'selected_location'])
    def sorted_locations(self):
        available_locations = self.locations
        # Add custom location to the list.
        if self.selected_location and self.selected_location not in available_locations:
            available_locations.insert(0, self.selected_location)
        return [
            {
                'location_info': i,
                'selected': i == self.selected_location,
                'on_location_item_release': self.on_location_item_release,
            }
            for i in self.locations
        ]

    def on_location_item_release(self, location_item):
        # Change selected location when user click on it.
        self.selected_location = location_item.location_info

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._refresh_locations_task:
            self._refresh_locations_task.cancel()
        if self._select_custom_location_task:
            self._select_custom_location_task.cancel()
        if self._create_local_task:
            self._create_local_task.cancel()
        if self._forget_task:
            self._forget_task.cancel()

    async def _refresh_locations(self):
        """
        Every couple of seconds, check if the list of local disks get updated.
        """
        if self.instance is not None:
            # If instance is configure, load current disk
            try:
                local_disk = await asyncio.get_event_loop().run_in_executor(None, self.instance.find_local_destination)
                self.selected_location = local_disk
            except LocalDestinationNotFound:
                self.selected_location = LocationInfo(
                    device=None,
                    mountpoint=self.instance.settings.localmountpoint,
                    relpath=self.instance.settings.localrelpath,
                    caption=self.instance.settings.localcaption,
                    free=None,
                    used=None,
                    size=None,
                    fstype=None,
                    removable=None,
                )
            finally:
                self.removable_locations_loading = False
        else:
            try:
                disks = await asyncio.get_event_loop().run_in_executor(None, list_disks, True)
                self.locations = disks
            except Exception:
                logger.warning('fail to list removable disks', exc_info=1)
            finally:
                self.removable_locations_loading = False

    async def _create_local(self, location, repositoryname, force=False):
        assert location
        assert repositoryname

        # Get full path of selected location
        path = os.path.join(location.mountpoint, location.relpath)

        # Create a new backup instance configuration.
        try:
            # If the relpath is the root of the external drive,
            # will create additonal directory structure using the reponame.
            # TODO Consider moving this part into configure_local
            if location.relpath == '.':
                path = os.path.join(location.mountpoint, "minarca", repositoryname)
                os.makedirs(path, exist_ok=True)
            self.instance = await self.backup.configure_local(
                path=path,
                repositoryname=repositoryname,
                force=force,
                instance=self.instance,
            )
        except PermissionError as e:
            logger.warning(str(e))
            self.error_message = _("You don't have permissions to write at this location.")
            self.error_detail = str(e)
        except RepositoryNameExistsError as e:
            logger.warning(str(e))
            ret = await question_dialog(
                parent=self,
                title=_('Destination already exists'),
                message=_('Do you want to replace the existing repository ?'),
                detail=_(
                    "The selected destination already exists at this "
                    "location. If you continue with this repository, "
                    "you will replace it's content using this computer. "
                ),
            )
            if ret:
                await self._create_local(location, repositoryname, force=True)
        except ConfigureBackupError as e:
            logger.warning(str(e))
            self.error_message = e.message
            self.error_detail = e.detail
        except Exception as e:
            logger.warning(str(e))
            self.error_message = _("Unknown problem happen when trying to configure the destination.")
            self.error_detail = str(e)
        else:
            self.error_message = ""
            self.error_detail = ""
            # On success, go to next step
            if self.create:
                App.get_running_app().set_active_view('BackupPatterns', instance=self.instance, create=self.create)
            else:
                App.get_running_app().set_active_view('DashboardView')
        finally:
            self.working = ''

    @alias_property(bind=['selected_location', 'repositoryname'])
    def valid(self):
        # Valid if a dist is selected AND repository name provided
        return self.selected_location is not None and self.repositoryname

    def reset(self):
        # When user click on Reset server connexion. Let enable editing.
        self.edit = True

    def refresh_locations(self):
        # Do nothing if task is already running
        if self._refresh_locations_task and not self._refresh_locations_task.done():
            return
        self.error_message = ""
        self.error_detail = ""
        self.removable_locations_loading = True
        self.selected_location = None
        self._refresh_locations_task = asyncio.create_task(self._refresh_locations())

    def select_custom_location(self):
        """
        Called when user want to browse a speicifc location.
        """

        async def _select_custom_location():
            folder = await folder_dialog(parent=self, title=_('Select location where to backup your files.'))
            if not folder:
                # Operation cancel by user
                return
            # FIXME
            # Check if it's a network location.
            if IS_WINDOWS and folder.replace('\\', '/').startswith('//'):
                # On windows, it's possible to access mountpoint using \\hostname\share\path\to\file. Before doing so, let confirm if this is whats the user really want.
                pass
            # Get Location Info
            location = get_location_info(folder)
            # If location information could not be retrived, abort the operation.
            if not location:
                await warning_dialog(
                    parent=self,
                    title=_("Unable to retrieve information from selected location"),
                    message=_("Unable to retrieve information from selected location"),
                    detail=_(
                        'Unable to obtain detailed information on the selected location. Please ensure that this location is accessible and valid. If the problem persists, consult the application log with your administrator.'
                    ),
                )
                return
            # Add selected location to the list.
            self.selected_location = location

        self._select_custom_location_task = asyncio.create_task(_select_custom_location())

    def cancel(self):
        # When operation is cancel by user, redirect it.

        if self.create:
            App.get_running_app().set_active_view('BackupCreate')
        else:
            App.get_running_app().set_active_view('DashboardView')

    def save(self, event=None):
        if not self.repositoryname or not self.selected_location or self.working:
            # Operation should not be accessible if not valid.
            return
        # Start creation task.
        self.working = _('Please wait. Initializing backup...')
        self._create_local_task = asyncio.create_task(
            self._create_local(location=self.selected_location, repositoryname=self.repositoryname)
        )

    def forget_instance(self):
        assert not self.create

        async def _forget_instance():
            # In edit mode, confirm operation, destroy the configuration and go to dashboard.
            ret = await question_dialog(
                parent=self,
                title=_('Are you sure ?'),
                message=_('Are you sure you want to delete this backup configuration ?'),
                detail=_(
                    'If you delete this backup configuration, this Minarca agent will erase its identity and will no longer run backup on schedule.'
                ),
            )
            if not ret:
                # Operation cancel by user.
                return
            self.instance.forget()
            App.get_running_app().set_active_view('DashboardView')

        self._forget_task = asyncio.create_task(_forget_instance())
