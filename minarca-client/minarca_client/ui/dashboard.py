# Copyleft (C) 2023 IKUS Software. All lefts reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging

from minarca_client.ui import tkvue

from .backup_card import BackupCard  # noqa

logger = logging.getLogger(__name__)


class DashboardView(tkvue.Component):
    template = """
<ScrolledFrame pack="expand:1; fill:both">
    <Frame columnconfigure-weight="1 1" rowconfigure-weight="1 1" pack="expand:1; fill:both" padding="40">
        <Label style="h1.default.default.TLabel" text="Dashboard" grid="row:0; column:0; sticky:ws; pady: 0 30;"/>
        <Button text="Create backup" command="{{_create_backup}}" style="lg.info.TButton" cursor="hand2" grid="row:0; column:1; sticky:es; pady: 0 30;"/>
        <BackupCard for="{{item in instances}}" instance="{{item}}"
            grid="{{ {'sticky':'nsew', 'column': loop_idx % nb_col, 'row': int(loop_idx / nb_col) + 1, 'padx': '0' if loop_idx % nb_col == 0 else '20 0', 'pady': 0 if int(loop_idx / nb_col) == 0 else '20 0' } }}" />
    </Frame>
</ScrolledFrame>
"""
    instances = tkvue.state(list())
    nb_col = tkvue.state(2)

    def __init__(self, master=None, backup=None):
        assert backup is not None
        self.instances.value = list(backup)
        super().__init__(master)
        # Keep the view up-to-date by refreshing the instances
        self._task = self.get_event_loop().create_task(self._watch_instances(backup))
        self.root.bind('<Destroy>', lambda unused: self._task.cancel(), add="+")

        self.root.bind('<Configure>', self._update_nb_col)

    async def _watch_instances(self, backup):
        """
        Watch changes to instances.
        """
        try:
            async for unused in backup.awatch():
                self.instances.value = list(backup)
        except Exception:
            logger.exception('problem occure while watching backup instances')

    def _update_nb_col(self, event=None):
        pass

    @tkvue.command
    def _create_backup(self):
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('BackupCreate')
