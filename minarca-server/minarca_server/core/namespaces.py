# Copyright (c) 2013 The Chromium OS Authors. All rights reserved.

import ctypes
import ctypes.util
import errno
import os
import signal
import socket
import subprocess
import sys
import time

from .mount import MS_NODEV, MS_NOEXEC, MS_NOSUID, MS_PRIVATE, MS_REC, MS_RELATIME, MS_SLAVE
from .mount import mount as _mount

CLONE_FS = 0x00000200
CLONE_FILES = 0x00000400
CLONE_NEWNS = 0x00020000
CLONE_NEWUTS = 0x04000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWUSER = 0x10000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000


def exit_as_status(status):
    """Exit the same way as |status|.
    If the status field says it was killed by a signal, then we'll do that to
    ourselves.  Otherwise we'll exit with the exit code.
    See http://www.cons.org/cracauer/sigint.html for more details.
    Args:
        status: A status as returned by os.wait type funcs.
    """
    exit_status = os.WEXITSTATUS(status)

    if os.WIFSIGNALED(status):
        # Kill ourselves with the same signal.
        sig_status = os.WTERMSIG(status)
        pid = os.getpid()
        os.kill(pid, sig_status)
        time.sleep(0.1)

        # Still here?  Maybe the signal was masked.
        try:
            signal.signal(sig_status, signal.SIG_DFL)
        except RuntimeError as e:
            if e.args[0] != errno.EINVAL:
                raise
        os.kill(pid, sig_status)
        time.sleep(0.1)

        # Still here?  Just exit.
        exit_status = 127

    # Exit with the code we want.
    sys.exit(exit_status)


def setns(fd, nstype):
    """Binding to the Linux setns system call. See setns(2) for details.

    Args:
        fd: An open file descriptor or path to one.
        nstype: Namespace to enter; one of CLONE_*.

    Raises:
        OSError: if setns failed.
    """
    try:
        fp = None
        if isinstance(fd, str):
            fp = open(fd)
            fd = fp.fileno()

        libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
        if libc.setns(ctypes.c_int(fd), ctypes.c_int(nstype)) != 0:
            e = ctypes.get_errno()
            raise OSError(e, os.strerror(e))
    finally:
        if fp is not None:
            fp.close()


def unshare(flags):
    """Binding to the Linux unshare system call. See unshare(2) for details.

    Args:
        flags: Namespaces to unshare; bitwise OR of CLONE_* flags.

    Raises:
        OSError: if unshare failed.
    """
    libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
    if libc.unshare(ctypes.c_int(flags)) != 0:
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e))


def _reap_children(pid):
    """Reap all children that get reparented to us until we see |pid| exit.

    Args:
        pid: The main child to watch for.

    Returns:
        The wait status of the |pid| child.
    """
    pid_status = 0

    while True:
        try:
            (wpid, status) = os.wait()
            if pid == wpid:
                # Save the status of our main child so we can exit with it below.
                pid_status = status
        except OSError as e:
            if e.errno == errno.ECHILD:
                break
            elif e.errno != errno.EINTR:
                raise

    return pid_status


def _safe_tcsetpgrp(fd, pgrp):
    """Set |pgrp| as the controller of the tty |fd|."""
    try:
        curr_pgrp = os.tcgetpgrp(fd)
    except OSError as e:
        # This can come up when the fd is not connected to a terminal.
        if e.errno == errno.ENOTTY:
            return
        raise

    # We can change the owner only if currently own it.  Otherwise we'll get
    # stopped by the kernel with SIGTTOU and that'll hit the whole group.
    if curr_pgrp == os.getpgrp():
        os.tcsetpgrp(fd, pgrp)


