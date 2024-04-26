# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import concurrent.futures
import logging

from kivy.base import ExceptionHandler, ExceptionManager
from kivy.lang import Builder
from kivy.modules import inspector
from kivymd.app import MDApp

from minarca_client.ui.theme import MinarcaTheme

from .about_menu import AboutMenu  # noqa
from .backup_connection_local import BackupConnectionLocal  # noqa
from .backup_connection_remote import BackupConnectionRemote  # noqa
from .backup_create import BackupCreate
from .backup_logs import BackupLogs  # noqa
from .backup_patterns import BackupPatterns  # noqa
from .backup_restore import BackupRestore  # noqa
from .backup_restore_custom import BackupRestoreCustom  # noqa
from .backup_restore_date import BackupRestoreDate  # noqa
from .backup_restore_full import BackupRestoreFull  # noqa
from .backup_settings import BackupSettings  # noqa
from .dashboard import DashboardView
from .side_pannel import SidePanel  # noqa

logger = logging.getLogger(__name__)

KV = '''
MDScreen:
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: 'vertical'

        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "50dp"
            padding: "21dp", "0dp"
            theme_bg_color: "Custom"
            md_bg_color: self.theme_cls.inverseSurfaceColor

            Image:
                source: "header-logo-30.png"
                size_hint: None, None
                height: "30dp"
                pos_hint: {'center_y': .5}

            Widget:

            MDIconButton:
                icon: "menu" if nav_drawer.state == 'close' else "window-close"
                theme_icon_color: "Custom"
                icon_color: self.theme_cls.inverseOnSurfaceColor
                pos_hint: {'center_y': .5}
                on_release: nav_drawer.set_state("toggle")

        MDNavigationLayout:

            MDScreenManager:

                MDScreen:

                    MDBoxLayout:
                        id: body
                        md_bg_color: self.theme_cls.backgroundColor

            AboutMenu:
                id: nav_drawer
                backup: app.backup

'''


class MinarcaApp(MDApp, ExceptionHandler):

    def __init__(self, *args, backup=None, **kwargs):
        assert backup is not None
        self.backup = backup
        super().__init__(*args, **kwargs)
        self.theme_cls = MinarcaTheme()

    def mainloop(self):
        # Start the main even loop.
        loop = asyncio.get_event_loop()
        # Configure default executor.
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix='AsyncioExecutor')
        loop.set_default_executor(executor)
        # Configure exception handling.
        ExceptionManager.add_handler(self)
        # Start application event loop.
        loop.run_until_complete(self.async_run(async_lib='asyncio'))
        loop.close()

    def build(self):
        # Define default Window size
        self.icon = "minarca-72.png"
        return Builder.load_string(KV)

    def handle_exception(self, exception):
        # Handle the exception globally
        logger.exception('An error occurred')
        # FIXME Optionally, you can display an error message to the user
        # I'm not sure this is working.
        return ExceptionManager.RAISE

    def _install_settings_keys(self, window):
        # Replace settings view by inspector when debug is enabled.
        if logger.isEnabledFor(logging.DEBUG):
            inspector.start(window, self)

    def on_start(self):
        # Show default view.
        self.set_active_view(DashboardView)
        super().on_start()

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
        self._clear_widgets_recursive(self.root.ids.body)
        # Load new view.
        widget = view_class(backup=self.backup, **kwargs)
        self.root.ids.body.add_widget(widget)

    def _clear_widgets_recursive(self, widget):
        """
        Recursively remove all children from given widget.
        """
        remove_widget = widget.remove_widget
        for child in list(widget.children):
            remove_widget(child)
            self._clear_widgets_recursive(child)
