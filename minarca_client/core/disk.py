# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Nov. 9, 2023

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import logging
import os
import re
import subprocess
from collections import namedtuple
from pathlib import Path

import psutil

from .compat import IS_LINUX, IS_MAC, IS_WINDOWS

logger = logging.getLogger(__name__)

DeviceInfo = namedtuple('DeviceInfo', ['caption', 'device_type', 'fstype'])


class LocationInfo(
    namedtuple('LocationInfo', ['mountpoint', 'relpath', 'caption', 'free', 'used', 'size', 'fstype', 'device_type'])
):
    REMOVABLE = 'removable'
    REMOTE = 'remote'
    FIXED = 'fixed'

    def __eq__(self, other):
        if other is None:
            return False
        elif self is other:
            return True
        return self.mountpoint == other.mountpoint and self.relpath == other.relpath

    @property
    def removable(self):
        return self.device_type == self.REMOVABLE

    @property
    def remote(self):
        return self.device_type == self.REMOTE

    @property
    def fixed(self):
        return self.device_type == self.FIXED

    @property
    def is_mountpoint(self):
        """Return True if the given location is the root of the mount point."""
        return self.relpath == Path('.')


def _get_mountpoint_posix(filename):
    node = Path(filename)
    # Handle MacOS firmlink differently.
    if IS_MAC and node == Path('/System/Volumes/Data'):
        return node
    file_dev = node.stat().st_dev
    while node.name != '':
        parent_node = node.parent
        if parent_node.stat().st_dev != file_dev:
            return node
        node = parent_node
    return node


def _get_device_posix(filename):
    """Return the corresponding device name hosting a file."""
    assert isinstance(filename, Path)
    # On MacOS and Linux, will use the "df" command line to get the device name.
    data = subprocess.check_output(["df", filename], env={'LANG': 'en_US'}, text=True)
    lines = data.splitlines()
    if len(lines) < 2:
        return None
    return Path(lines[1].split()[0])


if IS_WINDOWS:
    import win32api
    import win32file

    def _get_mountpoint_win(filename):
        """Return the mount point"""
        # On Windows we can use the splitdrive to support Drive letter (C:\) and network share (\\server\path).
        mountpoint = Path(os.path.splitdrive(filename)[0])
        if not str(mountpoint).endswith('/'):
            mountpoint = mountpoint / '/'
        return mountpoint

    def _get_device_win(filename):
        """Return the corresponding device name hosting a file."""
        assert isinstance(filename, Path)
        return filename.parts[0]

    def _get_device_info_win(device):
        """Return detail information about the device hosting this file. .e.g.: fstype, caption and removable."""

        # On Windows will gather detailed information using win32api.
        drive_type = win32file.GetDriveType(device)
        # Convert window drive_type to our device_type
        device_type = {
            win32file.DRIVE_REMOVABLE: LocationInfo.REMOVABLE,
            win32file.DRIVE_REMOTE: LocationInfo.REMOTE,
            win32file.DRIVE_FIXED: LocationInfo.FIXED,
        }.get(drive_type, None)
        # Get volume name and file system
        volume_name, _, _, _, fstype = win32api.GetVolumeInformation(device + '\\')
        if drive_type == win32file.DRIVE_REMOTE or not volume_name:
            # For remove simply return the device name (e.g.: \\server-name\path)
            volume_name = device
        return DeviceInfo(volume_name, device_type, fstype)

    _get_mountpoint = _get_mountpoint_win
    _get_device = _get_device_win
    _get_device_info = _get_device_info_win

elif IS_LINUX:

    def _get_device_fstype_linux(device):
        """Return the file system type."""
        # On Linux the most reliable source for fstype is findmntcommand line.
        data = subprocess.check_output(["findmnt", "-no", "FSTYPE", str(device)], env={'LANG': 'en_US'}, text=True)
        return data.strip()

    def _get_device_info_linux(device):
        """Return detail information about the device hosting this file. .e.g.: fstype, caption and removable."""

        # On MacOS and Linux, psutil is working well to get fstype
        fstype = _get_device_fstype_linux(device)

        # On Linux will get block device information from /sys
        try:
            # The given device is a partition, so get the parent block device from /sys
            device_name = (Path('/sys/class/block') / Path(device).name).readlink().parent.resolve().name
            device_path = Path('/sys/class/block/') / device_name
        except FileNotFoundError:
            # This happen for non-block device like remote share.
            return DeviceInfo(device, LocationInfo.REMOTE, 'unknown')

        # Determine the device_type using /sys/class/block/*/removable
        try:
            removable = (device_path / 'removable').read_text().strip() == '1'
            device_type = LocationInfo.REMOVABLE if removable else LocationInfo.FIXED
        except FileNotFoundError:
            device_type = None

        # Get Vendor and model for display name
        try:
            vendor = (device_path / 'device/vendor').read_text().strip()
            model = (device_path / 'device/model').read_text().strip()
            caption = ' '.join([t for t in [vendor, model] if t])
        except FileNotFoundError:
            caption = None
        return DeviceInfo(caption, device_type, fstype)

    _get_mountpoint = _get_mountpoint_posix
    _get_device = _get_device_posix
    _get_device_info = _get_device_info_linux

