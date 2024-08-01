# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.


import asyncio
import getpass
import logging
import logging.handlers
import os
import signal
import sys
import traceback
from argparse import ArgumentParser
from pathlib import Path

import rdiffbackup.run

from minarca_client import __version__
from minarca_client.core import Backup, InstanceId
from minarca_client.core.compat import IS_WINDOWS, RobustRotatingFileHandler, get_default_repositoryname, get_log_file
from minarca_client.core.config import Pattern, Settings
from minarca_client.core.exceptions import (
    BackupError,
    InstanceNotFoundError,
    NotRunningError,
    NotScheduleError,
    RepositoryNameExistsError,
)
from minarca_client.core.latest import LatestCheck, LatestCheckFailed
from minarca_client.locale import _

_EXIT_BACKUP_FAIL = 1
_EXIT_REPO_EXISTS = 4
_EXIT_NOT_RUNNING = 5
_EXIT_LINK_ERROR = 6
_EXIT_SCHEDULE_ERROR = 7
_EXIT_KIVY_ERROR = 8
_EXIT_RESTORE_FAIL = 9
_EXIT_INTERUPT = 10

_ARGS_ALIAS = {
    '--backup': 'backup',
    '--stop': 'stop',
    '--status': 'status',
}

logger = logging.getLogger(__name__)


def _abort(msg=None):
    print(msg or _('Operation aborted by the user.'))
    sys.exit(1)


def _prompt_yes_no(msg):
    """
    Return True if user answer yes to our question.
    """
    answer = input(msg)
    return answer.lower() in [_("yes"), _("y")]


def _backup(force, instance_id):
    signal.signal(signal.SIGINT, signal.default_int_handler)
    # Check version
    try:
        latest_check = LatestCheck()
        if not latest_check.is_latest():
            logging.info(_('new version %s available') % latest_check.get_latest_version())
    except LatestCheckFailed:
        logging.info(_('fail to check for latest version'))
    backup = Backup()
    try:
        for instance in backup[instance_id]:
            try:
                asyncio.run(instance.backup(force=force))
            except NotScheduleError as e:
                # If one backup is not schedule to run, continue with next backup.
                logging.info(str(e))
    except BackupError as e:
        # Print message to stdout and log file.
        logging.error(str(e))
        sys.exit(_EXIT_BACKUP_FAIL)
    except Exception:
        logging.exception("unexpected error during backup")
        sys.exit(_EXIT_BACKUP_FAIL)


def _forget(instance_id, force=False):
    backup = Backup()
    # Start by listing the backup
    print(_("Backup Instances:"))
    for instance in backup[instance_id]:
        title = instance.settings.repositoryname or _("No name")
        print('* %s' % title)
    if force or _prompt_yes_no(_('Are you sure you want to forget the above backup settings ? (Yes/No): ')):
        for instance in backup[instance_id]:
            instance.forget()


def _link(remoteurl=None, username=None, name=None, force=False, password=None):
    """
    Start the linking process in command line.
    """
    backup = Backup()
    # Prompt remoteurl
    remoteurl = remoteurl or input('remote url (e.g.: https://backup.examples.com): ') or _abort()
    # Prompt username
    username = username or input('username: ') or _abort()
    # Prompt for password if missing.
    password = password or getpass.getpass(_('password or access token: ')) or _abort()
    # Use default repo if not provided
    name = name or get_default_repositoryname()
    # Start linking process.
    try:
        try:
            asyncio.run(
                backup.configure_remote(
                    remoteurl=remoteurl, username=username, password=password, repositoryname=name, force=force
                )
            )
            print(_('Linked successfully'))
        except RepositoryNameExistsError as e:
            print(e.message)
            if _prompt_yes_no(_('Do you want to replace the existing repository ? (Yes/No): ')):
                asyncio.run(
                    backup.configure_remote(
                        remoteurl=remoteurl, username=username, password=password, repositoryname=name, force=True
                    )
                )
                print(_('Linked successfully'))
                return
            sys.exit(_EXIT_REPO_EXISTS)
    except BackupError as e:
        print(e.message)
        sys.exit(_EXIT_LINK_ERROR)
    # If link is success, Schedule job.
    # On windows this step fail for unknown reason with various user priviledge.
    try:
        backup.schedule_job()
    except OSError:
        print(
            _(
                'A problem prevent the automatic scheduling of backup jobs. As a result, your backup tasks cannot be executed as planned.'
            )
        )


