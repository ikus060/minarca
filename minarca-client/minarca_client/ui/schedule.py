# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging

import pkg_resources
from minarca_client.core import Backup
from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class ScheduleView(tkvue.Component):
    template = pkg_resources.resource_string('minarca_client.ui', 'templates/schedule.html').decode("utf-8")

    def __init__(self, *args, **kwargs):
        self.backup = Backup()
        self.data = tkvue.Context({
            'schedule': self.backup.get_settings('schedule')
        })
        super().__init__(*args, **kwargs)
        self.data.watch('schedule', self.update_schedule)

    def update_schedule(self, value):
        """
        Called to update the frequency.
        """
        self.backup.schedule(schedule=value)
