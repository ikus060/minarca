import asyncio
import os
import tempfile
import unittest

from kivy.base import EventLoop
from kivy.clock import Clock

from minarca_client.core.backup import Backup
from minarca_client.core.compat import IS_LINUX
from minarca_client.ui.app import MinarcaApp

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class BaseAppTest(unittest.IsolatedAsyncioTestCase):
    """Base class to run graphical unit test."""

    ACTIVE_VIEW = None
    ACTIVE_VIEW_KWARGS = {}

    @property
    def view(self):
        return self.app.root.ids.body.children[0]

    def setUp(self):
        # Create a working directory for Minarca data
        self.tmp = tempfile.TemporaryDirectory(prefix='minarca-client-test-')
        os.environ['MINARCA_CONFIG_HOME'] = self.tmp.name
        os.environ['MINARCA_DATA_HOME'] = self.tmp.name
        os.environ['MINARCA_CHECK_LATEST_VERSION'] = 'False'

    def tearDown(self):
        # Clear the temporary working directory
        self.tmp.cleanup()

    async def asyncSetUp(self):
        # Make sure the app is not running.
        self.assertIsNone(MinarcaApp.get_running_app())

        # Starting Minarca application using asyncio.
        self.app = MinarcaApp(backup=Backup())
        self._task = asyncio.create_task(self.app.async_run())
        await self.pump_events()

        # When Browse to create local backup
        if self.ACTIVE_VIEW:
            self.app.set_active_view(self.ACTIVE_VIEW, **self.ACTIVE_VIEW_KWARGS)

        # Need to wait explicitly because of Clock.tick getting called
        await self.pump_events()

    async def asyncTearDown(self):
        # Stop application
        self.app.stop()
        # Destroy windows content
        self.app._clear_widgets_recursive(self.app.root)
        # Let the event loop execute some event
        await asyncio.sleep(0.1)
        # Check if all asyncio task are completed.
        remaining_tasks = [
            task
            for task in asyncio.all_tasks()
            if 'App.async_run' not in str(task._coro) and 'IsolatedAsyncioTestCase' not in str(task._coro)
        ]
        self.assertFalse(remaining_tasks, 'some asyncio task are still running')
        # Unschedule all events
        for event in list(Clock.get_events()):
            Clock.unschedule(event)

    async def pump_events(self):
        """Wait until all scheduled event are processed."""
        # Let the event loop process all existing events
        await asyncio.sleep(0.1)
        # Then wait until all event are processed.
        while not EventLoop.quit:
            remaining_events = [event for event in Clock.get_events() if event.callback]
            if not remaining_events:
                break
            await asyncio.sleep(0.1)