def _pattern(include, pattern, instance_id):
    backup = Backup()
    if not backup.is_configured():
        print(_('To update include or exclude pattern, you must configure at least one backup instance.'))
        sys.exit(1)
    try:
        for instance in backup[instance_id]:
            patterns = instance.patterns
            for path in pattern:
                p = Pattern(include, path, None)
                if not p.is_wildcard():
                    # Resolve relative path
                    path = (Path.cwd() / path).resolve()
                    p = Pattern(include, path, None)
                # Add new pattern
                patterns.append(p)
            patterns.save()
    except BackupError as e:
        # Print message to stdout and log file.
        logging.info(str(e))
        sys.exit(_EXIT_BACKUP_FAIL)
    except Exception:
        logging.exception("unexpected error updating patterns")
        sys.exit(_EXIT_BACKUP_FAIL)


def _patterns(instance_id):
    backup = Backup()
    try:
        for instance in backup[instance_id]:
            for p in instance.patterns:
                line = ('+%s' if p.include else '-%s') % p.pattern
                print(line)
    except BackupError as e:
        # Print message to stdout and log file.
        logging.info(str(e))
        sys.exit(_EXIT_BACKUP_FAIL)
    except Exception:
        logging.exception("unexpected error retrieving patterns")
        sys.exit(_EXIT_BACKUP_FAIL)


def _pause(delay, instance_id):
    """
    Pause backup for the given number of hours.
    """
    backup = Backup()
    try:
        for instance in backup[instance_id]:
            instance.pause(delay=delay)
    except BackupError as e:
        # Print message to stdout and log file.
        logging.info(str(e))
        sys.exit(_EXIT_BACKUP_FAIL)
    except Exception:
        logging.exception("unexpected error updating backup config")
        sys.exit(_EXIT_BACKUP_FAIL)


def _rdiff_backup(options):
    """
    Execute rdiff-backup process within minarca.
    """
    try:
        return rdiffbackup.run.main_run(options)
    except Exception:
        # Capture any exception and return exitcode.
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        sys.exit(_EXIT_BACKUP_FAIL)


def _restore(restore_time, force, paths, instance_id, destination):
    signal.signal(signal.SIGINT, signal.default_int_handler)
    assert isinstance(paths, list)
    backup = Backup()

    #
    # Prompt user to define the backup source.
    #
    if instance_id.value is None and len(backup) >= 2:
        print(_('From which backup source do you want to restore data from ?'))
        for instance in backup:
            if instance.is_remote():
                print(
                    '%s - Remote backup `%s` from `%s`'
                    % (instance.id, instance.settings.repositoryname, instance.settings.remoteurl)
                )
            elif instance.is_local():
                print(
                    '%s - Local backup `%s` from `%s`'
                    % (instance.id, instance.settings.repositoryname, instance.settings.localcaption)
                )
        value = input('Enter backup instance id: ') or _abort()
        try:
            instance = backup[value]
        except InstanceNotFoundError:
            _abort(_('Invalid instance id: %s') % instance_id)
    else:
        instances = backup[instance_id]
        if len(instances) == 0:
            _abort(_("Your instance value doesn't matches any backup instances"))
        elif len(instances) >= 2:
            _abort(_("Your instance value matches too many backup instances"))
        instance = instances[0]

    #
    # Prompt user for paths
    #
    if not paths:
        # Prompt user for folder(s) to be restored if not provided on command line.
        paths = []
        for p in instance.patterns:
            if (
                p.include
                and not p.is_wildcard()
                and _prompt_yes_no(_('Do you want to restore %s? (Yes/No): ') % p.pattern)
            ):
                paths.append(p)
    else:
        # Convert specific path to be restored.
        paths = [(Path.cwd() / path).resolve() for path in paths]
    if not paths:
        _abort()

    #
    # Prompt user to confirm restore operation.
    #
    if not force:
        confirm = _prompt_yes_no(
            _(
                'Are you sure you want to proceed with the restore operation? Please note that this will override your current data. (Yes/No): '
            )
        )
        if not confirm:
            _abort()
    # Execute restore operation.
    try:
        asyncio.run(instance.restore(restore_time=restore_time, paths=paths, destination=destination))
    except BackupError as e:
        # Print message to stdout and log file.
        logging.info(str(e))
        sys.exit(_EXIT_RESTORE_FAIL)
    except Exception:
        logging.exception("unexpected error during restore")
        sys.exit(_EXIT_RESTORE_FAIL)


