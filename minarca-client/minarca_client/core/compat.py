# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import datetime
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
from contextlib import contextmanager

import pkg_resources

from minarca_client.locale import _

IS_WINDOWS = os.name == 'nt'
IS_LINUX = sys.platform in ['linux', 'linux2']
IS_MAC = sys.platform == 'darwin'
HAS_DISPLAY = os.environ.get('DISPLAY', None) or IS_WINDOWS or IS_MAC


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


def get_is_admin():
    if IS_WINDOWS:
        return False
    else:
        return os.geteuid() == 0


IS_ADMIN = get_is_admin()


def get_home(is_admin=IS_ADMIN):
    if is_admin:
        if IS_WINDOWS:
            return os.path.join(
                os.path.abspath(os.environ.get('WINDIR', 'C:/Windows')), 'System32/config/systemprofile'
            )
        else:
            return "/root"
    else:
        return os.path.abspath(str(pathlib.Path.home()))


def get_local_appdata(is_admin=IS_ADMIN):
    """
    Return Local App folder.
    """
    return os.path.abspath(os.environ.get("LOCALAPPDATA", os.path.join(get_home(is_admin), "AppData", "Local")))


@makedirs
def get_log_path(is_admin=IS_ADMIN):
    """
    Return the location of the log file.
    """
    if IS_WINDOWS:
        return os.path.join(get_local_appdata(is_admin), "minarca")
    elif IS_MAC:
        return os.path.join(get_home(), "Library/Logs/Minarca")
    # IS_LINUX
    if is_admin:
        return "/var/log"
    return get_data_home(is_admin)


def get_log_file(is_admin=IS_ADMIN):
    return os.path.join(get_log_path(is_admin), "minarca.log")


@makedirs
def get_config_home(is_admin=IS_ADMIN):
    if os.environ.get('MINARCA_CONFIG_HOME'):
        return os.path.abspath(os.environ.get('MINARCA_CONFIG_HOME'))
    if IS_WINDOWS:
        return os.path.join(get_local_appdata(is_admin), "minarca")
    elif IS_MAC:
        return os.path.join(get_home(is_admin), "Library/Preferences/Minarca")
    # IS_LINUX
    if is_admin:
        return "/etc/minarca"
    return os.path.abspath(
        os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(get_home(is_admin), ".config/")), "minarca")
    )


@makedirs
def get_data_home(is_admin=IS_ADMIN):
    if os.environ.get('MINARCA_DATA_HOME'):
        return os.path.abspath(os.environ.get('MINARCA_DATA_HOME'))
    if IS_WINDOWS:
        return os.path.join(get_local_appdata(is_admin), "minarca")
    elif IS_MAC:
        return os.path.join(get_home(is_admin), "Library/Minarca")
    # IS_LINUX
    if is_admin:
        return "/var/lib/minarca"
    else:
        return os.path.abspath(
            os.path.join(os.environ.get("XDG_DATA_HOME", os.path.join(get_home(is_admin), ".local/share/")), "minarca")
        )


def _get_path():
    """
    Return PATH lookup
    """
    path = os.environ.get('PATH', 'C:\\Windows\\system32' if IS_WINDOWS else '/usr/bin')
    path = os.path.dirname(sys.executable) + os.pathsep + path
    if IS_WINDOWS:
        ssh_path = pkg_resources.resource_filename(__name__, 'openssh\\win_%s' % platform.machine().lower())
        path = ssh_path + os.pathsep + path
    return path


def get_rdiff_backup_version():
    """
    Return the version of rdiff-backup
    """
    try:
        return pkg_resources.get_distribution("rdiff-backup").version
    except Exception:
        return 'unknown'


def get_ssh():
    """
    Return the location of SSH executable.
    """
    if os.environ.get('MINARCA_SSH'):
        return os.environ.get('MINARCA_SSH')
    name = 'ssh.exe' if IS_WINDOWS else 'ssh'
    path = _get_path()
    ssh = shutil.which(name, path=path)
    if not ssh:
        raise FileNotFoundError(name)
    return ssh


def get_ssh_keygen():
    """
    Return the location of SSH executable.
    """
    if os.environ.get('MINARCA_SSH_KEYGEN'):
        return os.environ.get('MINARCA_SSH_KEYGEN')
    name = 'ssh-keygen.exe' if IS_WINDOWS else 'ssh-keygen'
    ssh_keygen = shutil.which(name, path=_get_path())
    if not ssh_keygen:
        raise FileNotFoundError(name)
    return ssh_keygen


