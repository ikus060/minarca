# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import asyncio
import datetime
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from importlib.metadata import distribution as get_distribution
from importlib.resources import files
from logging import FileHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path

import aiofiles

from minarca_client.locale import _

IS_WINDOWS = sys.platform in ['win32']
IS_LINUX = sys.platform in ['linux', 'linux2']
IS_MAC = sys.platform == 'darwin'
HAS_DISPLAY = os.environ.get('DISPLAY', None) or IS_WINDOWS or IS_MAC


async def tail(filepath, num_lines=1000):
    """
    Tails a file asynchronously and yields the last 1000 lines and subsequent additions.

    Args:
        filepath (str): Path to the text file.
        block_size (int, optional): Block size for reading the file. Defaults to 4096.

    Yields:
        str: Line from the tail of the file.
    """
    async with aiofiles.open(filepath, mode='rb') as f:
        # Read the file as fast as possible
        await f.seek(0, 2)
        init_pos = pos = await f.tell()
        block_size = 4096
        lines_found = 0
        blocks = []
        while lines_found <= num_lines and pos > 0:
            pos -= block_size
            await f.seek(max(0, pos))
            block = await f.read(block_size if pos > 0 else (pos + block_size))
            blocks.append(block)
            lines_found += block.count(b'\n')
        lines = b''.join(reversed(blocks)).splitlines()
        for line in lines:
            yield line

        # Seek to initial end-of-file
        await f.seek(init_pos, 0)
        while True:
            line = await f.readline()
            if not line:
                await asyncio.sleep(0.1)
                continue
            yield line


def makedirs(func, mode=0o750):
    """
    Function decorator to create the directory if missing.
    """

    def _wrap_func(*args, **kwargs):
        name = func(*args, **kwargs)
        try:
            os.makedirs(name, mode=mode, exist_ok=True)
        except PermissionError:
            # Silently ignore permissions error while creating the directory.
            # The process will later fail to read or write file to the folder.
            pass
        return name

    return _wrap_func


def flush(path):
    if IS_WINDOWS:
        # On Windows this required administrator priviledge.
        return
    if hasattr(os, 'O_DIRECTORY'):
        try:
            fd = os.open(path, os.O_DIRECTORY)
            os.fsync(fd)
            os.close(fd)
        except IOError:
            pass


def get_is_admin():
    if IS_WINDOWS:
        return False
    else:
        return os.geteuid() == 0


IS_ADMIN = get_is_admin()


def get_default_repositoryname():
    """
    Return a default value for the repository name.
    """
    try:
        import socket

        hostname = socket.gethostname()
    except Exception:
        import platform

        hostname = platform.node()
    return hostname.split('.')[0]


def get_home(is_admin=IS_ADMIN):
    if is_admin:
        if IS_WINDOWS:
            windir = Path(os.environ.get('WINDIR', 'C:/Windows')).absolute()
            return windir / 'System32/config/systemprofile'
        else:
            return Path("/root")
    return Path.home()


def get_local_appdata(is_admin=IS_ADMIN):
    """
    Return Local App folder.
    """
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        return Path(localappdata).absolute()
    return get_home(is_admin) / "AppData/Local"


@makedirs
def get_log_path(is_admin=IS_ADMIN):
    """
    Return the location of the log file.
    """
    if IS_WINDOWS:
        return get_local_appdata(is_admin) / "minarca"
    elif IS_MAC:
        return get_home() / "Library/Logs/Minarca"
    elif IS_LINUX:
        if is_admin:
            return Path("/var/log")
        return get_data_home(is_admin)
    raise RuntimeError('unsupported platform')


def get_log_file(is_admin=IS_ADMIN):
    return get_log_path(is_admin) / "minarca.log"


@makedirs
def get_config_home(is_admin=IS_ADMIN):
    config_home = os.environ.get('MINARCA_CONFIG_HOME')
    if config_home:
        return Path(config_home).absolute()
    if IS_WINDOWS:
        return get_local_appdata(is_admin) / "minarca"
    elif IS_MAC:
        return get_home(is_admin) / "Library/Preferences/Minarca"
    elif IS_LINUX:
        if is_admin:
            return Path("/etc/minarca")
        return Path(os.environ.get("XDG_CONFIG_HOME", get_home(is_admin) / ".config")) / "minarca"
    raise RuntimeError('unsupported platform')


@makedirs
def get_data_home(is_admin=IS_ADMIN):
    if os.environ.get('MINARCA_DATA_HOME'):
        return Path(os.environ.get('MINARCA_DATA_HOME')).absolute()
    if IS_WINDOWS:
        return get_local_appdata(is_admin) / "minarca"
    elif IS_MAC:
        return get_home(is_admin) / "Library/Minarca"
    elif IS_LINUX:
        if is_admin:
            return Path("/var/lib/minarca")
        else:
            return Path(os.environ.get("XDG_DATA_HOME", get_home(is_admin) / ".local/share")) / "minarca"
    raise RuntimeError('unsupported platform')