def _stop(force, instance_id):
    backup = Backup()
    try:
        for instance in backup[instance_id]:
            instance.stop()
    except NotRunningError:
        print(_('backup not running'))
        if not force:
            sys.exit(_EXIT_NOT_RUNNING)
    except BackupError as e:
        # Print message to stdout and log file.
        logging.info(str(e))
        sys.exit(_EXIT_BACKUP_FAIL)
    except Exception:
        logging.exception("unexpected error stoping backup")
        sys.exit(_EXIT_BACKUP_FAIL)


def _schedule(schedule, instance_id, username=None, password=None):
    backup = Backup()
    # Define frequency
    for instance in backup[instance_id]:
        instance.settings.schedule = schedule
        instance.settings.save()
    # Make sure to schedule job in OS too.
    run_if_logged_out = (username, password) if username or password else None
    try:
        backup.schedule_job(run_if_logged_out)
    except Exception as e:
        print(str(e))
        sys.exit(_EXIT_SCHEDULE_ERROR)


def _start(force, instance_id):
    signal.signal(signal.SIGINT, signal.default_int_handler)
    backup = Backup()
    # Check if instance_id is valid.
    try:
        list(backup[instance_id])
    except InstanceNotFoundError as e:
        # Print message to stdout and log file.
        logging.info(str(e))
        sys.exit(_EXIT_BACKUP_FAIL)

    # Trigger backup execution.
    backup.start_all(force=force, instance_id=instance_id.value)


def _status(instance_id):
    """
    Return status for each backup.
    """
    backup = Backup()
    try:
        # Test connection for all backup.
        if len(backup):
            print('Verifying connection...')
        entries = []
        for instance in backup[instance_id]:
            status = instance.status
            settings = instance.settings
            try:
                asyncio.run(instance.test_connection())
                connected = True
            except BackupError:
                connected = False
            entries.append((instance, connected))

        # Print result.
        for instance, connected in entries:
            status = instance.status
            settings = instance.settings
            title = _("Backup Instance: %s") % (settings.repositoryname or _("No name"))
            print(title)
            print('=' * len(title))

            print(" * " + _("Identifier:             %s") % instance.id)
            if instance.is_remote():
                print(" * " + _("Remote server:          %s") % settings.remotehost)
            elif instance.is_local():
                print(" * " + _("Local device:           %s") % settings.localcaption)
            print(" * " + _("Connectivity status:    %s") % (_("Connected") if connected else _("Not connected")))
            print(
                " * "
                + _("Last successful backup: %s")
                % (status.lastsuccess.strftime("%Y-%m-%dT%H:%M:%S%z") if status.lastsuccess else _('Never'))
            )
            print(
                " * "
                + _("Last backup date:       %s")
                % (status.lastdate.strftime("%Y-%m-%dT%H:%M:%S%z") if status.lastdate else _('Never'))
            )
            print(" * " + _("Last backup status:     %s") % (status.current_status or _('Never')))
            if status.details:
                print(" * " + _("Details:                %s") % status.details or '')
            if settings.pause_until:
                print(_("Paused until:           %s") % settings.pause_until)

    except BackupError as e:
        # Print message to stdout and log file.
        logging.info(str(e))
        sys.exit(_EXIT_BACKUP_FAIL)
    except Exception:
        logging.exception("unexpected error getting backup status")
        sys.exit(_EXIT_BACKUP_FAIL)


