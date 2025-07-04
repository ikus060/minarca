# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import asyncio
import logging
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
from importlib.metadata import distribution as get_distribution
from importlib.resources import files
from logging.handlers import RotatingFileHandler
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

IS_WINDOWS = sys.platform in ['win32']
IS_LINUX = sys.platform in ['linux', 'linux2']
IS_MAC = sys.platform == 'darwin'
HAS_DISPLAY = os.environ.get('DISPLAY', None) or IS_WINDOWS or IS_MAC

if IS_WINDOWS:
    import ntsecuritycon
    import pywintypes
    import win32api
    import win32con
    import win32security

    def get_sid(name):
        try:
            sid, _domain, _account_type = win32security.LookupAccountName(None, name)
            return sid
        except pywintypes.error:
            return None

    def build_access_mask(mode):
        """
        Convert a Unix chmod-style mode (e.g., 0o644) into corresponding Windows ACL masks
        for owner, group, and others.

        Returns:
            (owner_mask, group_mask, other_mask)
        """
        masks = []
        for shift in (6, 3, 0):  # owner, group, other
            bits = (mode >> shift) & 0b111
            mask = 0
            if bits & 0b100:
                mask |= ntsecuritycon.FILE_GENERIC_READ
            if bits & 0b010:
                mask |= ntsecuritycon.FILE_GENERIC_WRITE
            if bits & 0b001:
                mask |= ntsecuritycon.FILE_GENERIC_EXECUTE
            masks.append(mask)
        # owner: add ACL-safe extras
        masks[0] |= win32con.WRITE_DAC | win32con.WRITE_OWNER | ntsecuritycon.DELETE
        return tuple(masks)


def check_secure_file(filepath, mode=0o400):
    """
    Check if the given file is properly protected with the specified chmod mode.
    Supports both Unix and Windows.
    """
    if not IS_WINDOWS:
        st = os.stat(filepath)
        if st.st_uid != os.getuid():
            raise PermissionError(f"File '{filepath}' must be owned by the current user.")

        actual = st.st_mode & 0o777
        if actual != mode:
            raise PermissionError(f"File '{filepath}' has permissions {oct(actual)}, expected {oct(mode)}.")
        return

    # Get current user SID
    current_user = win32security.LookupAccountName(None, win32api.GetUserName())
    current_user_sid = current_user[0]

    # Get the file security descriptor
    sd = win32security.GetFileSecurity(
        filepath,
        win32security.DACL_SECURITY_INFORMATION | win32security.OWNER_SECURITY_INFORMATION,
    )

    # Check ownership
    owner_sid = sd.GetSecurityDescriptorOwner()
    if owner_sid != current_user_sid:
        raise PermissionError(f"File '{filepath}' must be owned by the current user.")

    # Lookup well-known SIDs
    system_sid = get_sid("SYSTEM")
    admin_sid = get_sid("Administrators")
    everyone_sid = get_sid("Everyone")

    # Track permission expectations
    owner_bits, group_bits, other_bits = build_access_mask(mode)
    expected = {
        str(current_user_sid): owner_bits,
        str(system_sid): group_bits,
        str(admin_sid): group_bits,
        str(everyone_sid): other_bits,
    }

    # Check DACL
    dacl = sd.GetSecurityDescriptorDacl()
    if dacl is None:
        raise PermissionError(f"No DACL on '{filepath}', may be world-accessible.")

    # Check all ACEs
    for i in range(dacl.GetAceCount()):
        ace = dacl.GetAce(i)
        ace_sid = ace[2]
        access_mask = ace[1]

        expected_mask = expected.get(str(ace_sid), 0)
        if access_mask != expected_mask:
            try:
                sid_name, _, _ = win32security.LookupAccountSid(None, ace_sid)
            except Exception:
                sid_name = "UNKNOWN"
            raise PermissionError(
                f"File '{filepath}' grants incorrect permissions to '{sid_name}': "
                f"{oct(access_mask)} instead of {oct(expected_mask)}"
            )


