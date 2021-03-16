#
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Sep. 25, 2020

@author: Patrik Dufresne
'''

import argparse
from functools import reduce
import logging
import operator
import os
import shutil
import subprocess
import sys
import tempfile

from rdiffweb.core.config import parse_args
from snakeoil.contexts import SplitExec
from snakeoil.osutils.mount import mount, MS_BIND, MS_REC, MS_RDONLY
from snakeoil.process import namespaces


class Jail(SplitExec):
    """
    Responsible to provide a context manager to split execution into a separate
    process, then using user namespace and chroot isolate the execution
    into a sandbox.
    
    path will be the only writable folder. Everything else is read-only.
    
    Only part of the filesystem is available: /bin, /lib, /lib64, /opt, /usr

    See https://lwn.net/Articles/531114/ about Linux User Namespace.
    """

    def __init__(self, path=None):
        SplitExec.__init__(self)
        self.root = tempfile.mkdtemp(prefix='minarca-jail-')
        self.path = path
        if self.path:
            self.path = os.path.abspath(self.path)

    def _child_setup(self):
        # Create a user namespace for isolation.
        namespaces.simple_unshare(user=True, mount=True, uts=False, net=True, pid=False)

        # Mount proc
        os.mkdir(os.path.join(self.root, 'proc'))
        mount(source='/proc', target=os.path.join(self.root, 'proc'), fstype=None, flags=MS_BIND | MS_REC)
        # Create default mountpoint to run executables.
        for mountpoint in ['/bin', '/lib', '/lib64', '/usr', '/opt']:
            if not os.path.isdir(mountpoint):
                continue
            dest = os.path.join(self.root, mountpoint[1:])
            os.mkdir(dest)
            mount(source=mountpoint, target=dest, fstype=None, flags=reduce(operator.or_, [MS_BIND, MS_REC, MS_RDONLY], 0))
        # Create custom mount point
        if self.path:
            dest = os.path.join(self.root, self.path[1:])
            os.makedirs(dest)
            mount(source=self.path, target=dest, fstype=None, flags=reduce(operator.or_, [MS_BIND, MS_REC], 0))
        # chroot
        os.chmod(self.root, 0o700)
        os.chroot(self.root)
        os.chdir('/')

    def _cleanup(self):
        shutil.rmtree(self.root)


def _parse_args(args):
    parser = argparse.ArgumentParser(description='Minarca shell called to handle incoming SSH connection.')
    parser.add_argument('username')
    parser.add_argument('userroot')
    # TODO parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    return parser.parse_args(args)


def _setup_logging(cfg):
    """
    Configure minarca-shell log file.
    """
    # For backward compatibility use logfile as a reference to define the
    # location of the minarca-shell log file.
    if cfg.log_file:
        shell_logfile = os.path.join(os.path.dirname(cfg.log_file), 'shell.log')
        fmt = "[%(asctime)s][%(levelname)-7s][%(ip)s][%(user)s][%(threadName)s][%(name)s] %(message)s"
        logging.basicConfig(
            filename=shell_logfile,
            level=logging.DEBUG,
            format=fmt)


def _jail(userroot, args):
    """
    Create a chroot jail using namespaces to isolate completely
    rdiff-backup execution.
    """
    with Jail(userroot):
        subprocess.check_call(args, cwd=userroot, env={'LANG': 'en_US.utf-8', 'HOME': userroot})


def main(args=None):
    # Read the configuration and setup logging
    cfg = parse_args(args=[])
    _setup_logging(cfg)

    # Parse arguments
    args = _parse_args(args or sys.argv[1:])
    username = args.username
    userroot = args.userroot

    # Add current user and ip address to logging context
    ip = os.environ.get('SSH_CLIENT', '').split(' ')[0]
    logger = logging.getLogger(__name__)
    logger = logging.LoggerAdapter(logger, {'user':username, 'ip':ip})

    # Check if folder exists
    if not os.path.isdir(userroot):
        logger.info("invalid user home: %s", userroot)
        print("ERROR user home directory is miss configured.", file=sys.stderr)
        sys.exit(1)

    # Get Original ssh command from environment variable.
    ssh_original_command = os.environ.get("SSH_ORIGINAL_COMMAND", '')
    if not ssh_original_command:
        print("ERROR no command provided.", file=sys.stderr)
        sys.exit(1)

    # Get extra arguments for rdiff-backup.
    _extra_args = cfg.minarca_rdiff_backup_extra_args
    if _extra_args:
        _extra_args = _extra_args.split(' ')
    else:
        _extra_args = []

    # Either we get called by rdiff-backup directly
    # or we get called by minarca client which replace the command by the name of the repository.
    if ssh_original_command in ["echo -n 1", "echo -n host is alive", "/usr/bin/rdiff-backup -V"]:
        # Used by backup-ninja to verify connectivity
        subprocess.check_call(ssh_original_command.split(' '), env={'LANG': 'en_US.utf-8'}, stdout=sys.stdout.fileno(), stderr=sys.stderr.fileno())
    else:
        # When called by minarca client, the command should be the name of the repository.
        # Validate if the repository is valid.
        cmd = ['rdiff-backup', '--server'] + _extra_args
        logger.info("running command [%s] in jail [%s]", ' '.join(cmd), userroot)
        try:
            _jail(userroot, cmd)
        except OSError:
            logger.error("Fail to create rdiff-backup jail. If you are running minarca-shell in Docker, make sure you started the container with `--privileged`. If you are on Debian, make sure to disable userns hardening `echo 1 > /proc/sys/kernel/unprivileged_userns_clone`.", exc_info=1)


if __name__ == '__main__':
    main()
