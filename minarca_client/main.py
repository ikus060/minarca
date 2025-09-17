# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import argparse
import asyncio
import logging
import logging.handlers
import os
import signal
import sys
import traceback
from pathlib import Path

from minarca_client import __version__
from minarca_client.core import Backup, InstanceId
from minarca_client.core.appconfig import appconfig
from minarca_client.core.compat import (
    IS_MAC,
    IS_WINDOWS,
    RobustRotatingFileHandler,
    get_default_repositoryname,
    get_log_file,
    nice,
)
from minarca_client.core.exceptions import (
    BackupError,
    InstanceNotFoundError,
    KivyError,
    NotConfiguredError,
    NotRunningError,
    NotScheduleError,
    RepositoryNameExistsError,
    RunningError,
)
from minarca_client.core.settings import Settings
from minarca_client.locale import _

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
    from minarca_client.core.latest import LatestCheck, LatestCheckFailed

    signal.signal(signal.SIGINT, signal.default_int_handler)
    # Check version
    try:
        latest_check = LatestCheck()
        if not latest_check.is_latest():
            logging.info(_('new version %s available'), latest_check.get_latest_version())
    except LatestCheckFailed:
        logging.info(_('fail to check for latest version'))
    backup = Backup()
    for instance in backup[instance_id]:
        try:
            asyncio.run(instance.backup(force=force))
        except NotScheduleError as e:
            # If one backup is not schedule to run, continue with next backup.
            logging.info("%s: %s", instance.log_id, e)


def _forget(instance_id, force=False):
    backup = Backup()
    # Start by listing the backup
    print(_("Backup Instances:"))
    for instance in backup[instance_id]:
        title = instance.settings.repositoryname or _("No name")
        print('* %s' % title)
    if force or _prompt_yes_no(_('Are you sure you want to forget the above backup settings? (Yes/No): ')):
        for instance in backup[instance_id]:
            instance.forget()


def _configure(
    remoteurl=None, username=None, name=None, force=False, purge_destination=False, password=None, localdest=None
):
    """
    Start the configuration process in command line.
    """
    import functools
    import getpass

    from minarca_client.core.disk import get_location_info

    backup = Backup()

    # Prompt destination type
    if remoteurl:
        is_local = False
    elif localdest:
        is_local = True
    else:
        is_local = (
            _prompt_yes_no(_('Do you want to backup to a local device (external disk or network share)? (Yes/No): '))
            or _abort()
        )

    if is_local:
        # Prompt destination
        localdest = localdest or input(_('Enter the local destination path: ')) or _abort()
        location = get_location_info(Path(localdest))

        # Use default repo if not provided
        name = name or get_default_repositoryname()

        # Create the minarca structure if required
        if location.is_mountpoint:
            path = location.mountpoint / "minarca" / name
            path.mkdir(parents=1, exist_ok=1)
        else:
            path = location.mountpoint / location.relpath
        configure_func = functools.partial(
            backup.configure_local,
            path=path,
            repositoryname=name,
            force=force,
            purge_destination=purge_destination,
        )
    else:
        # Prompt remoteurl
        remoteurl = remoteurl or input(_('Remote URL (e.g.: https://backup.examples.com): ')) or _abort()
        # Prompt username
        username = username or input(_('Username: ')) or _abort()
        # Prompt for password if missing.
        password = password or getpass.getpass(_('Password or access token: ')) or _abort()
        # Use default repo if not provided
        name = name or get_default_repositoryname()

        configure_func = functools.partial(
            backup.configure_remote,
            remoteurl=remoteurl,
            username=username,
            password=password,
            repositoryname=name,
            force=force,
        )

    # Start linking process.
    try:
        asyncio.run(configure_func())
        print(_('Linked successfully'))
    except RepositoryNameExistsError as e:
        print(str(e))
        if _prompt_yes_no(_('Do you want to replace the existing repository? (Yes/No): ')):
            asyncio.run(configure_func(force=True))
            print(_('Linked successfully'))
        else:
            sys.exit(e.error_code)

    # If link is success, Schedule job.
    # On windows this step fail for unknown reason with various user priviledge.
    backup.schedule_job()