def _ui():
    """
    Entry point to start minarca user interface.
    """
    try:
        from minarca_client.ui.app import MinarcaApp
    except Exception:
        # This is raised by kivy if it can create a window.
        # In that scenario, we still need to display an error message to the user.
        logger.exception('application startup failed')
        from minarca_client.dialogs import error_dialog

        dlg = error_dialog(
            parent=None,
            title=_('Minarca'),
            message=_('Application fail to start'),
            detail=_(
                'If the problem persists, check the logs with your administrator or try reinstalling the application.'
            ),
        )
        asyncio.run(dlg)
        sys.exit(_EXIT_KIVY_ERROR)

    # Start event loop with backup instance.
    backup = Backup()
    app = MinarcaApp(backup=backup)
    app.mainloop()


def _verify(instance_id):
    backup = Backup()
    for instance in backup[instance_id]:
        asyncio.run(instance.verify())


def _parse_args(args):
    parser = ArgumentParser(
        description=_(
            "Minarca manage your computer's backup by linking your computer with a centralized server and running backups on a given schedule."
        ),
        add_help=True,
    )
    # Check if the application should default to GUI mode.
    is_ui = parser.prog in ['minarcaw', 'minarcaw.exe']

    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-d', '--debug', action='store_true')

    #
    # Define subcommands
    #
    subparsers = parser.add_subparsers(dest='subcommand', required=not is_ui, metavar="{command}")
    if is_ui:
        parser.set_defaults(func=_ui)

    # Start
    sub = subparsers.add_parser('start', help=_('start a backup in background mode'))
    sub.add_argument('--force', action='store_true', help=_("force execution of a backup even if it's not time to run"))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Limit backup to the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.set_defaults(func=_start)

    # Backup
    sub = subparsers.add_parser('backup', help=_('start a backup in foreground mode'))
    sub.add_argument('--force', action='store_true', help=_("force execution of a backup even if it's not time to run"))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Limit backup to the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.set_defaults(func=_backup)

    # exclude
    sub = subparsers.add_parser('exclude', help=_('exclude files to be backup'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Add exclude file pattern to the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.add_argument('pattern', nargs='+', help=_('file pattern to be exclude. may contains `*` or `?` wildcard'))
    sub.set_defaults(func=_pattern)
    sub.set_defaults(include=False)

    # include
    sub = subparsers.add_parser('include', help=_('include files to be backup'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Add include file pattern to the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.add_argument('pattern', nargs='+', help=_('file pattern to be exclude. may contains `*` or `?` wildcard'))
    sub.set_defaults(func=_pattern)
    sub.set_defaults(include=True)

    # Link
    sub = subparsers.add_parser('link', help=_('link this minarca backup with a minarca server'))
    sub.add_argument('-r', '--remoteurl', help=_("URL to the remote minarca server. e.g.: http://example.com:8080/"))
    sub.add_argument('-u', '--username', help=_("user name to be used for authentication"))
    sub.add_argument(
        '-p', '--password', help=_("password or access token to use for authentication. Will prompt if not provided")
    )
    sub.add_argument('-n', '--name', help=_("repository name to be used"))
    sub.add_argument(
        '--force', action='store_true', help=_("link to remote server even if the repository name already exists")
    )
    sub.set_defaults(func=_link)

    # patterns
    sub = subparsers.add_parser('patterns', help=_('list the includes / excludes patterns'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Show include and exclude patterns only for the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.set_defaults(func=_patterns)

    # Restore
    sub = subparsers.add_parser('restore', help=_('restore data from backup'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Force usage of a given instance to be used for restore."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.add_argument(
        '--restore-time',
        help=_(
            "Date time to be restored. Could be 'now' to retore the latest backup. Could be an epoch value like '1682367069'. Could be an ISO date format like '2023-02-24T04:11:09-04:00'. Could be an interval like '3D' for 3 days ago."
        ),
    )
    sub.add_argument(
        '--destination',
        help=_("Define alternate location where to restore file or folder instead of restoring them in place"),
    )
    sub.add_argument(
        '--force', action='store_true', help=_("Force execution of restore operation without confirmation from user")
    )
    sub.add_argument('paths', nargs='*', help=_('files and folders to be restore'))
    sub.set_defaults(func=_restore)

    # Stop
    sub = subparsers.add_parser('stop', help=_('stop the backup'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Stop only the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.add_argument('--force', action='store_true', help=_("doesn't fail if the backup is not running"))
    sub.set_defaults(func=_stop)

    # scheduler
    sub = subparsers.add_parser(
        'schedule', help=_('create required schedule task in crontab or Windows Task Scheduler')
    )
    sub.add_argument(
        '--hourly',
        dest='schedule',
        action='store_const',
        const=Settings.HOURLY,
        help=_("schedule backup to run hourly"),
    )
    sub.add_argument(
        '--daily',
        dest='schedule',
        action='store_const',
        const=Settings.DAILY,
        help=_("schedule backup to run daily"),
    )
    sub.add_argument(
        '--weekly',
        dest='schedule',
        action='store_const',
        const=Settings.WEEKLY,
        help=_("schedule backup to run weekly"),
    )
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Configure only the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    if IS_WINDOWS:
        sub.add_argument('-u', '--username', help=_("username required to run task when user is logged out"))
        sub.add_argument('-p', '--password', help=_("password required to run task when user is logged out"))
    sub.set_defaults(func=_schedule, schedule=Settings.DAILY)

    # Status
    sub = subparsers.add_parser('status', help=_('return the current minarca status'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Show status for the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.set_defaults(func=_status)

    # forget
    sub = subparsers.add_parser('forget', aliases=['unlink'], help=_('forget settings of backup'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Forget settings of the given backup instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.add_argument('--force', action='store_true', help=_("Force forget operation without confirmation from user"))
    sub.set_defaults(func=_forget)

    # pause
    sub = subparsers.add_parser(
        'pause',
        help=_('temporarily delay the execution of the backup for the given amount of hours. Default 24 hours.'),
    )
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Pause only the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.add_argument('-d', '--delay', help=_("number of hours"), type=int, default=24)
    sub.add_argument(
        '-c',
        '--clear',
        nargs='?',
        help=_("clear previously set delay"),
        const=0,
        dest='delay',
        action='store',
        default=0,
    )
    sub.set_defaults(func=_pause)

    # verify
    sub = subparsers.add_parser('verify', help=_('verify backup integrity'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Verify backup integrity of the given backup instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.set_defaults(func=_verify)

    # ui
    sub = subparsers.add_parser('ui', help=_('open graphical user interface (default when calling minarcaw)'))
    sub.set_defaults(func=_ui)

    # rdiff-backup
    sub = subparsers.add_parser('rdiff-backup')
    sub.add_argument('options', nargs='*')
    sub.set_defaults(func=_rdiff_backup)

    # Quick hack to support previous `--backup`, `--stop`
    args = [_ARGS_ALIAS.get(a, a) for a in args]
    # Quick hack to accept any arguments for rdiff-backup sub command
    if args and args[0] == 'rdiff-backup':
        args = args.copy()
        args.insert(1, '--')
    return parser.parse_args(args)


def _configure_logging(debug=False):
    """
    Configure logging system. Make stdout quiet when running within a cron job.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.ERROR)
    # Make requests more quiet
    logging.getLogger('requests').setLevel(logging.WARNING)
    # Avoid "Using selector: EpollSelector"
    logging.getLogger('asyncio').setLevel(logging.WARNING)

    #
    # Configure default logging for the whole application. e.g.: minarca.log
    #
    default_file_handler = RobustRotatingFileHandler(get_log_file(), maxBytes=(1048576 * 5), backupCount=5)
    default_file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(process)d][%(levelname)-5.5s][%(threadName)-12.12s] %(message)s")
    )
    default_file_handler.setLevel(logging.DEBUG)
    root.addHandler(default_file_handler)

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
    kwargs = {k: v for k, v in args._get_kwargs() if k not in ['func', 'subcommand', 'debug']}
    # Configure logging
    _configure_logging(debug=args.debug)
    # Call appropriate function
    try:
        return args.func(**kwargs)
    except KeyboardInterrupt:
        print(_('Process interrupt by user.'))
        sys.exit(_EXIT_INTERUPT)


if __name__ == "__main__":
    sys.exit(main())