def create_pidns():
    """Start a new pid namespace

    This will launch all the right manager processes.  The child that returns
    will be isolated in a new pid namespace.

    If functionality is not available, then it will return w/out doing anything.

    Returns:
        The last pid outside of the namespace.
    """
    first_pid = os.getpid()

    try:
        # First create the namespace.
        unshare(CLONE_NEWPID)
    except OSError as e:
        if e.errno == errno.EINVAL:
            # For older kernels, or the functionality is disabled in the config,
            # return silently.  We don't want to hard require this stuff.
            return first_pid
        else:
            # For all other errors, abort.  They shouldn't happen.
            raise

    # Now that we're in the new pid namespace, fork.  The parent is the master
    # of it in the original namespace, so it only monitors the child inside it.
    # It is only allowed to fork once too.
    pid = os.fork()
    if pid:
        # Mask SIGINT with the assumption that the child will catch & process it.
        # We'll pass that back up below.
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # Forward the control of the terminal to the child so it can manage input.
        _safe_tcsetpgrp(sys.stdin.fileno(), pid)

        # Reap the children as the parent of the new namespace.
        exit_as_status(_reap_children(pid))
    else:
        # Make sure to unshare the existing mount point if needed.  Some distros
        # create shared mount points everywhere by default.
        try:
            _mount(None, '/proc', 'proc', MS_PRIVATE | MS_REC)
        except OSError as e:
            if e.errno != errno.EINVAL:
                raise

        # The child needs its own proc mount as it'll be different.
        _mount('proc', '/proc', 'proc', MS_NOSUID | MS_NODEV | MS_NOEXEC | MS_RELATIME)

        pid = os.fork()
        if pid:
            # Mask SIGINT with the assumption that the child will catch & process it.
            # We'll pass that back up below.
            signal.signal(signal.SIGINT, signal.SIG_IGN)

            # Now that we're in a new pid namespace, start a new process group so that
            # children have something valid to use.  Otherwise getpgrp/etc... will get
            # back 0 which tends to confuse -- you can't setpgrp(0) for example.
            os.setpgrp()

            # Forward the control of the terminal to the child so it can manage input.
            _safe_tcsetpgrp(sys.stdin.fileno(), pid)

            # Watch all of the children.  We need to act as the master inside the
            # namespace and reap old processes.
            exit_as_status(_reap_children(pid))

    # Create a process group for the grandchild so it can manage things
    # independent of the init process.
    os.setpgrp()

    # The grandchild will return and take over the rest of the sdk steps.
    return first_pid


def create_netns():
    """Start a new net namespace

    We will bring up the loopback interface, but that is all.

    If functionality is not available, then it will return w/out doing anything.
    """
    # The net namespace was added in 2.6.24 and may be disabled in the kernel.
    try:
        unshare(CLONE_NEWNET)
    except OSError as e:
        if e.errno == errno.EINVAL:
            return
        else:
            # For all other errors, abort.  They shouldn't happen.
            raise

    # Since we've unshared the net namespace, we need to bring up loopback.
    # The kernel automatically adds the various ip addresses, so skip that.
    try:
        subprocess.call(['ip', 'link', 'set', 'up', 'lo'])
    except OSError as e:
        if e.errno == errno.ENOENT:
            sys.stderr.write('warning: could not bring up loopback for network; ' 'install the iproute2 package\n')
        else:
            raise


def create_utsns(hostname=None):
    """Start a new UTS namespace

    If functionality is not available, then it will return w/out doing anything.
    """
    # The UTS namespace was added 2.6.19 and may be disabled in the kernel.
    try:
        unshare(CLONE_NEWUTS)
    except OSError as e:
        if e.errno != errno.EINVAL:
            return
        else:
            raise

    # hostname/domainname default to the parent namespace settings if unset
    if hostname is not None:
        socket.sethostname(hostname)


def create_userns():
    """Start a new user namespace

    If functionality is not available, then it will return w/out doing anything.
    """

    # Get original uid/gid values before they're changed on entering the namespace.
    uid = os.getuid()
    gid = os.getgid()

    try:
        unshare(CLONE_NEWUSER)
    except OSError as e:
        if e.errno == errno.EINVAL:
            return
        else:
            # For all other errors, abort.  They shouldn't happen.
            raise

    with open('/proc/self/setgroups', 'w') as f:
        f.write('deny')
    with open('/proc/self/uid_map', 'w') as f:
        f.write('0 %s 1\n' % uid)
    with open('/proc/self/gid_map', 'w') as f:
        f.write('0 %s 1\n' % gid)


def simple_unshare(mount=True, uts=True, ipc=True, net=False, pid=False, user=False, hostname=None):
    """Simpler helper for setting up namespaces quickly.

    If support for any namespace type is not available, we'll silently skip it.

    Args:
        mount: Create a mount namespace.
        uts: Create a UTS namespace.
        ipc: Create an IPC namespace.
        net: Create a net namespace.
        pid: Create a pid namespace.
        user: Create a user namespace.
        hostname: hostname to use for the UTS namespace
    """
    # user namespace must be first
    if user:
        create_userns()

    # The mount namespace is the only one really guaranteed to exist --
    # it's been supported forever and it cannot be turned off.
    if mount:
        unshare(CLONE_NEWNS)

        # Avoid mounts in the new namespace from affecting the parent namespace
        # on systems that share the rootfs by default, but allow events in the
        # parent to propagate down.
        try:
            _mount(None, '/', None, MS_REC | MS_SLAVE)
        except OSError as e:
            if e.errno != errno.EINVAL:
                raise

    if uts:
        create_utsns(hostname)

    # The IPC namespace was added 2.6.19 and may be disabled in the kernel.
    if ipc:
        try:
            unshare(CLONE_NEWIPC)
        except OSError as e:
            if e.errno != errno.EINVAL:
                pass

    if net:
        create_netns()

    if pid:
        create_pidns()