def _pattern(include, pattern, instance_id):
    from minarca_client.core.pattern import Pattern

    backup = Backup()
    if not backup.is_configured():
        print(_('To update include or exclude patterns, you must configure at least one backup instance.'))
        sys.exit(NotConfiguredError.error_code)
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


def _patterns(instance_id):
    backup = Backup()
    for instance in backup[instance_id]:
        for p in instance.patterns:
            line = ('+%s' if p.include else '-%s') % p.pattern
            print(line)


def _pause(delay, instance_id):
    """
    Pause backup for the given number of hours.
    """
    backup = Backup()
    for instance in backup[instance_id]:
        instance.pause(delay=delay)


def _rdiff_backup(args):
    """
    Execute rdiff-backup process within minarca.
    """
    import rdiffbackup.run

    # Write directly to stdout to check for error.
    try:
        version = rdiffbackup.run.Globals.version
        print(f'rdiff-backup {version}', flush=True)
    except IOError:
        # Broken pipe error
        sys.exit(141)
    # Set the priority to below normal
    nice()
    # Start the backup process
    try:
        return rdiffbackup.run.main_run(args)
    except Exception:
        # Capture any exception and return exitcode.
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        sys.exit(BackupError.error_code)


_rdiff_backup.configure_log = False


def _imap_backup(args):
    from minarca_client.core.imap_backup import main_run

    # Set the priority to below normal
    nice()
    # Start the IMAP backup.
    try:
        return main_run(args)
    except Exception:
        # Capture any exception and return exitcode.
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        sys.exit(BackupError.error_code)


_imap_backup.configure_log = False


def _restore(restore_time, force, paths, instance_id, destination):
    signal.signal(signal.SIGINT, signal.default_int_handler)
    assert isinstance(paths, list)
    backup = Backup()

    #
    # Prompt user to define the backup source.
    #
    if instance_id.value is None and len(backup) >= 2:
        print(_('From which backup source do you want to restore data from?'))
        for instance in backup:
            if instance.is_remote():
                print(
                    '%s - Online Backup `%s` from `%s`'
                    % (instance.id, instance.settings.repositoryname, instance.settings.remoteurl)
                )
            elif instance.is_local():
                print(
                    '%s - Local backup `%s` from `%s`'
                    % (instance.id, instance.settings.repositoryname, instance.settings.localcaption)
                )
        value = input(_('Enter backup instance ID: ')) or _abort()
        try:
            instance = backup[value]
        except InstanceNotFoundError:
            _abort(_('Invalid instance ID: %s') % instance_id)
    else:
        instances = backup[instance_id]
        if len(instances) == 0:
            _abort(_("Your instance value doesn't match any backup instances"))
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
                paths.append(p.pattern)
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
    asyncio.run(instance.restore(restore_time=restore_time, paths=paths, destination=destination))


def _stop(force, instance_id):
    backup = Backup()
    try:
        for instance in backup[instance_id]:
            instance.stop()
    except NotRunningError as e:
        logger.warning(str(e))
        if not force:
            sys.exit(e.error_code)


def _schedule(schedule, instance_id, username=None, password=None):
    backup = Backup()
    # Define frequency
    for instance in backup[instance_id]:
        instance.settings.schedule = schedule
        instance.settings.save()
    # Make sure to schedule job in OS too.
    run_if_logged_out = (username, password) if username or password else None
    backup.schedule_job(run_if_logged_out)


def _start(force, instance_id):
    signal.signal(signal.SIGINT, signal.default_int_handler)
    backup = Backup()

    # Check if instance_id is valid.
    list(backup[instance_id])

    # Trigger backup execution.
    backup.start_all(force=force, instance_id=instance_id.value)


def _status(instance_id):
    """
    Return status for each backup.
    """
    backup = Backup()
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
            + _("Last successful backup: %s") % (status.lastsuccess.strftime() if status.lastsuccess else _('Never'))
        )
        print(" * " + _("Last backup date:       %s") % (status.lastdate.strftime() if status.lastdate else _('Never')))
        print(" * " + _("Last backup status:     %s") % (status.current_status or _('Never')))
        if status.details:
            print(" * " + _("Details:                %s") % status.details or '')
        if settings.pause_until:
            print(_("Paused until:           %s") % settings.pause_until.strftime())


