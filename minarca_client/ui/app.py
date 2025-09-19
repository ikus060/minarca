# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import concurrent.futures
import importlib
import logging

from kivy.base import ExceptionHandler, ExceptionManager
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.modules import inspector
from kivy.properties import StringProperty
from kivymd.app import MDApp

from minarca_client.core.appconfig import appconfig
from minarca_client.dialogs import error_dialog
from minarca_client.locale import _
from minarca_client.ui.theme import Theme

from .about_menu import AboutMenu  # noqa
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
                source: app.header_logo
                fit_mode: "contain"
                size_hint: None, None
                height: "32dp"
                width: self.height * self.image_ratio
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

    header_logo = StringProperty(str(appconfig.header_logo))

    icon = StringProperty(str(appconfig.favicon))

    title = StringProperty(appconfig.header_name)

    use_kivy_settings = False

    def __init__(self, *args, backup=None, test=False, **kwargs):
        assert backup is not None
        self.backup = backup
        self.test = test
        super().__init__(*args, **kwargs)
        self.theme_cls = Theme()

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

    def load_kv(self, filename=None):
        """Disable default '*.kv' loading"""
        pass

    def load_config(self):
        """Disable default config load."""
        pass

    def build(self):
        return Builder.load_string(KV)

    async def async_handle_exception(self, window, exception):
        await error_dialog(
            parent=window,
            title=_('Unhandled Exception Detected'),
            message=_('The application encountered an unexpected error and needs to close.'),
            detail=_(
                'Please check the logs for more information. If this problem '
                'occurs again, report it to support.\n\n'
                'Details: %s\n\n'
                'The application will now quit.'
            )
            % str(exception),
        )
        self.stop()

    def handle_exception(self, exception):
        # Handle the exception globally
        logger.exception('an error occurred')
        # If window still open, display an error.
        if self._app_window:
            asyncio.create_task(self.async_handle_exception(self._app_window, exception))
            return ExceptionManager.PASS
        else:
            return ExceptionManager.RAISE

    def _install_settings_keys(self, window):
        # Replace settings view by inspector when debug is enabled.
        if logging.getLogger('kivy').isEnabledFor(logging.DEBUG):
            inspector.start(window, self)

    def on_start(self):
        # Show default view.
        self.set_active_view('dashboard.DashboardView')
        # If testing, application close after 2 sec.
        if self.test:
            Clock.schedule_once(self.stop, 1)

    def _find_class(self, view_class):
        """
        Load reference to the class.
        """
        module_name, class_name = view_class.rsplit('.', 1)
        module = importlib.import_module('minarca_client.ui.' + module_name)
        return getattr(module, class_name)

    def set_active_view(self, view_class, **kwargs):
        """
        Change the current visible view. URL define the location to be displayed as <view-name>://<backup-instance>
        """
        assert isinstance(view_class, str)
        assert '.' in view_class
        # Regirect to Create backup if empty.
        if view_class == 'dashboard.DashboardView' and len(self.backup) <= 0:
            view_class = 'backup_create.BackupCreate'
        class_ref = self._find_class(view_class)

        # Forget & Destroy existing children
        self._clear_widgets_recursive(self.root.ids.body)
        # Since KivyMD is not taking care to cancel ClockEvent when widget get removed,
        # Here we take the time to delete them.
        for event in Clock.get_events():
            if not event.loop and event.timeout > 0:
                event.cancel()
        # Load new view.
        widget = class_ref(backup=self.backup, **kwargs)
        self.root.ids.body.add_widget(widget)

    def _clear_widgets_recursive(self, widget):
        """
        Recursively remove all children from given widget.
        """
        remove_widget = widget.remove_widget
        for child in list(widget.children):
            remove_widget(child)
            self._clear_widgets_recursive(child)
