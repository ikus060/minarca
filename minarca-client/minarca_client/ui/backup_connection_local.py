# Copyleft (C) 2023 IKUS Software. All lefts reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import functools
import logging
import os
import tkinter.messagebox

import humanfriendly

from minarca_client.core.compat import get_default_repositoryname
from minarca_client.core.disk import DiskInfo, get_disk_info, list_disks
from minarca_client.core.exceptions import LocalDiskNotFound, RepositoryNameExistsError, ConfigureBackupError
from minarca_client.locale import _
from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class BackupConnectionLocal(tkvue.Component):
    template = """
<Frame pack="expand:1; fill:both">
    <SidePanel create="{{create}}" is-remote="False" text="Select an external hard disk to be used for backing up your data." step="0" maximum="3" pack="side:left; fill:y" />
    <Separator orient="vertical" pack="side:left; fill:y" />

    <!-- Form -->
    <Frame style="white.TFrame" padding="50" pack="expand:1; fill:both" visible="{{ not working }}">
        <Label text="Local device" style="h3.info.white.TLabel" pack="fill:x; pady:0 20" />

        <Button text="Reset local device connexion" command="{{reset}}" style="sm.secondary.TButton" pack="anchor:w; pady:0 20" visible="{{ not edit }}"/>

        <!-- Error message -->
        <Label text="{{ error_message }}" style="white.danger.TLabel" wrap="1" pack="fill:x; pady:0 15" padding="12" visible="{{ error_message }}" />
        <Label text="{{ error_detail }}" style="danger.white.TLabel" wrap="1" pack="fill:x; pady:0 20" visible="{{ error_detail }}" />

        <Label text="Backup name" style="white.TLabel" pack="fill:x; pady:0 10" disabled="{{ not edit }}"/>
        <Entry textvariable="{{ repositoryname }}" pack="fill:x; pady:0 30" disabled="{{ not edit }}"/>

        <Frame style="white.TFrame" pack="fill:x; pady:0 20" visible="{{ edit or selected_disk is None}}">
            <Button text="Refresh" command="{{refresh_removable_disks}}" style="sm.secondary.TButton" pack="side:left; padx: 0 10;"/>
            <Button text="Browse" command="{{select_custom_disk}}" style="sm.secondary.TButton" pack="side:left" visible="{{ edit }}"/>
        </Frame>

        <!-- Disk -->
        <ScrolledFrame style="white.TFrame" pack="expand:1; fill:both;" visible="{{removable_disks or selected_disk}}" >
            <!-- Display a "fake" disk entry if selected disk is not in the detected list. -->
            <Button
                style="light-info.TOutlineButton"
                image="{{ 'check-circle-fill-success' if selected_disk is None or check_disk_criteria(selected_disk) is None else 'exclamation-triangle-fill-warning' }}"
                text="{{ selected_disk and selected_disk.caption }}"
                compound="left"
                pack="fill:x; pady:0 10"
                padding="20"
                visible="{{selected_disk is not None and selected_disk not in removable_disks and not removable_disks_loading}}"
                >
                    <Tooltip text="{{ selected_disk and check_disk_criteria(selected_disk) }}" width="55"/>
                    <Label text="{{ selected_disk and format_disk_size(selected_disk)}}" style="light-info.TLabel" place="relx:1; rely:0.5; x:-20; anchor:e"/>
            </Button>
            <Button for="{{disk in removable_disks}}"
                command="{{ set_disk(disk) }}"
                style="{{ 'light-info.TOutlineButton' if selected_disk==disk else 'white.TOutlineButton' }}"
                image="{{ 'check-circle-fill-success' if check_disk_criteria(disk) is None else 'exclamation-triangle-fill-warning' }}"
                text="{{ disk.caption }}"
                compound="left"
                pack="fill:x; pady:0 10"
                padding="20"
                cursor="hand2">
                    <Tooltip text="{{ check_disk_criteria(disk) }}" width="55"/>
                    <Label text="{{format_disk_size(disk)}}" style="{{ 'light-info.TLabel' if selected_disk==disk else 'white.TLabel' }}" place="relx:1; rely:0.5; x:-20; anchor:e"/>
            </Button>
        </ScrolledFrame>

        <!-- Display a notice when no removable disk are available -->
        <Label text="No external disk detected is suitable for data backup."
            style="white.TLabel"
            visible="{{ edit and not removable_disks and not removable_disks_loading and selected_disk is None }}"
            pack="expand:1; fill:both; pady: 30"
            anchor="center"/>

        <!-- Display a looding label when getting list of disk -->
        <Label text="Loading..."
            image="spinner-16"
            compound="left"
            style="white.TLabel"
            visible="{{ removable_disks_loading }}"
            pack="expand:1; fill:both; pady: 30"
            anchor="center"/>

        <Frame style="white.TFrame" pack="fill:x; pady:20 0;">
            <Button text="{{ _('Back') if create else _('Cancel') }}" command="{{cancel}}" style="default.TButton" pack="side:left; padx:0 10;" cursor="hand2" />
            <Button text="{{ _('Next') if create else _('Save') }}" command="{{save}}" style="info.TButton" pack="side:left" state="{{'!disabled' if valid else 'disabled'}}" cursor="{{'hand2' if valid else 'arrow'}}" visible="{{ edit }}"/>
        </Frame>
        <Button text="Delete backup settings" image="trash-danger" compound="left" command="{{forget_instance}}" style="danger.white.TLink" pack="fill:x; pady:30 0;" cursor="hand2" visible="{{ not create }}"/>
    </Frame>

    <Frame style="white.TFrame" padding="50" pack="expand:1; fill:both;" visible="{{ working }}">
        <Label image="spinner-64" style="white.TLabel" pack="expand:1; fill:both; pady:0 10" anchor="s"/>
        <Label text="Verifying local device." style="light.white.TLabel" pack="fill:x;" anchor="n" />
        <Label text="Please Wait" style="light.white.TLabel" pack="expand:1; fill:both;" anchor="n" />
    </Frame>

</Frame>
"""
    working = tkvue.state(False)
    edit = tkvue.state(True)
    create = tkvue.state(False)
    repositoryname = tkvue.state("")
    removable_disks_loading = tkvue.state(False)
    removable_disks = tkvue.state([])
    selected_disk = tkvue.state(None)
    error_message = tkvue.state(None)
    error_detail = tkvue.state(None)

    _refresh_removable_disks_task = None

    def __init__(self, master=None, backup=None, create=False, instance=None):
        self.backup = backup
        self.instance = instance
        self.create.value = create
        # Allow editing when creating new repo.
        self.edit.value = self.instance is None
        super().__init__(master)
        # Refresh disk on creation
        self.refresh_removable_disks()
        if self.instance is None:
            # Define default repo name on creation
            self.repositoryname.value = get_default_repositoryname()
        else:
            self.repositoryname.value = instance.settings.repositoryname
        # Register call back to stop running task.
        self.root.bind('<Destroy>', self._cancel_tasks, add="+")

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._refresh_removable_disks_task:
            self._refresh_removable_disks_task.cancel()

    async def _refresh_removable_disks(self):
        """
        Every couple of seconds, check if the list of local disks get updated.
        """
        if self.instance is not None:
            # If instance is configure, load current disk
            try:
                local_disk = await self.get_event_loop().run_in_executor(None, self.instance.find_local_disk)
                self.selected_disk.value = local_disk
            except LocalDiskNotFound as e:
                self.selected_disk.value = DiskInfo(
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
                self.error_detail.value = str(e)
            finally:
                self.removable_disks_loading.value = False
        else:
            try:
                disks = await self.get_event_loop().run_in_executor(None, list_disks, True)
                self.removable_disks.value = disks
            except Exception:
                logger.warn('fail to list removable disks', exc_info=1)
            finally:
                self.removable_disks_loading.value = False

    async def _create_local(self, disk, repositoryname, force=False):
        assert disk
        assert repositoryname

        # Get path of selected disk
        path = os.path.join(disk.mountpoint, disk.relpath)

        # If the relpath is the root of the external drive,
        # will create additonal directory structure using the reponame.
        if disk.relpath == '.':
            path = os.path.join(path, "minarca", repositoryname)
            os.makedirs(path, exist_ok=True)

        # Create a new backup instance configuration.
        try:
            call = functools.partial(
                self.backup.configure_local,
                path=path,
                repositoryname=repositoryname,
                force=force,
                instance=self.instance,
            )
            self.instance = await self.get_event_loop().run_in_executor(None, call)
        except RepositoryNameExistsError as e:
            logger.warning(str(e))
            ret = tkinter.messagebox.askyesno(
                parent=self.root,
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
            self.error_message.value = e.message
            self.error_detail.value = e.detail
        else:
            self.error_message.value = None
            self.error_detail.value = None
            # On success, go to next step
            if self.create.value:
                toplevel = self.root.winfo_toplevel()
                toplevel.set_active_view('BackupPatterns', instance=self.instance, create=self.create.value)
            else:
                toplevel = self.root.winfo_toplevel()
                toplevel.set_active_view('DashboardView')
        finally:
            self.working.value = False

    @tkvue.computed_property
    def valid(self):
        # Valid if a dist is selected AND repository name provided
        return self.selected_disk.value is not None and self.repositoryname.value

    @tkvue.command
    def reset(self):
        # When user click on Reset server connexion. Let enable editing.
        self.edit.value = True

    @tkvue.command
    def refresh_removable_disks(self):
        # Do nothing if task is already running
        if self._refresh_removable_disks_task and not self._refresh_removable_disks_task.done():
            return
        self.error_message.value = None
        self.error_detail.value = None
        self.removable_disks.value = []
        self.removable_disks_loading.value = True
        self._refresh_removable_disks_task = self.get_event_loop().create_task(self._refresh_removable_disks())

    @tkvue.command
    def select_custom_disk(self):
        """
        Called when user want to browse a speicifc location.
        """
        folder = tkinter.filedialog.askdirectory(
            title=_('Select local device where to backup your files.'),
            parent=self.root,
            mustexist=True,
        )
        if not folder:
            # Operation cancel by user
            self.selected_disk.value = None
            return
        # Get Device UUID
        disk = get_disk_info(folder)
        # If disk information could not be retrived, abort the operation.
        if not disk:
            tkinter.messagebox.showwarning(
                parent=self.root,
                icon='warning',
                title=_("Unable to retrieve information from local device"),
                message=_('Unable to retrieve information from local device'),
                detail=_(
                    'Unable to obtain detailed information on the selected location. Please ensure that this location is a local device. If the problem persists, consult the application log with your administrator.'
                ),
            )
            self.selected_disk.value = None
            return
        # Add selected location to the list.
        self.selected_disk.value = disk

    @tkvue.command
    def format_disk_size(self, disk):
        """
        Return a rounded human readable disk size.
        """
        if not getattr(disk, 'size', False):
            return None
        return humanfriendly.format_size(disk.size)

    @tkvue.command
    def check_disk_criteria(self, disk):
        """
        Check disk criteria.
        """
        if disk.fstype in ['vfat', 'FAT32', 'msdos']:
            return _(
                "This locale device is formatted with an outdated FAT32 file system, which is not recommended. If you intend to use this disk, it is advisable to reformat the device using NTFS."
            )
        elif disk.free and disk.free <= 250 * 1000 * 1000 * 1000:
            # Warn if the disk space available is less then 250 GiB.
            return _(
                "This local device offers a mere %s of available free space, which may prove inadequate for your long-term backup needs. It is advisable to opt for a disk with a capacity exceeding 250 GiB of free space."
            ) % humanfriendly.format_size(disk.size)
        elif disk.removable is False:
            return _(
                "This locale device was not identified as removable. Utilizing an internal disk drive for backups is not recommended, as it provides less protection."
            )
        return None

    @tkvue.command
    def set_disk(self, disk):
        self.selected_disk.value = disk

    @tkvue.command
    def cancel(self):
        # When operation is cancel by user, redirect it.
        toplevel = self.root.winfo_toplevel()
        if self.create.value:
            toplevel.set_active_view('BackupCreate')
        else:
            toplevel.set_active_view('DashboardView')

    @tkvue.command
    def save(self, event=None):
        if not self.repositoryname.value or not self.selected_disk.value or self.working.value:
            # Operation should not be accessible if not valid.
            return
        # Start creation task.
        coro = self._create_local(disk=self.selected_disk.value, repositoryname=self.repositoryname.value)
        self.working.value = True
        handle = self.get_event_loop().create_task(coro)
        self.root.bind('<Destroy>', lambda unused: handle.cancel(), add="+")

    @tkvue.command
    def forget_instance(self):
        assert not self.create.value
        # In edit mode, confirm operation, destroy the configuration and go to dashboard.
        return_code = tkinter.messagebox.askyesno(
            parent=self.root,
            title=_('Are you sure ?'),
            message=_('Are you sure you want to delete this backup configuration ?'),
            detail=_(
                'If you delete this backup configuration, this Minarca agent will erase its identity and will no longer run backup on schedule.'
            ),
        )
        if not return_code:
            # Operation cancel by user.
            return
        self.instance.forget()
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('DashboardView')
