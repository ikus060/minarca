# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import asyncio
import logging

from kivy.event import EventDispatcher
from kivy.properties import DictProperty, ObjectProperty
from watchfiles import DefaultFilter, awatch

from minarca_client.core import Backup, BackupInstance

logger = logging.getLogger(__name__)


class AbstractViewModel(EventDispatcher):

    def __init__(self, model):
        super().__init__()
        self._model = model

    def __getattr__(self, item):
        # Delegate everything else to the domain object to avoid duplicates
        return getattr(self._model, item)


class BackupViewModel(AbstractViewModel):

    _watch_task: asyncio.Task | None = None

    instances = DictProperty(rebind=True)

    def __init__(self, model):
        assert isinstance(model, Backup)
        super().__init__(model)
        # Initialize list of instances.
        self.rescan()

    def rescan(self):
        # When mtime get updated, let refresh the list of instances
        self._model.rescan()
        src = self._model.instances
        dst = self.instances

        # Remove keys not present in src
        for iid in list(dst.keys() - src.keys()):
            inst = dst.pop(iid, None)
            if inst:
                inst.stop_watching()

        # Add keys that are in src but missing in dst
        for iid in src.keys():
            if iid not in dst.keys():
                dst[iid] = BackupInstanceViewModel(src[iid])
            else:
                dst[iid]._reload_from_model()

    def start_watching(self, debounce_ms=300):
        # prevent double-start
        if self._watch_task and not self._watch_task.done():
            return
        self._watch_task = asyncio.create_task(self._watch(debounce_ms), name='watch-backup-instances')

    def stop_watching(self):
        t = self._watch_task
        self._watch_task = None
        if t and not t.done():
            t.cancel()

    async def _watch(self, debounce_ms):
        """
        Watch all backup instances related files: config & status.
        """
        try:
            async for _changes in awatch(
                self._model._config_home,
                self._model._data_home,
                watch_filter=DefaultFilter(ignore_entity_patterns=['.log$', '.log.[0-9]$']),
                recursive=False,
                debounce=debounce_ms,
            ):
                self.rescan()
        except asyncio.CancelledError:
            pass  # normal shutdown
        except Exception:
            logger.exception("backup watcher crashed")
        finally:
            # make sure the handle is cleared if the loop exits
            if self._watch_task and self._watch_task.done():
                self._watch_task = None

    def configure_remote(self, *args, **kwargs):
        try:
            return self._model.configure_remote(*args, **kwargs)
        finally:
            self.rescan()

    def configure_local(self, *args, **kwargs):
        try:
            return self._model.configure_local(*args, **kwargs)
        finally:
            self.rescan()

    def delete_instance(self, *args, **kwargs):
        try:
            return self._model.delete_instance(*args, **kwargs)
        finally:
            self.rescan()


class BackupInstanceViewModel(AbstractViewModel):

    patterns = ObjectProperty(rebind=True)
    status = ObjectProperty(rebind=True)
    settings = ObjectProperty(rebind=True)

    def __init__(self, model):
        assert isinstance(model, BackupInstance)
        super().__init__(model)
        self._reload_from_model()

    def _reload_from_model(self):
        self._model.load_patterns()
        self._model.load_status()
        self._model.load_settings()
        self.patterns = self._model.patterns
        self.status = self._model.status
        self.settings = self._model.settings

    def stop_watching(self):
        pass
