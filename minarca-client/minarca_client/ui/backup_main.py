import concurrent.futures
import webbrowser

import tkvue

from .backup_connection_local import BackupConnectionLocal  # noqa
from .backup_connection_remote import BackupConnectionRemote  # noqa
from .backup_create import BackupCreate
from .backup_logs import BackupLogs  # noqa
from .backup_patterns import BackupPatterns  # noqa
from .backup_settings import BackupSettings  # noqa
from .dashboard import DashboardView
from .theme_example import ThemeExample


class MainDialog(tkvue.Component):
    template = """<TopLevel geometry="1024x718" title="Minarca Backup" style="default.TFrame">
    <Frame id="header" pack="side:top; fill:x" style="dark.TFrame" padding="20 10 20 10">
        <!-- Header logo -->
        <Label style="light.dark.TLabel" pack="side:left; fill:x;" image="minarca-header-logo" />

        <!-- TODO remove those buttons -->
        <!-- Buttons -->
        <Button text="Dashboard" command="{{_show_dashboard}}" style="white.dark.TLink" pack="side:left"/>
        <Button text="Theme" command="{{_show_theme}}" style="white.dark.TLink" pack="side:left"/>
    </Frame>
</TopLevel>"""

    def __init__(self, *args, backup=None, **kwargs):
        assert backup is not None
        self.backup = backup
        super().__init__(*args, **kwargs)
        self.set_active_view(DashboardView)
        # Configure default executor for asyncio
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix='AsyncioExecutor')
        self.get_event_loop().set_default_executor(executor)
        # Make set_active_view available at top level
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view = self.set_active_view

    @tkvue.command
    def _show_dashboard(self):
        self.set_active_view(DashboardView)

    @tkvue.command
    def _show_theme(self):
        self.set_active_view(ThemeExample)

    def set_active_view(self, view_class, **kwargs):
        """
        Change the current visible view. URL define the location to be displayed as <view-name>://<backup-instance>
        """
        assert view_class
        # Lookup class name
        if isinstance(view_class, str):
            assert view_class in globals(), f'view_class {view_class} not found'
            view_class = globals().get(view_class)
        # Regirect to Create backup if empty.
        if view_class is DashboardView and len(self.backup) <= 0:
            view_class = BackupCreate
        # Forget & Destroy existing children
        _last_view = getattr(self, '_last_view', None)
        if _last_view:
            _last_view.forget()
            self.root.after_idle(_last_view.destroy)
        # Load new view.
        self._last_view = view_class(master=self.root, backup=self.backup, **kwargs)
        self._last_view.pack(fill='both', expand="true")

    def show_help(self):
        help_url = self.backup.get_help_url()
        webbrowser.open(help_url)
