# Copyleft (C) 2023 IKUS Software. All lefts reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging

from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class BackupCreate(tkvue.Component):
    template = """
<ScrolledFrame pack="expand:1; fill:both">
    <Frame padding="40 40 40 40" columnconfigure-weight="2 1 1 2" pack="expand:1; fill:both">
        <Label style="h1.default.default.TLabel" text="Create a backup" grid="row:0; column:0; columnspan:4; pady:0 58;" visible="{{ backup_count==0 }}"/>
        <Label style="h1.default.default.TLabel" text="Create a backup" grid="row:0; column:0; columnspan:2; pady:0 58; sticky:nw" visible="{{ backup_count>0 }}"/>
        <Button text="Back" command="{{go_back}}" style="default.TButton" cursor="hand2" grid="row:0; column:2; columnspan:2; sticky:ne" visible="{{ backup_count>0 }}"/>

        <!-- Remote -->
        <Frame style="white.TLabelframe" padding="40" grid="row:1; column:1; padx:0 15; sticky:nsew">
            <Label image="remote-backup-logo-128" style="white.TLabel" />
            <Label text="Remote backup" style="h2.info.white.TLabel" pack="pady:32 24" />
            <Separator pack="fill:x"/>
            <Label text="Accessible online" style="white.TLabel" pack="pady:8" />
            <Separator pack="fill:x"/>
            <Label text="Centralized management" style="white.TLabel" pack="pady:8"/>
            <Separator pack="fill:x"/>
            <Label text="Offsite backup" style="white.TLabel" pack="pady:8" />
            <Separator pack="fill:x"/>
            <Button text="Create" style="info.TButton" command="{{ _create_remote }}" pack="pady:30 0" cursor="hand2"/>
        </Frame>

        <!-- Local -->
        <Frame style="white.TLabelframe" padding="40" grid="row:1; column:2; padx:15 0; sticky:nsew">
            <Label image="local-backup-logo-128" style="white.TLabel" />
            <Label text="Local backup" style="h2.info.white.TLabel" pack="pady:32 24"/>
            <Separator pack="fill:x"//>
            <Label text="Offline Accessibility" style="white.TLabel" pack="pady:8" />
            <Separator pack="fill:x"//>
            <Label text="Cost Savings" style="white.TLabel" pack="pady:8"/>
            <Separator pack="fill:x"//>
            <Label text="Back on External Disk" style="white.TLabel" pack="pady:8" />
            <Separator pack="fill:x"/>
            <Button text="Create" style="info.TButton" command="{{ _create_local }}" pack="pady:30 0" cursor="hand2"/>
        </Frame>
    </Frame>
</ScrolledFrame>
"""
    backup_count = tkvue.state(0)

    def __init__(self, master=None, backup=None):
        assert backup is not None
        self.backup_count.value = len(backup)
        super().__init__(master)

    @tkvue.command
    def _create_remote(self):
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('BackupConnectionRemote', create=True)

    @tkvue.command
    def _create_local(self):
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('BackupConnectionLocal', create=True)

    @tkvue.command
    def go_back(self):
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('DashboardView')
