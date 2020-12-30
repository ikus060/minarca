# -*- coding: utf-8 -*-
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
import logging
import os
from subprocess import Popen
import sys
import tempfile

from rdiffweb.core.config import read_config


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
    rdiffweb_logfile = cfg.get('logfile', '/var/log/minarca/server.log')
    shell_logfile = os.path.join(os.path.dirname(rdiffweb_logfile), 'shell.log')
    fmt = "[%(asctime)s][%(levelname)-7s][%(ip)s][%(user)s][%(threadName)s][%(name)s] %(message)s"
    try:
        logging.basicConfig(
            filename=shell_logfile,
            level=logging.DEBUG,
            format=fmt)
    except FileNotFoundError:
        # If the file can't be open will need to log to a temporary file.
        shell_logfile = os.path.join(tempfile.gettempdir(), 'minarca-shell.log')
        logging.basicConfig(
            filename=shell_logfile,
            level=logging.DEBUG,
            format=fmt)


def _exec(cmd, cwd):

    with Popen(cmd, cwd=cwd, stdout=sys.stdout.fileno(), stderr=sys.stderr.fileno()) as p:
        try:
            return p.wait(timeout=None)
        except:
            p.kill()
            raise


def _load_config():
    cfg = {}
    for file in ["/etc/minarca/minarca-server.conf", "/etc/minarca/minarca-shell.conf"]:
        try:
            cfg.update(read_config(file))
        except:
            pass
    return cfg


def main(args=None):
    # Read the configuration and setup logging
    cfg = _load_config()
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
    _extra_args = cfg.get('rdiffbackup_args', [])
    if _extra_args:
        _extra_args = _extra_args.split(' ')

    # Either we get called by rdiff-backup directly
    # or we get called by minarca client which replace the command by the name of the repository.
    if ssh_original_command in ["echo -n 1", "echo -n host is alive", "/usr/bin/rdiff-backup -V"]:
        # Used by backup-ninja to verify connectivity
        _exec(
            cmd=ssh_original_command.split(' '),
            cwd=userroot)
    elif ssh_original_command == "rdiff-backup --server":
        # When called by legacy rdiff-backup.
        logger.info("running legacy command: %s", ssh_original_command)
        _exec(
            cmd=["rdiff-backup", "--server"] + _extra_args,
            cwd=userroot)
    else:
        # When called by minarca client, the command should be the name of the repository.
        # Validate if the repository is valid.
        reponame = ssh_original_command
        repopath = os.path.normpath(os.path.join(userroot, reponame))
        if not repopath.startswith(userroot):
            logger.info("invalid repo: %s", reponame)
            print("ERROR repository name %s is not valid" % reponame, file=sys.stderr)
            exit(1)
        # Start rdiff-backup server
        logger.info("starting rdiff-backup in repopath: %s", repopath)
        _exec(
            cmd=['rdiff-backup', '--server', '--restrict=' + reponame] + _extra_args,
            cwd=userroot)


if __name__ == '__main__':
    main()