def secure_file(filepath, mode=0o400):
    """
    Adjust file permissions using Unix-style chmod value.
    On Windows, emulate with:
    - ACLs for owner/group/other
    - FILE_ATTRIBUTE_READONLY if owner can't write
    - FILE_ATTRIBUTE_HIDDEN if filename starts with "."
    """
    #

    if not IS_WINDOWS:
        os.chmod(filepath, mode)
        return

    # Extract permission bits
    owner_bits, group_bits, other_bits = build_access_mask(mode)

    # Get current file attributes
    attrs = win32api.GetFileAttributes(str(filepath))

    # Try to adjust hidden flag before updating permissions
    filename = os.path.basename(filepath)
    if filename.startswith("."):
        attrs |= win32con.FILE_ATTRIBUTE_HIDDEN
    else:
        attrs &= ~win32con.FILE_ATTRIBUTE_HIDDEN
    if not (mode & stat.S_IRUSR):
        attrs |= win32con.FILE_ATTRIBUTE_READONLY
    else:
        attrs &= ~win32con.FILE_ATTRIBUTE_READONLY
    # Try to write file attributes.
    try:
        win32api.SetFileAttributes(str(filepath), attrs)
    except pywintypes.error:
        pass

    # Get SIDs
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
    owner_sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
    system_sid = get_sid("SYSTEM")
    admin_sid = get_sid("Administrators")
    everyone_sid = get_sid("Everyone")

    # Build DACL
    dacl = win32security.ACL()
    if owner_bits:
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, owner_bits, owner_sid)
    if group_bits:
        if system_sid:
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, group_bits, system_sid)
        if admin_sid:
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, group_bits, admin_sid)
    if other_bits and everyone_sid:
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, other_bits, everyone_sid)

    # Apply security descriptor
    sd = win32security.SECURITY_DESCRIPTOR()
    sd.SetSecurityDescriptorOwner(owner_sid, False)
    sd.SetSecurityDescriptorDacl(1, dacl, 0)

    win32security.SetFileSecurity(
        str(filepath), win32security.DACL_SECURITY_INFORMATION | win32security.OWNER_SECURITY_INFORMATION, sd
    )
    # Try to write file attributes.
    try:
        win32api.SetFileAttributes(str(filepath), attrs)
    except pywintypes.error:
        pass


def ssh_keygen(public_key, private_key, length=2048):
    """
    Generate public and private SSH Key-pair.
    """
    key = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, key_size=length)
    private_key_bytes = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()
    )
    public_key_bytes = key.public_key().public_bytes(serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH)
    with open(private_key, 'wb') as f:
        f.write(private_key_bytes)
    with open(public_key, 'wb') as f:
        f.write(public_key_bytes)
    # Set proper permissions on private key.
    secure_file(private_key)


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


def nice():
    """Increase the niceness of the process to below normal."""
    import psutil

    try:
        if IS_WINDOWS:
            # On Windows,
            p = psutil.Process(os.getpid())
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else:
            if os.nice(0) == 0:
                os.nice(10)
    except Exception:
        # Just log the error.
        logging.getLogger(__name__).warning('fail to lower process priority', exc_info=1)


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
    import aiofiles

    try:
        async with aiofiles.open(filepath, 'r') as f:
            return await f.read()
    except OSError:
        if errors == 'none':
            return None
        raise


async def file_write_async(filepath: Path, text):
    import aiofiles

    async with aiofiles.open(filepath, 'w') as f:
        return await f.write(text)


def file_stat(filename):
    try:
        return os.stat(filename)
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


def stop_process(pid):
    """
    Gently terminate a process and all it's children.
    """
    import signal

    import psutil

    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return True

    try:
        # Step 1: Try a gentle shutdown with SIGINT
        parent.send_signal(signal.SIGINT)

        # Step 2: Wait up to 3 seconds for the process to exit
        try:
            parent.wait(timeout=3)
            return True
        except psutil.TimeoutExpired:
            # Step 3: Terminate children
            children = parent.children(recursive=True)
            for child in children:
                if child.is_running():
                    child.terminate()
            _gone, alive = psutil.wait_procs(children, timeout=1)
            for child in alive:
                child.kill()

            # Step 4: Terminate main process
            if parent.is_running():
                parent.terminate()

            try:
                parent.wait(timeout=1)
            except psutil.TimeoutExpired:
                parent.kill()

    except (psutil.NoSuchProcess, SystemError):
        return False


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
            logging.FileHandler.emit(self, record)
        except Exception:
            self.handleError(record)
