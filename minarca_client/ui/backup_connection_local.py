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

from minarca_client.core.compat import IS_LINUX, get_default_repositoryname
from minarca_client.core.disk import DiskInfo, get_disk_info, list_disks
from minarca_client.core.exceptions import ConfigureBackupError, LocalDiskNotFound, RepositoryNameExistsError
from minarca_client.dialogs import folder_dialog, question_dialog, warning_dialog
from minarca_client.locale import _
from minarca_client.ui.spinner_overlay import SpinnerOverlay  # noqa
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)


Builder.load_string(
    '''
<DiskItem>:
    divider:
    adaptive_height: True
    theme_bg_color: "Custom"
    md_bg_color: self.theme_cls.secondaryContainerColor if root.selected else self.theme_cls.surfaceColor

    MDListItemLeadingIcon:
        icon_color: self.theme_cls.primaryColor if root.check_disk_criteria else self.theme_cls.onSurfaceColor
        icon: "alert-circle-outline" if root.check_disk_criteria else "harddisk"

    MDListItemHeadlineText:
        text: root.title

    MDListItemSupportingText:
        text: root.details

    MDListItemTertiaryText:
        theme_text_color: "Custom"
        text_color: self.theme_cls.primaryColor
        text: root.check_disk_criteria or " "


<BackupConnectionLocal>:
    id: backup_connection_local
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    SidePanel:
        is_remote: False
        create: root.create
        text: _("Select an external hard disk to be used for backing up your data.")
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
                    text: _("External device")
                    font_style: "Title"
                    role: "small"
                    text_color: self.theme_cls.primaryColor

                CButton:
                    text: _('Reset local device connexion')
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
                    on_release: root.refresh_removable_disks()
                    role: "small"
                    theme_bg_color: "Custom"
                    md_bg_color: self.theme_cls.secondaryColor
                    theme_text_color: "Custom"
                    text_color: self.theme_cls.onSecondaryColor

                CButton:
                    id: btn_browse
                    text: _('Browse')
                    on_release: root.select_custom_disk()
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
                    display: not root.sorted_removable_disks

                RecycleView:
                    viewclass: "DiskItem"
                    data: root.sorted_removable_disks

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


class DiskItem(MDListItem):
    disk_info = ObjectProperty()
    selected = BooleanProperty()
    on_disk_item_release = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def remove_widget(self, widget, *args, **kwargs):
        super().remove_widget(widget, *args, **kwargs)

    def on_release(self):
        if callable(self.on_disk_item_release):
            self.on_disk_item_release(self)
        return super().on_release()

    @alias_property(bind=['disk_info'])
    def title(self):
        return self.disk_info.caption if self.disk_info else ""

    @alias_property(bind=['disk_info'])
    def details(self):
        if not self.disk_info:
            return ""
        # When size cannot be detected, it's because the disk is not connected.
        if self.disk_info.size is None and self.disk_info.free is None:
            return str(LocalDiskNotFound())
        size = humanfriendly.format_size(self.disk_info.size)
        free = humanfriendly.format_size(self.disk_info.free)
        fstype = self.disk_info.fstype or ""
        return _("%s Drive with %s available space \u2022 Format %s") % (size, free, fstype)

    @alias_property(bind=['disk_info'])
    def check_disk_criteria(self):
        if not self.disk_info:
            return ""
        # Check disk criteria.
        if self.disk_info.fstype in ['vfat', 'FAT32', 'msdos']:
            return _("FAT32 file system is not recommended for backup.")
        if IS_LINUX and self.disk_info.fstype in ['ntfs']:
            return _("NTFS is not recommended for backup on Linux.")
        elif self.disk_info.free and self.disk_info.free <= 250 * 1000 * 1000 * 1000:
            # Warn if the disk space available is less then 250 GiB.
            return _("Available disk space on this device is limited.")
        elif self.disk_info.removable is False:
            return _("This device was not identified as removable.")
        return ""


class BackupConnectionLocal(MDBoxLayout):
    working = StringProperty()
    edit = BooleanProperty(True)
    create = BooleanProperty(False)
    repositoryname = StringProperty("")
    removable_disks_loading = BooleanProperty(False)
    removable_disks = ListProperty([])
    selected_disk = ObjectProperty(None, allownone=True)
    error_message = StringProperty("")
    error_detail = StringProperty("")

    _create_local_task = None
    _refresh_removable_disks_task = None
    _select_custom_disk_task = None
    _forget_task = None

    def __init__(self, backup=None, create=False, instance=None):
        self.backup = backup
        self.instance = instance
        self.create = create
        # Allow editing when creating new repo.
        self.edit = self.instance is None
        super().__init__()
        # Refresh disk on creation
        self.refresh_removable_disks()
        if self.instance is None:
            # Define default repo name on creation
            self.repositoryname = get_default_repositoryname()
        else:
            self.repositoryname = instance.settings.repositoryname

    @alias_property(bind=['removable_disks', 'selected_disk'])
    def sorted_removable_disks(self):
        all_disk = self.removable_disks
        # Add custom disk to the list.
        if self.selected_disk and self.selected_disk not in all_disk:
            all_disk.insert(0, self.selected_disk)
        return [
            {'disk_info': i, 'selected': i == self.selected_disk, 'on_disk_item_release': self.on_disk_item_release}
            for i in self.removable_disks
        ]

    def on_disk_item_release(self, disk_item):
        # Change selected disk when user click on it.
        self.selected_disk = disk_item.disk_info

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._refresh_removable_disks_task:
            self._refresh_removable_disks_task.cancel()
        if self._select_custom_disk_task:
            self._select_custom_disk_task.cancel()
        if self._create_local_task:
            self._create_local_task.cancel()
        if self._forget_task:
            self._forget_task.cancel()

    async def _refresh_removable_disks(self):
        """
        Every couple of seconds, check if the list of local disks get updated.
        """
        if self.instance is not None:
            # If instance is configure, load current disk
            try:
                local_disk = await asyncio.get_event_loop().run_in_executor(None, self.instance.find_local_disk)
                self.selected_disk = local_disk
            except LocalDiskNotFound:
                self.selected_disk = DiskInfo(
                    device=None,
                    mountpoint=None,
                    relpath=self.instance.settings.localrelpath,
                    caption=self.instance.settings.localcaption,
                    free=None,
                    used=None,
                    size=None,
                    fstype=None,
                    removable=None,
                )
            finally:
                self.removable_disks_loading = False
        else:
            try:
                disks = await asyncio.get_event_loop().run_in_executor(None, list_disks, True)
                self.removable_disks = disks
            except Exception:
                logger.warning('fail to list removable disks', exc_info=1)
            finally:
                self.removable_disks_loading = False

    async def _create_local(self, disk, repositoryname, force=False):
        assert disk
        assert repositoryname

        # Get path of selected disk
        path = os.path.join(disk.mountpoint, disk.relpath)

        # Create a new backup instance configuration.
        try:
            # If the relpath is the root of the external drive,
            # will create additonal directory structure using the reponame.
            # TODO Consider moving this part into configure_local
            if disk.relpath == '.':
                path = os.path.join(path, "minarca", repositoryname)
                os.makedirs(path, exist_ok=True)
            self.instance = await self.backup.configure_local(
                path=path,
                repositoryname=repositoryname,
                force=force,
                instance=self.instance,
            )
        except PermissionError as e:
            logger.warning(str(e))
            self.error_message = _("You don't have permissions to write on this disk.")
            self.error_detail = str(e)
        except RepositoryNameExistsError as e:
            logger.warning(str(e))
            ret = await question_dialog(
                parent=self,
                title=_('Destination already exists'),
                message=_('Do you want to replace the existing repository ?'),
                detail=_(
                    "The selected destination already exists on "
                    "the device. If you continue with this repository, "
                    "you will replace it's content using this computer. "
                ),
            )
            if ret:
                await self._create_local(disk, repositoryname, force=True)
        except ConfigureBackupError as e:
            logger.warning(str(e))
            self.error_message = e.message
            self.error_detail = e.detail
        except Exception as e:
            logger.warning(str(e))
            self.error_message = _("Unknown problem happen when trying to configure the disk.")
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

    @alias_property(bind=['selected_disk', 'repositoryname'])
    def valid(self):
        # Valid if a dist is selected AND repository name provided
        return self.selected_disk is not None and self.repositoryname

    def reset(self):
        # When user click on Reset server connexion. Let enable editing.
        self.edit = True

    def refresh_removable_disks(self):
        # Do nothing if task is already running
        if self._refresh_removable_disks_task and not self._refresh_removable_disks_task.done():
            return
        self.error_message = ""
        self.error_detail = ""
        self.removable_disks_loading = True
        self.selected_disk = None
        self._refresh_removable_disks_task = asyncio.create_task(self._refresh_removable_disks())

    def select_custom_disk(self):
        """
        Called when user want to browse a speicifc location.
        """

        async def _select_custom_disk():
            folder = await folder_dialog(parent=self, title=_('Select local device where to backup your files.'))
            if not folder:
                # Operation cancel by user
                return
            # Get Device UUID
            disk = get_disk_info(folder)
            # If disk information could not be retrived, abort the operation.
            if not disk:
                await warning_dialog(
                    parent=self,
                    title=_("Unable to retrieve information from local device"),
                    message=_('Unable to retrieve information from local device'),
                    detail=_(
                        'Unable to obtain detailed information on the selected location. Please ensure that this location is a local device. If the problem persists, consult the application log with your administrator.'
                    ),
                )
                return
            # Add selected location to the list.
            self.selected_disk = disk

        self._select_custom_disk_task = asyncio.create_task(_select_custom_disk())

    def cancel(self):
        # When operation is cancel by user, redirect it.

        if self.create:
            App.get_running_app().set_active_view('BackupCreate')
        else:
            App.get_running_app().set_active_view('DashboardView')

    def save(self, event=None):
        if not self.repositoryname or not self.selected_disk or self.working:
            # Operation should not be accessible if not valid.
            return
        # Start creation task.
        self.working = _('Please wait. Initializing backup on local device...')
        self._create_local_task = asyncio.create_task(
            self._create_local(disk=self.selected_disk, repositoryname=self.repositoryname)
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
