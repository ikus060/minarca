# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import concurrent.futures
import logging

# Define kivy configuration manually
from kivy.config import Config  # noqa

Config.set('kivy', 'exit_on_escape', 0)

from kivy.base import ExceptionHandler, ExceptionManager
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.modules import inspector
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp

from minarca_client.ui.theme import MinarcaTheme

from .backup_connection_local import BackupConnectionLocal  # noqa
from .backup_connection_remote import BackupConnectionRemote  # noqa
from .backup_create import BackupCreate
from .backup_logs import BackupLogs  # noqa
from .backup_patterns import BackupPatterns  # noqa
from .backup_restore import BackupRestore  # noqa
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
            md_bg_color: app.dark

            Image:
                source: "header-logo-30.png"
                size_hint: None, None
                height: "30dp"
                pos_hint: {'center_y': .5}

            Widget:

            MDIcon:
                icon: "menu"
                theme_icon_color: "Custom"
                icon_color: "#ffffff"
                pos_hint: {'center_y': .5}

        MDBoxLayout:
            id: body
            md_bg_color: self.theme_cls.backgroundColor
'''


class MinarcaApp(MDApp, ExceptionHandler):
    def __init__(self, *args, backup=None, **kwargs):
        assert backup is not None
        self.backup = backup
        super().__init__(*args, **kwargs)
        self.theme_cls = MinarcaTheme()

    def mainloop(self):
        # FIXME Investigate alternative and make use of trio ?
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
        # FIXME We should remove those color and use theme_cls.
        # Define all custom color here.
        self.primary = get_color_from_hex("#009FB9")
        self.dark = get_color_from_hex("#0E2933")
        self.white = get_color_from_hex("#ffffff")
        self.gray_10 = get_color_from_hex("#EEF0F1")
        self.gray_20 = get_color_from_hex("#CFD4D6")
        self.gray_50 = get_color_from_hex("#7E8D92")
        self.danger = get_color_from_hex("#CA393C")
        self.secondary = get_color_from_hex("#B6DDE2")
        self.secondary_50 = get_color_from_hex("#DBEEF0")
        self.warning = get_color_from_hex("#D88C46")
        self.warning_20 = get_color_from_hex("#FFF0D9")

        # Define application icon
        self.icon = "minarca.ico"
        # Define default Window size
        Window.size = (1024, 768)
        inspector.start(Window, self)
        return Builder.load_string(KV)

    def handle_exception(self, exception):
        # Handle the exception globally
        logger.exception('An error occurred')
        # FIXME Optionally, you can display an error message to the user
        # I'm not sure this is working.
        return ExceptionManager.RAISE

    def _install_settings_keys(self, window):
        # Do nothing to avoid creating settings view.
        pass

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