def get_temp():
    return tempfile.gettempdir()


def get_user_agent():
    from minarca_client.main import __version__

    return "minarca/{minarca_version} rdiff-backup/{rdiff_backup_version} ({os_name} {os_version} {os_arch})".format(
        minarca_version=__version__,
        rdiff_backup_version=get_rdiff_backup_version(),
        os_name=platform.system(),
        os_version=platform.release(),
        os_arch=platform.machine(),
    )


def get_minarca_exe():
    """
    Generate the appropriate command line for the scheduler.

    On Windows return minarcaw.exe to be in Windowed mode to avoid command line
    window to be created.
    """
    name = 'minarcaw.exe' if IS_WINDOWS else 'minarca'
    path = shutil.which(name, path=_get_path())
    if not path:
        raise FileNotFoundError(name)
    return os.path.abspath(path)


def ssh_keygen(public_key, private_key, length=2048):
    """
    Generate public and private SSH Keys.
    """
    # On Windows, pychrypto is not available. For this reason we are using
    # ssh-keygen directly to generate RSA key.
    tmp = tempfile.TemporaryDirectory()
    subprocess.run(
        [get_ssh_keygen(), '-b', str(length), '-t', 'rsa', '-f', os.path.join(tmp.name, 'id_rsa'), '-q', '-N', ''],
        stdout=subprocess.PIPE,
        check=True,
        cwd=tmp.name,
        env={},
    )
    shutil.move(os.path.join(tmp.name, 'id_rsa'), private_key)
    shutil.move(os.path.join(tmp.name, 'id_rsa.pub'), public_key)
    tmp.cleanup()


class _RedirectOutput:
    """
    Used to redirect std to logging.
    """

    def __init__(self, logger):
        self.logger = logger
        self.buffer = self
        self.encoding = 'utf-8'

    def write(self, value):
        # Write each lines to logging.
        if hasattr(value, 'decode'):
            value = value.decode(self.encoding)
        for line in value.splitlines():
            self.logger.debug(' local:' + line.rstrip())

    def flush(self):
        # Nothing to be flushed
        pass


@contextmanager
def redirect_ouput(logger):
    """
    Context manager to replace stdout and stderr for Rdiff-backup to
    redirect them to logging.

    Also need to redirect stderr at file descriptor level because it's used by
    ssh.exe sub-process.
    """

    def _reader_thread(fd):
        try:
            with open(fd, 'r') as f:
                line = f.readline()
                while line:
                    logger.debug('remote: ' + line.rstrip())
                    line = f.readline()
        except OSError:
            # OS Error 9 may happen in case of race condition.
            logger.exception('fail to pipe')

    if IS_WINDOWS and (sys.stderr is None or sys.stderr.__class__.__name__ == 'NullWriter'):
        # With PyInstaller, stderr is undefined.
        import win32api

        r_fd, w_fd = os.pipe()
        win32api.SetStdHandle(win32api.STD_ERROR_HANDLE, w_fd)
        stderr_copy = None
    else:
        # Copy original file descriptor
        _old_stderr_fd = sys.stderr.fileno()
        stderr_copy = os.fdopen(os.dup(_old_stderr_fd), 'wb')
        # Replace stderr file descriptor by our pipe
        r_fd, w_fd = os.pipe()
        os.dup2(w_fd, _old_stderr_fd)
    # Start a thread to read the pipe.
    t = threading.Thread(target=_reader_thread, args=(r_fd,))
    t.daemon = True
    t.start()
    try:
        # Make replacement at python level
        _old_stdout = sys.stdout
        _old_stderr = sys.stderr
        sys.stdout = sys.stderr = _RedirectOutput(logger)
        try:
            yield
        finally:
            # Restore stdout and stderr
            sys.stdout = _old_stdout
            sys.stderr = _old_stderr
    finally:
        # Restore file descriptor
        if stderr_copy:
            os.dup2(stderr_copy.fileno(), _old_stderr_fd)
            stderr_copy.close()
        # Close pipe
        os.close(w_fd)
        # Stop thread (wait maximum 5 sec)
        t.join(timeout=5)


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
            action.Path = get_minarca_exe()
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
                "ProgramArguments": [get_minarca_exe(), "backup"],
            }
            self.label = self.plist['Label']

        def create(self):
            if self.exists():
                # Task already exists. leave.
                return
            # Create missing directory.
            fname = launchd.plist.compute_filename(self.label, scope=launchd.plist.USER)
            if not os.path.exists(os.path.dirname(fname)):
                os.mkdir(os.path.dirname(fname))
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