if IS_MAC:

    def _diskutil_info(device):
        """
        Parse MacOS diskutil output
        """
        proc = subprocess.run(
            ["diskutil", "info", str(device)],
            env={'LANG': 'en_US', 'PATH': os.environ.get('PATH')},
            text=True,
            check=True,
            capture_output=True,
        )
        return {
            line.split(':')[0].strip(): line.split(':')[1].strip()
            for line in proc.stdout.split('\n')
            if line.strip()  # Ignore empty line.
            if ':' in line
        }

    def _get_device_info_macos(device):
        """Return detail information about the device hosting this file. .e.g.: fstype, caption and removable."""

        # On MacOS, will get information from diskutil commandline
        # Lookup device instead of partition.
        try:
            data = _diskutil_info(device)
        except subprocess.CalledProcessError as e:
            if 'Could not find disk' in e.stderr:
                # We could assume it's a remote device.
                return DeviceInfo(device, LocationInfo.REMOTE, 'unknown')
            raise
        # Convert MacOS device type to our device type.
        media_type = data.get('Removable Media', '')
        device_type = {'Removable': LocationInfo.REMOVABLE, 'Fixed': LocationInfo.FIXED}.get(media_type, None)
        # GET Filesystem information
        fstype = data.get('File System Personality', data.get('File System', None))
        # Get Device Caption
        caption = data.get('Volume Name', '')
        # Here we take a shortcut assuming the selected device is on partition #1 to get the parent device.
        disk_device = re.sub('s1$', '', str(device))
        if disk_device != device:
            data = _diskutil_info(disk_device)
            disk_name = data.get('Device / Media Name', '')
            caption += " "
            caption += disk_name
        return DeviceInfo(caption, device_type, fstype)

    _get_mountpoint = _get_mountpoint_posix
    _get_device = _get_device_posix
    _get_device_info = _get_device_info_macos


def list_disks():
    """
    Try to list external disk drive.
    """
    disks = []
    parts = psutil.disk_partitions()
    for part in parts:
        if 'ro' in part.opts.split(','):
            # Ignore readonly partition
            continue
        disks.append(Path(part.mountpoint))
    return disks


def list_disk_with_location_info(removable=False):
    """
    Return list of external disk with location info.
    """
    disk_infos = []
    for disk in list_disks():
        # Get detail information about the disk
        info = get_location_info(disk)
        if removable and (
            (info.device_type != LocationInfo.REMOVABLE) or ((IS_LINUX or IS_MAC) and info.mountpoint == '/')
        ):
            # Keep only removable devices
            continue
        disk_infos.append(info)
    return disk_infos


def splitmountpoint(filename):
    """Split the filename into mountpoint and relpath"""
    assert isinstance(filename, (Path, str))
    if isinstance(filename, str):
        filename = Path(filename)
    mountpoint = _get_mountpoint(filename)
    relpath = filename.relative_to(mountpoint)
    return (mountpoint, relpath)


def get_location_info(filename):
    assert isinstance(filename, Path)
    """Return detailed information about the device hosting the given filename. e.g.: disk usage, caption, fstype, removable"""
    # Start by splitting the filename
    mountpoint, relpath = splitmountpoint(filename)

    # Get disk usage information
    try:
        disk_usage = psutil.disk_usage(str(filename))
    except Exception:
        logger.warning(f'fail to get disk usage {filename}', exc_info=1)
        disk_usage = None

    # Also get device information like caption and removable.
    try:
        device = _get_device(filename)
        device_info = _get_device_info(device)
    except Exception:
        logger.warning(f'fail to get device info from {filename}', exc_info=1)
        device_info = None

    return LocationInfo(
        Path(mountpoint),
        Path(relpath),
        device_info.caption if device_info else Path(filename).name,
        disk_usage.free if disk_usage else None,
        disk_usage.used if disk_usage else None,
        disk_usage.total if disk_usage else None,
        device_info.fstype if device_info else None,
        device_info.device_type if device_info else None,
    )
