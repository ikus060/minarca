# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.


import getpass
import logging
import logging.handlers
import os
import signal
import sys
from argparse import ArgumentParser

import pkg_resources

from minarca_client import __version__
from minarca_client.core import (Backup, BackupError, NotRunningError,
                                 NotScheduleError, RepositoryNameExistsError,
                                 RunningError)
from minarca_client.core.compat import get_log_file
from minarca_client.core.config import Pattern, Settings
from minarca_client.locale import _
from minarca_client.ui.connect import SetupDialog
from minarca_client.ui.home import HomeDialog
from minarca_client.ui.tkvue import configure_tk

_EXIT_BACKUP_FAIL = 1
_EXIT_ALREADY_LINKED = 2
_EXIT_MISSING_PASSWD = 3
_EXIT_REPO_EXISTS = 4
_EXIT_NOT_RUNNING = 5

_ARGS_ALIAS = {
    '--backup': 'backup',
    '--stop': 'stop',
    '--status': 'status',
}


def _backup(force):
    signal.signal(signal.SIGINT, signal.default_int_handler)
    backup = Backup()
    try:
        backup.start(force)
    except (NotScheduleError, RunningError) as e:
        # Print message to stdout and log file.
        logging.info(str(e))
        sys.exit(_EXIT_BACKUP_FAIL)
    except BackupError:
        # Other backup error are logged with status
        sys.exit(_EXIT_BACKUP_FAIL)


def _link(remoteurl, username, name, force, password=None):
    """
    Start the linking process in command line.
    """
    # TODO Support username and password in remoteurl
    backup = Backup()
    # If the backup is already linked, return an error.
    if backup.is_linked():
        print(_('minarca is already linked, execute `minarca unlink`'))
        sys.exit(_EXIT_ALREADY_LINKED)
    # Prompt for password if missing.
    if not password:
        password = getpass.getpass(prompt=_('password: '))
    if not password:
        print(_('a password is required'))
        sys.exit(_EXIT_MISSING_PASSWD)
    try:
        backup.link(
            remoteurl=remoteurl,
            username=username,
            password=password,
            repository_name=name,
            force=force)
    except RepositoryNameExistsError:
        sys.exit(_EXIT_REPO_EXISTS)


def _pattern(include, pattern):
    backup = Backup()
    new_patterns = backup.get_patterns()
    for path in pattern:
        p = Pattern(include, path, None)
        if not p.is_wildcard():
            # Resolve relative path
            path = os.path.normpath(os.path.join(os.getcwd(), path))
            p = Pattern(include, path, None)
        new_patterns.append(p)
    backup.set_patterns(new_patterns)


def _patterns():
    backup = Backup()
    patterns = backup.get_patterns()
    patterns.write(sys.stdout)


def _stop(force):
    backup = Backup()
    try:
        backup.stop()
    except NotRunningError:
        print(_('backup not running'))
        if not force:
            sys.exit(_EXIT_NOT_RUNNING)


def _schedule(schedule=None):
    backup = Backup()
    backup.schedule(schedule=schedule)


def _status():
    backup = Backup()
    status = backup.get_status()
    settings = backup.get_settings()
    try:
        backup.test_server()
        connected = True
    except BackupError:
        connected = False
    print(_("Remote server:          %s") % settings['remotehost'])
    print(_("Connectivity status:    %s" %
            (_("Connected") if connected else _("Not connected"))))
    print(_("Last successful backup: %s") %
          status.get('lastsuccess', _('Never')))
    print(_("Last backup date:       %s") % status.get('lastdate', _('Never')))
    print(_("Last backup status:     %s") %
          status.get('lastresult', _('Never')))
    print(_("Details:                %s") % status.get('details', ''))


def _ui():
    """
    Entry point to start minarca user interface.
    """
    # Configure TK with our theme.
    theme_file = pkg_resources.resource_filename('minarca_client.ui', 'theme/minarca.tcl')
    configure_tk(basename='Minarca', classname='Minarca', icon='minarca-128', theme='minarca', theme_source=theme_file)

    # If not linked, let the user configure mianrca
    backup = Backup()
    if not backup.is_linked():
        dlg = SetupDialog()
        dlg.mainloop()
        if not backup.is_linked():
            # Operation canceled by user
            return

    home = HomeDialog()
    home.mainloop()


def _unlink():
    backup = Backup()
    backup.unlink()


