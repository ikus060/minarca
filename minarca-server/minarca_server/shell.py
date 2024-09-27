#
# Minarca server
#
# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Sep. 25, 2020

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import argparse
import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
from collections import deque

import configargparse
from tzlocal import get_localzone

from minarca_server.config import get_parser
from minarca_server.core.jail import Jail

try:
    import pkg_resources

    __version__ = pkg_resources.get_distribution("minarca-server").version
except Exception:
    __version__ = 'DEV'

DEFAULT_RDIFF_BACKUP_VERSION = '2.0'


def _setup_logging(cfg):
    """
    Configure minarca-shell log file.
    """
    # For backward compatibility use logfile as a reference to define the
    # location of the minarca-shell log file.
    if cfg.log_file:
        shell_logfile = os.path.join(os.path.dirname(cfg.log_file), 'shell.log')
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        default_handler = logging.handlers.RotatingFileHandler(shell_logfile, maxBytes=10485760, backupCount=20)
        default_handler.setFormatter(
            logging.Formatter("[%(asctime)s][%(levelname)-7s][%(ip)s][%(user)s][PID:%(process)d][%(name)s] %(message)s")
        )
        root.addHandler(default_handler)


def _jail(userroot, args):
    """
    Create a chroot jail using namespaces to isolate completely
    rdiff-backup execution.
    """
    tz = get_localzone().zone
    with Jail(userroot):
        process = subprocess.Popen(
            args, cwd=userroot, env={'LANG': 'en_US.utf-8', 'TZ': tz, 'HOME': userroot}, stderr=subprocess.PIPE
        )
        # This implementation capture the last 25 lines of output.
        last_logs = deque(maxlen=25)
        out = sys.stderr.buffer
        try:
            line = process.stderr.readline()
            while line:
                last_logs.append(line)
                out.write(line)
                out.flush()
                line = process.stderr.readline()
        except BrokenPipeError:
            pass
        # Wait for the process to finish
        process.stderr.close()
        retcode = process.wait()
        if retcode:
            raise subprocess.CalledProcessError(
                retcode, args[0], stderr=''.join([line.decode('utf-8', 'replace') for line in last_logs])
            )


def _find_rdiff_backup(version=DEFAULT_RDIFF_BACKUP_VERSION):
    return shutil.which('rdiff-backup-%s' % (version,))


def _parse_config():
    """
    Use the default configuration parser to retrieve the configuration from environment variable or
    config file. But to avoid any parsing error, keep only the values we are interested in.
    """
    server_parser = get_parser()
    parser = configargparse.ArgumentParser(
        default_config_files=server_parser._default_config_files, auto_env_var_prefix=server_parser._auto_env_var_prefix
    )
    parser.add_argument('--log-file', '--logfile', default=server_parser._defaults['log_file'])
    parser.add_argument('--minarca-rdiff-backup-extra-args', '--rdiffbackup-args')
    return parser.parse_known_args(args=[])[0]


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.parse_args(args)

    # Try to configure logging system using minarca-server config.
    cfg = _parse_config()
    _setup_logging(cfg)

    # Parse arguments
    username = os.environ.get('MINARCA_USERNAME')
    userroot = os.environ.get('MINARCA_USER_ROOT')

    # Add current user and ip address to logging context
    ip = os.environ.get('SSH_CLIENT', '').split(' ')[0]
    logger = logging.getLogger(__name__)
    logger = logging.LoggerAdapter(logger, {'user': username, 'ip': ip})

    # Check if folder exists
    if not userroot or not os.path.isdir(userroot):
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
    try:
        if ssh_original_command in ["echo -n 1", "echo -n host is alive"]:
            # Used by backup-ninja to verify connectivity
            subprocess.check_call(
                ssh_original_command.split(' '),
                env={'LANG': 'en_US.utf-8'},
                stdout=sys.stdout.fileno(),
                stderr=sys.stderr.fileno(),
            )
        elif ssh_original_command in ["/usr/bin/rdiff-backup -V"]:
            rdiff_backup = _find_rdiff_backup()
            subprocess.check_call(
                [rdiff_backup, '-V'],
                env={'LANG': 'en_US.utf-8'},
                stdout=sys.stdout.fileno(),
                stderr=sys.stderr.fileno(),
            )
        else:
            if ssh_original_command.startswith("rdiff-backup ") and "--server" in ssh_original_command:
                # When called directly by rdiff-backup.
                # So let use default rdiff-backup version.
                rdiff_backup = _find_rdiff_backup()
            elif 'minarca/' in ssh_original_command:
                # When called by Minarca, we receive a user agent string.
                if 'rdiff-backup/1.2.8' in ssh_original_command:
                    rdiff_backup = _find_rdiff_backup(version='1.2')
                elif 'rdiff-backup/2.0' in ssh_original_command:
                    rdiff_backup = _find_rdiff_backup(version='2.0')
                elif 'rdiff-backup/2.2' in ssh_original_command:
                    rdiff_backup = _find_rdiff_backup(version='2.2')
                else:
                    logger.info("unsupported version: %s", ssh_original_command)
                    print("ERROR: unsupported version: %s" % ssh_original_command, file=sys.stderr)
                    sys.exit(1)
            else:
                # When called by legacy minarca client with rdiff-backup v1.2.8.
                # the command should be the name of the repository.
                rdiff_backup = _find_rdiff_backup(version='1.2')

            # Run the server in chroot jail.
            cmd = [rdiff_backup, '--server'] + _extra_args
            logger.info("running command [%s] in jail [%s] for: %s", ' '.join(cmd), userroot, ssh_original_command)
            try:
                _jail(userroot, cmd)
                logger.info("rdiff-backup terminated successfully")
            except PermissionError:
                logger.error(
                    "Fail to create rdiff-backup jail. If you are running minarca-shell in Docker, make sure you started the container with `--privileged`. If you are on Debian, make sure to disable userns hardening `echo 1 > /proc/sys/kernel/unprivileged_userns_clone`.",
                    exc_info=1,
                )
    except subprocess.CalledProcessError as e:
        logger.warning("%s Last output: \n%s" % (e, e.stderr))
    except Exception:
        logger.error("unhandled exception in minarca-shell", exc_info=1)


if __name__ == '__main__':
    main()