def _get_path():
    """
    Return PATH lookup
    """
    path = os.environ.get('PATH', 'C:\\Windows\\system32' if IS_WINDOWS else '/usr/bin')
    path = os.path.dirname(sys.executable) + os.pathsep + path
    if IS_WINDOWS:
        ssh_path = files(__package__) / ('openssh/win_%s' % platform.machine().lower())
        path = str(ssh_path) + os.pathsep + path
    return path


def get_rdiff_backup_version():
    """
    Return the version of rdiff-backup
    """
    try:
        return get_distribution("rdiff-backup").version
    except Exception:
        return 'unknown'


def get_ssh():
    """
    Return the location of SSH executable.
    """
    # TODO Drop support for SSH 32bits.
    if os.environ.get('MINARCA_SSH'):
        return Path(os.environ.get('MINARCA_SSH'))
    name = 'ssh.exe' if IS_WINDOWS else 'ssh'
    path = _get_path()
    ssh = shutil.which(name, path=path)
    if not ssh:
        raise FileNotFoundError(name)
    return Path(ssh)


def get_temp():
    return Path(tempfile.gettempdir())


def get_user_agent():
    from minarca_client import __version__

    return "minarca/{minarca_version} rdiff-backup/{rdiff_backup_version} ({os_name} {os_version} {os_arch})".format(
        minarca_version=__version__,
        rdiff_backup_version=get_rdiff_backup_version(),
        os_name=platform.system(),
        os_version=platform.release(),
        os_arch=platform.machine(),
    )


def get_minarca_exe(windowed=0):
    """
    Generate the appropriate command line for the scheduler.

    On Windows return minarca.exe to be in Windowed mode to avoid command line
    window to be created.
    """
    if IS_WINDOWS:
        name = 'minarcaw.exe' if windowed else 'minarca.exe'
    else:
        name = 'minarca'
    path = shutil.which(name, path=_get_path())
    if not path:
        raise FileNotFoundError(name)
    return Path(path).absolute()


def detach_call(args):
    """
    Create a subprogress in detached mode.
    """
    creationflags = (
        subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        if IS_WINDOWS
        else 0
    )
    return subprocess.Popen(
        args,
        stdin=None,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=creationflags,
    )


def file_read(fn, default=None, maxsize=4096):
    try:
        with open(fn, 'r') as f:
            return f.read(maxsize).strip()
    except OSError:
        # Silently ignore any os error
        return default


async def file_read_async(filepath: Path, errors='none'):
    try:
        async with aiofiles.open(filepath, 'r') as f:
            return await f.read()
    except OSError:
        if errors == 'none':
            return None
        raise


async def file_write_async(filepath: Path, text):
    async with aiofiles.open(filepath, 'w') as f:
        return await f.write(text)


def file_stat(self):
    try:
        return os.stat(self._fn)
    except FileNotFoundError:
        # Silently ignore error if file doesn't exists
        return None


async def watch_file(filename, poll_delay=0.25, timeout=None):
    """
    Return changes whenever the file get updated.
    """
    assert 0 < poll_delay
    assert timeout is None or poll_delay < timeout
    remaining_time = timeout or 1
    prev_stat = file_stat(filename)
    while 0 < remaining_time:
        await asyncio.sleep(poll_delay)
        if timeout:
            remaining_time = timeout - poll_delay
        new_stat = file_stat(filename)
        if prev_stat != new_stat:
            yield "changed"
        prev_stat = new_stat


def open_file_with_default_app(path):
    if IS_WINDOWS:
        os.startfile(path)
    elif IS_MAC:
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


class RobustRotatingFileHandler(RotatingFileHandler):
    """
    Robust logging rotating file handler for Windows.

    This rotating file handler handle the scenario when the log file
    is already open by another application and cannot be renamed on
    Windows operating system. Is such scenario, the logging will
    continue in the same file until the file can be renamed.
    """

    def emit(self, record):
        """
        Emit a record.

        Output the record to the file, catering for rollover as described
        in doRollover().
        """
        # Proceed with file rollover.
        # In case of error, rollback to original stream.
        try:
            if self.shouldRollover(record):
                self.doRollover()
        except Exception:
            pass
        try:
            FileHandler.emit(self, record)
        except Exception:
            self.handleError(record)


