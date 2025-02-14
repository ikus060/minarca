# Copyright (C) 2024 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Oct 21, 2024

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''

import asyncio
import datetime
import logging
import os

from minarca_client.core.config import Datetime, KeyValueConfigFile
from minarca_client.core.notification import clear_notification, send_notification
from minarca_client.locale import _

logger = logging.getLogger(__name__)

LAST_RESULTS = ['SUCCESS', 'FAILURE', 'RUNNING', 'STALE', 'INTERRUPT']


class Status(KeyValueConfigFile):
    RUNNING_DELAY = 5  # When running status file get updated every 5 seconds.

    _fields = [
        ('details', str, None),
        ('lastdate', lambda x: Datetime(x) if x else None, None),
        ('lastresult', lambda x: x if x in LAST_RESULTS else 'UNKNOWN', 'UNKNOWN'),
        ('lastsuccess', lambda x: Datetime(x) if x else None, None),
        ('pid', int, None),
        ('action', lambda x: x if x in ['backup', 'restore'] else None, None),
        ('lastnotificationid', str, None),
        ('lastnotificationdate', lambda x: Datetime(x) if x else None, None),
    ]

    @property
    def current_status(self):
        """
        Return a backup status. Read data from the status file and make
        interpretation of it.
        """
        import psutil

        now = Datetime()
        # After reading the status file, let determine the real status.
        data = dict(self._data)
        if data.get('lastresult') == 'RUNNING':
            # Get pid and checkif process is running.
            pid = data.get('pid')
            if not pid:
                return 'INTERRUPT'
            try:
                psutil.Process(data.get('pid')).is_running()
            except (ValueError, psutil.NoSuchProcess):
                return 'INTERRUPT'
            # Then let check if the status file was updated within the last 10 seconds.
            lastdate = data.get('lastdate')
            if lastdate and now - lastdate > datetime.timedelta(seconds=self.RUNNING_DELAY * 2):
                return 'STALE'
        # By default return lastresult value.
        return data.get('lastresult')


class UpdateStatus:
    """
    Update the status while the backup is running.
    """

    def __init__(self, instance, action='backup'):
        assert action in ['backup', 'restore']
        self.instance = instance
        self.status = instance.status
        self.action = action
        self.running = False

    def _write_status(self):
        self.status.pid = os.getpid()
        self.status.lastresult = 'RUNNING'
        self.status.lastdate = Datetime()
        self.status.details = ''
        self.status.action = self.action
        self.status.save()

    async def _task(self):
        """Update the status file continiously with new data."""
        while self.running:
            await asyncio.sleep(Status.RUNNING_DELAY - 1)
            self._write_status()

    async def __aenter__(self):
        self.running = True
        # Start the process by writing a file time to the file
        logger.info(f"{self.instance.log_id}: {self.action} START")
        self._write_status()
        self.task = asyncio.create_task(self._task())

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        await self.task
        if exc_type is None:
            logger.info(f"{self.instance.log_id}: {self.action} SUCCESS")
            with self.status as t:
                t.lastresult = 'SUCCESS'
                t.lastsuccess = Datetime()
                t.lastdate = self.status.lastsuccess
                t.details = ''
        else:
            logger.error(f"{self.instance.log_id}: {self.action} FAILED")
            with self.status as t:
                t.lastresult = 'FAILURE'
                t.lastdate = Datetime()
                t.details = str(exc_val)


class UpdateStatusNotification:
    """
    Handle update of notification when backup status is success or fail.
    """

    def __init__(self, instance):
        assert instance
        self.instance = instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        status = self.instance.status
        settings = self.instance.settings
        if exc_type is None:
            # Backup is successful
            # clear previous notification (if any).
            notification_id = status.lastnotificationid
            if notification_id:
                logger.debug(f"{self.instance.id}: clear previous notification %s", notification_id)
                try:
                    clear_notification(notification_id)
                except Exception:
                    pass
                status.lastnotificationid = None
        else:
            # Backup failed
            if self.is_notification_time():
                # show notification if inactivity period is reached.
                previous_id = status.lastnotificationid
                logger.debug(f"{self.instance.id}: create or replace notification: %s", previous_id)
                maxage = settings.maxage
                try:
                    notification_id = send_notification(
                        title=_('Your backup is outdated'),
                        body=_(
                            'Your backup %s is outdated by over %s days. Please plug in your local device and run the backup.'
                        )
                        % (settings.repositoryname, maxage),
                        replace_id=previous_id,
                    )
                    status.lastnotificationid = notification_id
                    status.lastnotificationdate = Datetime()
                except Exception:
                    logger.warning(f"{self.instance.id}: problem while sending new notification", exc_info=1)
        status.save()

    def is_notification_time(self):
        """
        Return true if the application should raise a notification.
        """
        status = self.instance.status
        settings = self.instance.settings
        # Do not notify if max age is not defined.
        if settings.maxage is None or settings.maxage <= 0:
            return False
        # Only notify every 24 hrs.
        if status.lastnotificationdate and Datetime() - status.lastnotificationdate < datetime.timedelta(days=1):
            return False
        # Notify if last backup never occured.
        if status.lastsuccess is None:
            return True
        # Notify if reaching maxage.
        return Datetime() - status.lastsuccess > datetime.timedelta(days=settings.maxage)
