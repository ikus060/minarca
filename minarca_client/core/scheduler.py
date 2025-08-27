# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import datetime
import os
import subprocess
from pathlib import Path

from minarca_client.core.compat import IS_LINUX, IS_MAC, IS_WINDOWS, get_minarca_exe
from minarca_client.locale import _

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

        def _get_task(self):
            # Get reference to the task name and check the executable.
            root_folder = self.scheduler.GetFolder('\\')
            try:
                return root_folder.GetTask('\\' + self.NAME)
            except pywintypes.com_error:  # @UndefinedVariable
                return None

        def exists(self):
            return self._get_task() is not None

        @property
        def run_if_logged_out(self):
            """
            Return the current status of `run_if_logged_out`.
            """
            task_def = self._get_task()
            return task_def and task_def.Definition.Principal.LogonType == TASK_LOGON_PASSWORD

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
                "Keeps your backup application running. If this task is disabled or stopped, "
                "backups will no longer run. This task is created when the application is "
                "linked to a backup server."
            )
            task_def.Settings.Enabled = True
            task_def.Settings.StopIfGoingOnBatteries = False
            task_def.Settings.DisallowStartIfOnBatteries = False
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
                if winerror == -2147024891:
                    # Permissions error when running agent as "Administrator" without admin right.
                    raise PermissionError(
                        _(
                            'A problem prevents the scheduling of backup jobs. Try running the application with Administrator rights.'
                        )
                    )
                elif winerror == -2147023570:
                    # When username or password are invalid, provide a better error message.
                    raise PermissionError(
                        _(
                            'The user account is unknown or the password is incorrect. Be sure to enter your Windows credentials.'
                        )
                    )
                raise OSError(None, win32api.FormatMessage(winerror), None, winerror)

        def delete(self):
            """
            Delete entry from Task Scheduler.

            This operation might required priviledge escalation.
            """
            task = self._get_task()
            if not task:
                # Task doesn't exists
                return
            # Try deleting with current priviledges.
            try:
                root_folder = self.scheduler.GetFolder('\\')
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

    class CrontabScheduler:
        def __init__(self):
            from crontab import CronTab

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
