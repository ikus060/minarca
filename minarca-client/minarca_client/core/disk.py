# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Nov. 9, 2023

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import os
import re
import subprocess
from collections import namedtuple

import psutil

from .compat import IS_LINUX, IS_MAC, IS_WINDOWS

if IS_WINDOWS:
    import win32api
    import win32file

if IS_LINUX:

    def _read(fn, encoding=None, default=None):
        try:
            with open(fn, 'r', encoding=encoding) as f:
                return f.read().strip()
        except OSError:
            # Silently ignore any os error
            return default


if IS_MAC:

    def _diskutil_parse(output):
        """
        Parse MacOS diskutil output
        """
        return {
            line.split(':')[0].strip(): line.split(':')[1].strip()
            for line in output.split('\n')
            if line.strip()  # Ignore empty line.
            if ':' in line
        }


DeviceInfo = namedtuple('DeviceInfo', ['caption', 'removable'])


class DiskInfo(
    namedtuple(
        'DiskInfo', ['device', 'mountpoint', 'relpath', 'caption', 'free', 'used', 'size', 'fstype', 'removable']
    )
):
    def __eq__(self, other):
        if other is None:
            return False
        elif self is other:
            return True
        return self.device == other.device and self.mountpoint == other.mountpoint and self.relpath == other.relpath


def _get_device_info(device):
    if IS_WINDOWS:
        # On Windows will gather detailed information using win32api.
        drive_type = win32file.GetDriveType(device)
        removable = drive_type == win32file.DRIVE_REMOVABLE
        volume_name, _, _, _, _ = win32api.GetVolumeInformation(device + '\\')
        return DeviceInfo(volume_name, removable)
    elif IS_MAC:
        # On MacOS, will get information from diskutil commandline
        # Lookup device instead of partition.
        data = _diskutil_parse(
            subprocess.check_output(
                ["diskutil", "info", device], env={'LANG': 'en_US', 'PATH': os.environ.get('PATH')}, text=True
            )
        )
        removable = data.get('Removable Media', '') == 'Removable'
        caption = data.get('Volume Name', '')
        disk_device = re.sub('s1$', '', device)
        if disk_device != device:
            data = _diskutil_parse(
                subprocess.check_output(
                    ["diskutil", "info", disk_device], env={'LANG': 'en_US', 'PATH': os.environ.get('PATH')}, text=True
                )
            )
            disk_name = data.get('Device / Media Name', '')
            caption += " "
            caption += disk_name
        return DeviceInfo(caption, removable)
    elif IS_LINUX:
        # On Linux will get information from sysfs
        part_device_name = os.path.basename(device)
        try:
            # Find parent block device `/sys/class/block/<device>/..`
            device_name = os.path.basename(
                os.path.abspath(
                    os.path.join(
                        '/sys/class/block', os.readlink(os.path.join('/sys/class/block', part_device_name)), '..'
                    )
                )
            )
        except FileNotFoundError:
            return None
        # Check if removable /sys/class/block/*/removable
        removable_fn = os.path.join('/sys/class/block/', device_name, 'removable')
        removable = _read(removable_fn) == '1'
        # Get Vendor and model for display name
        vendor_fn = os.path.join('/sys/class/block/', device_name, 'device/vendor')
        vendor = _read(vendor_fn) or ''
        model_fn = os.path.join('/sys/class/block/', device_name, 'device/model')
        model = _read(model_fn)
        caption = ' '.join([t for t in [vendor, model] if t])
        return DeviceInfo(caption, removable)
    return None


def _get_device_name(filename):
    """
    Determine the device name where the given filename reside on.
    """
    if IS_WINDOWS:
        # On Windows, the device name if the Drive Letter.
        device_name = os.path.splitdrive(filename)[0]
        return device_name + '\\'
    elif IS_MAC or IS_LINUX:
        # On MacOS and Linux, will use the "df" command line to get the device name.
        data = subprocess.check_output(["df", filename], env={'LANG': 'en_US'}, text=True)
        lines = data.splitlines()
        if len(lines) >= 2:
            device_name = lines[1].split()[0]
            return device_name


def list_disks(removable=False):
    """
    Try to list external disk drive.
    """
    disks = []
    parts = psutil.disk_partitions()
    for part in parts:
        if removable and IS_LINUX and part.mountpoint == '/':
            # Ignore Root Device on Linux
            continue
        if 'ro' in part.opts.split(','):
            # Ignore readonly partition
            continue
        # Get detail information about the device.
        info = _get_device_info(part.device)
        if not info:
            continue
        if removable and not info.removable:
            # Keep only removable devices
            continue
        usage = psutil.disk_usage(part.mountpoint)
        disks.append(
            DiskInfo(
                part.device,
                part.mountpoint,
                '.',
                info.caption,
                usage.free,
                usage.used,
                usage.total,
                part.fstype,
                removable,
            )
        )
    return disks


def get_disk_info(filename):
    """
    For a given filename, return a Disk Info
    """
    # Get the device name where the given filename exists.
    device = _get_device_name(filename)
    if not device:
        return None
    # Get caption and removable info of device.
    info = _get_device_info(device)
    if not info:
        return None
    # Lookup mountpoint
    part = next((p for p in psutil.disk_partitions() if p.device == device), None)
    if not part:
        return None
    # Get Disk usage information
    usage = psutil.disk_usage(filename)
    # Calculate the relative path between the filename and mount point.
    relpath = os.path.relpath(filename, part.mountpoint)
    return DiskInfo(
        device, part.mountpoint, relpath, info.caption, usage.free, usage.used, usage.total, part.fstype, info.removable
    )