def _parse_args(args):
    parser = ArgumentParser(
        description="Minarca manage your combuter backups by linking your computer with a centralized server and running backups on a given schedule.",
        add_help=True)
    # Check if the application should default to GUI mode.
    is_ui = parser.prog in ['minarcaw', 'minarcaw.exe']

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s ' + __version__)
    parser.add_argument(
        '-d', '--debug',
        action='store_true')

    #
    # Define subcommands
    #
    subparsers = parser.add_subparsers(dest='subcommand', required=not is_ui)
    if is_ui:
        parser.set_defaults(func=_ui)

    # Backup
    sub = subparsers.add_parser(
        'backup',
        help=_('start a backup'))
    sub.add_argument(
        '--force',
        action='store_true',
        help=_("force execution of a backup even if it's not time to run"))
    sub.set_defaults(func=_backup)

    # exclude
    sub = subparsers.add_parser(
        'exclude',
        help=_('exclude files to be backup'))
    sub.add_argument(
        'pattern',
        nargs='+',
        help=_('file pattern to be exclude. may contains `*` or `?` wildcard'))
    sub.set_defaults(func=_pattern)
    sub.set_defaults(include=False)

    # include
    sub = subparsers.add_parser(
        'include',
        help=_('include files to be backup'))
    sub.add_argument(
        'pattern',
        nargs='+',
        help=_('file pattern to be exclude. may contains `*` or `?` wildcard'))
    sub.set_defaults(func=_pattern)
    sub.set_defaults(include=True)

    # Link
    sub = subparsers.add_parser(
        'link',
        help=_('link this minarca backup with a minarca server'))
    sub.add_argument(
        '-r', '--remoteurl',
        required=True,
        help=_("URL to the remote minarca server. e.g.: http://example.com:8080/"))
    sub.add_argument(
        '-u', '--username',
        required=True,
        help=_("user name to be used for authentication"))
    sub.add_argument(
        '-p', '--password',
        help=_("password to use for authentication. Will prompt if not provided"))
    sub.add_argument(
        '-n', '--name',
        required=True,
        help=_("repository name to be used"))
    sub.add_argument(
        '--force',
        action='store_true',
        help=_("link to remote server even if the repository name already exists"))
    sub.set_defaults(func=_link)

    # patterns
    sub = subparsers.add_parser(
        'patterns',
        help=_('list the includes / excludes patterns'))
    sub.set_defaults(func=_patterns)

    # Stop
    sub = subparsers.add_parser(
        'stop',
        help=_('stop the backup'))
    sub.add_argument(
        '--force',
        action='store_true',
        help=_("doesn't fail if the backup is not running"))
    sub.set_defaults(func=_stop)

    # scheduler
    sub = subparsers.add_parser(
        'schedule',
        help=_('create required schedule task in crontab or Windows Task Scheduler'))
    sub.add_argument(
        '--hourly',
        dest='schedule',
        action='store_const',
        const=Settings.HOURLY,
        help=_("schedule backup to run hourly"))
    sub.add_argument(
        '--daily',
        dest='schedule',
        action='store_const',
        const=Settings.DAILY,
        help=_("schedule backup to run daily"))
    sub.add_argument(
        '--weekly',
        dest='schedule',
        action='store_const',
        const=Settings.WEEKLY,
        help=_("schedule backup to run weekly"))
    sub.set_defaults(func=_schedule)

    # Status
    sub = subparsers.add_parser(
        'status',
        help=_('return the current minarca status'))
    sub.set_defaults(func=_status)

    # unlink
    sub = subparsers.add_parser(
        'unlink',
        help=_('unlink this minarca client from server'))
    sub.set_defaults(func=_unlink)

    # ui
    sub = subparsers.add_parser(
        'ui',
        help=_('open graphical user interface (default when calling minarcaw)'))
    sub.set_defaults(func=_ui)

    # Quick hack to support previous `--backup`, `--stop`
    args = [_ARGS_ALIAS.get(a, a) for a in args]
    return parser.parse_args(args)


def _configure_logging(debug=False):
    """
    Configure logging system. Make stdout quiet when running within a cron job.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Configure log file
    file_handler = logging.handlers.RotatingFileHandler(
        get_log_file(),
        maxBytes=(1048576 * 5),
        backupCount=5)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(process)d][%(levelname)-5.5s][%(threadName)-12.12s] %(message)s"))
    file_handler.setLevel(logging.DEBUG)
    root.addHandler(file_handler)

    # Configure stdout
    # With non_interactive mode, only print error.
    try:
        interactive = sys.stdout and os.isatty(sys.stdout.fileno())
    except Exception:
        interactive = False
    default_level = logging.INFO if interactive else logging.ERROR
    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(logging.Formatter("%(message)s"))
    console.setLevel(logging.DEBUG if debug else default_level)
    root.addHandler(console)


def main(args=None):
    """
    Entry point to start minarca command line interface.
    """
    # Parse the arguments
    if args is None:
        args = sys.argv[1:]
    args = _parse_args(args)
    # Remove func from args
    kwargs = {k: v for k, v in args._get_kwargs() if k not in [
        'func', 'subcommand', 'debug']}
    # Configure logging
    _configure_logging(debug=args.debug)
    # Call appropriate function
    return args.func(**kwargs)


if __name__ == "__main__":
    sys.exit(main())