if IS_WINDOWS:
    import pythoncom  # @UnresolvedImport
    import pywintypes  # @UnresolvedImport
    import win32api  # @UnresolvedImport
    import win32com.client  # @UnresolvedImport

    TASK_CREATE_OR_UPDATE = 6
    TASK_LOGON_NONE = 0
    TASK_LOGON_PASSWORD = 1

    class WindowsScheduler:
        NAME = _('Minarca Backup')

        def __init__(self):
            pythoncom.CoInitialize()  # @UndefinedVariable
            self.scheduler = win32com.client.Dispatch('Schedule.Service')
            self.scheduler.Connect()

        def exists(self):
            # Get reference to the task name and check the executable.
            root_folder = self.scheduler.GetFolder('\\')
            try:
                root_folder.GetTask('\\' + self.NAME)
                return True
            except pywintypes.com_error:  # @UndefinedVariable
                return False

        @property
        def run_if_logged_out(self):
            """
            Return the current status of `run_if_logged_out`.
            """
            root_folder = self.scheduler.GetFolder('\\')
            try:
                task_def = root_folder.GetTask('\\' + self.NAME)
                return task_def.Definition.Principal.LogonType == TASK_LOGON_PASSWORD
            except pywintypes.com_error:  # @UndefinedVariable
                return False

        def create(self, run_if_logged_out=None):
            """
            Create entry in Windows Task Scheduler.
            """
            if self.exists():
                # Task already exists. leave.
                return

            root_folder = self.scheduler.GetFolder('\\')
            task_def = self.scheduler.NewTask(0)

            # Create time trigger every hour
            start_time = datetime.datetime.now() + datetime.timedelta(minutes=-1)
            TASK_TRIGGER_TIME = 1
            trigger = task_def.Triggers.Create(TASK_TRIGGER_TIME)
            trigger.StartBoundary = start_time.isoformat()
            trigger.Repetition.Duration = ""
            trigger.Repetition.Interval = "PT15M"  # 15 min interval

            # Create action
            TASK_ACTION_EXEC = 0
            action = task_def.Actions.Create(TASK_ACTION_EXEC)
            action.ID = 'MINARCA'
            action.Path = str(get_minarca_exe(windowed=True))
            action.Arguments = 'backup'

            # Set parameters
            task_def.RegistrationInfo.Description = _(
                "Keeps your Minarca Backup Software running. If this task is disabled "
                "or stopped, your Minarca backup will stop working. This task gets "
                "created when linking Minarca with a central backup server. When "
                "installing Minarca on a Windows Server, it's preferable to change "
                "the settings of this task and select 'Run whether user is logged "
                "on or not' to make sure the backup is running even when nobody is "
                "using the server."
            )
            task_def.Settings.Enabled = True
            task_def.Settings.StopIfGoingOnBatteries = False
            task_def.Settings.ExecutionTimeLimit = "PT0S"  # enable the task to run indefinitely

            # Register task
            # If task already exists, it will be updated
            try:
                root_folder.RegisterTaskDefinition(
                    self.NAME,  # Task name
                    task_def,
                    TASK_CREATE_OR_UPDATE,
                    run_if_logged_out[0] if run_if_logged_out else '',
                    run_if_logged_out[1] if run_if_logged_out else '',
                    TASK_LOGON_PASSWORD if run_if_logged_out else TASK_LOGON_NONE,
                )
            except pywintypes.com_error as e:
                winerror = e.excepinfo[5]
                raise OSError(None, win32api.FormatMessage(winerror), None, winerror)

        def delete(self):
            """
            Delete entry from Task Scheduler.

            This operation might required priviledge escalation.
            """
            root_folder = self.scheduler.GetFolder('\\')
            try:
                task = root_folder.GetTask('\\' + self.NAME)
            except pywintypes.com_error:  # @UndefinedVariable
                # Task doesn't exists
                return
            # Try deleting with current priviledges.
            try:
                root_folder.DeleteTask(task.Name, 0)
            except pywintypes.com_error as e:
                # If operation is denied, try deleting the task using runas
                # command line.
                winerror = e.excepinfo[5]
                if winerror == -2147024891:  # Access denied.
                    retcode = subprocess.call(['SCHTASKS.exe', '/Delete', '/TN', self.NAME, '/F'])
                    if retcode == 0:
                        return
                    raise OSError(None, win32api.FormatMessage(winerror), None, winerror)

    Scheduler = WindowsScheduler

if IS_MAC:
    import launchd  # @UnresolvedImport

    class MacScheduler:
        def __init__(self):
            self.plist = {
                "Label": "org.minarca.minarca-client.plist",
                "StartInterval": 900,  # 15 min interval
                "ProgramArguments": [str(get_minarca_exe()), "backup"],
            }
            self.label = self.plist['Label']

        def create(self):
            if self.exists():
                # Task already exists. leave.
                return
            # Create missing directory.
            fname = Path(launchd.plist.compute_filename(self.label, scope=launchd.plist.USER))
            fname.parent.mkdir(parents=1, exist_ok=1)
            # Dump plist file
            fname = launchd.plist.write(self.label, self.plist)
            launchd.load(fname)

        def delete(self):
            fname = launchd.plist.discover_filename(self.label)
            if fname:
                launchd.unload(fname)
                os.unlink(fname)

        def exists(self):
            job = launchd.LaunchdJob(self.label)
            return job.exists()

    Scheduler = MacScheduler

if IS_LINUX:
    from crontab import CronTab

    class CrontabScheduler:
        def __init__(self):
            self.cron = CronTab(user=True)
            minarca = get_minarca_exe()
            assert minarca
            self.command = '%s backup' % minarca

        def exists(self):
            jobs = list(self.cron.find_command(self.command))
            return bool(jobs)

        def create(self):
            if self.exists():
                # Task already exists. leave.
                return
            # Create the task.
            job = self.cron.new(command=self.command)
            now = datetime.datetime.now()
            start = now.minute % 15
            job.minute.on(start, start + 15, start + 30, start + 45)
            self.cron.write()

        def delete(self):
            return self.cron.remove_all(command=self.command)

    Scheduler = CrontabScheduler