def _ui(test=False):
    """
    Entry point to start minarca user interface.
    """
    try:
        from minarca_client.ui.app import MinarcaApp
    except KivyError | Exception:
        # This is raised by kivy if it can create a window.
        # In that scenario, we still need to display an error message to the user.
        logger.exception('application startup failed')
        from minarca_client.dialogs import error_dialog

        if not test:
            dlg = error_dialog(
                parent=None,
                title=appconfig.header_name,
                message=_('Application failed to start'),
                detail=_(
                    'If the problem persists, check the logs with your administrator or try reinstalling the application.'
                ),
            )
            asyncio.run(dlg)
        sys.exit(KivyError.error_code)

    # Start event loop with backup instance.
    backup = Backup()
    app = MinarcaApp(backup=backup, test=test)
    app.mainloop()


def _verify(instance_id):
    backup = Backup()
    for instance in backup[instance_id]:
        asyncio.run(instance.verify())


def _parse_args():
    parser = argparse.ArgumentParser(
        prog='minarca',
        description=_(
            "Manages your computer's backup by linking your computer with a centralized server and running backups on a given schedule."
        ),
        add_help=True,
    )
    # Check if the application should default to GUI mode.
    is_ui = os.path.basename(sys.executable) in ['minarcaw', 'minarcaw.exe']

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
    sub = subparsers.add_parser('exclude', help=_('exclude files from being backed up'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Add exclude file pattern to the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.add_argument('pattern', nargs='+', help=_('file pattern to be excluded. May contain `*` or `?` wildcard'))
    sub.set_defaults(func=_pattern)
    sub.set_defaults(include=False)

    # include
    sub = subparsers.add_parser('include', help=_('include files to be backed up'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Add include file pattern to the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.add_argument('pattern', nargs='+', help=_('file pattern to be excluded. May contain `*` or `?` wildcard'))
    sub.set_defaults(func=_pattern)
    sub.set_defaults(include=True)

    # configure
    sub = subparsers.add_parser(
        'configure', aliases=['link'], help=_('configure this agent to backup to a new destination (remote or local)')
    )
    sub.add_argument('-r', '--remoteurl', help=_("URL to the remote server. e.g.: http://example.com:8080/"))
    sub.add_argument('-u', '--username', help=_("username to be used for authentication with the remote server"))
    sub.add_argument(
        '-p',
        '--password',
        help=_("password or access token to use for authentication. You will be prompted if not provided"),
    )
    sub.add_argument('-n', '--name', help=_("repository name to be used"))
    sub.add_argument(
        '--force',
        action='store_true',
        help=_("replace existing repository on backup destination if it exists without confirmation"),
    )
    sub.add_argument(
        '--purge-destination',
        action='store_true',
        help=_("delete all contents of destination, then initialize/configure it -- only work for local destination"),
    )
    sub.add_argument('-d', '--localdest', help=_('path to local destination'))
    sub.set_defaults(func=_configure)

    # patterns
    sub = subparsers.add_parser('patterns', help=_('list the include/exclude patterns'))
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
        help=_("Force the use of a given instance for restore."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.add_argument(
        '--restore-time',
        help=_(
            "Date and time to be restored. Could be 'now' to restore the latest backup. Could be an epoch value like '1682367069'. Could be an ISO date format like '2023-02-24T04:11:09-04:00'. Could be an interval like '3D' for 3 days ago."
        ),
    )
    sub.add_argument(
        '--destination',
        help=_("Define an alternate location to restore files or folders instead of restoring them in place."),
    )
    sub.add_argument(
        '--force',
        action='store_true',
        help=_("Force execution of restore operation without confirmation from the user."),
    )
    sub.add_argument('paths', nargs='*', help=_('files and folders to be restored'))
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
    sub.add_argument('--force', action='store_true', help=_("doesn't fail if the backup is not running."))
    sub.set_defaults(func=_stop)

    # scheduler
    if IS_WINDOWS:
        help_msg = _('create the required scheduled task in Windows Task Scheduler')
    elif IS_MAC:
        help_msg = _('create the required scheduled task in launchd')
    else:
        help_msg = _('create the required scheduled task in crontab')
    sub = subparsers.add_parser('schedule', help=help_msg)
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
        sub.add_argument('-u', '--username', help=_("username required to run task when the user is logged out"))
        sub.add_argument('-p', '--password', help=_("password required to run task when the user is logged out"))
    sub.set_defaults(func=_schedule, schedule=Settings.DAILY)

    # Status
    sub = subparsers.add_parser('status', help=_('return the current backup status'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Show status for the given instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.set_defaults(func=_status)

    # forget
    sub = subparsers.add_parser('forget', aliases=['unlink'], help=_('forget backup settings'))
    sub.add_argument(
        '--instance',
        dest='instance_id',
        help=_("Forget settings of the given backup instance(s)."),
        default=InstanceId(None),
        type=InstanceId,
    )
    sub.add_argument(
        '--force', action='store_true', help=_("Force forget operation without confirmation from the user.")
    )
    sub.set_defaults(func=_forget)

    # pause
    sub = subparsers.add_parser(
        'pause',
        help=_('temporarily delay the execution of the backup for the given number of hours. Default is 24 hours.'),
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
    # ui --test use to test the GUI in CICD.
    sub.add_argument('--test', help=argparse.SUPPRESS, action='store_true')

    # rdiff-backup
    sub = subparsers.add_parser('rdiff-backup', help=_('For internal use'))
    sub.add_argument('args', nargs='*')
    sub.set_defaults(func=_rdiff_backup)

    # imap-backup
    sub = subparsers.add_parser('imap-backup', help=_('For internal use'))
    sub.add_argument('args', nargs='*')
    sub.set_defaults(func=_imap_backup)

    return parser


def _configure_logging(debug=False):
    """
    Configure logging system.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    # Make requests more quiet
    logging.getLogger('requests').setLevel(logging.WARNING)
    # Avoid "Using selector: EpollSelector"
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    # Avoid kivy logs by default.
    logging.getLogger('kivy').setLevel(logging.DEBUG if debug else logging.WARNING)
    # Capture warning
    logging.captureWarnings(True)
    #
    # Configure default logging for the whole application. e.g.: minarca.log
    #
    default_file_handler = RobustRotatingFileHandler(get_log_file(), maxBytes=(1048576 * 5), backupCount=5)
    default_file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(process)d][%(levelname)-8s][%(threadName)-12.12s] %(message)s")
    )
    default_file_handler.setLevel(logging.DEBUG)
    root.addHandler(default_file_handler)

    # Make stdout very-quiet when running as cron job (or any non-interactive stdout).
    # Unless the --debug flag is used.
    try:
        interactive = sys.stdout and sys.stdout.isatty()
    except Exception:
        interactive = False
    if debug:
        console_level = logging.DEBUG
    elif interactive:
        console_level = logging.INFO
    else:
        console_level = logging.ERROR
    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(logging.Formatter("%(message)s"))
    console.setLevel(console_level)
    root.addHandler(console)


def main(args=None):
    """
    Entry point to start minarca command line interface.
    """
    # Parse the arguments
    if args is None:
        args = sys.argv[1:]

    # Parse arguments
    parser = _parse_args()
    # Quick hack to support previous `--backup`, `--stop`
    args = [_ARGS_ALIAS.get(a, a) for a in args]
    # Quick hack to accept any arguments for rdiff-backup sub command
    if args and args[0] in ['rdiff-backup', 'imap-backup']:
        args = args.copy()
        args.insert(1, '--')
    args = parser.parse_args(args)

    # Remove func from args
    kwargs = {k: v for k, v in args._get_kwargs() if k not in ['func', 'subcommand', 'debug']}
    # Configure logging if required.
    if getattr(args.func, 'configure_log', True):
        _configure_logging(debug=args.debug)
    try:
        # Call appropriate function
        return args.func(**kwargs)
    except RunningError as e:
        # Print warning message is already running.
        logging.error(e.message)
        if e.detail:
            logging.error(e.detail)
        sys.exit(e.error_code)
    except BackupError as e:
        # Print message to stdout and log file.
        logging.error(e.message)
        if e.detail:
            logging.error(e.detail)
        sys.exit(e.error_code)
    except Exception:
        logging.exception("unexpected error retrieving patterns")
        sys.exit(BackupError.error_code)


if __name__ == "__main__":
    sys.exit(main())
