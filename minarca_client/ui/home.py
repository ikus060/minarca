import webbrowser

import pkg_resources
import tkvue

import minarca_client.ui.patterns  # noqa
import minarca_client.ui.schedule  # noqa
import minarca_client.ui.settings  # noqa
import minarca_client.ui.status  # noqa
from minarca_client.core import Backup


class HomeDialog(tkvue.Component):
    template = pkg_resources.resource_string('minarca_client.ui', 'templates/home.html')

    def __init__(self, *args, **kwargs):
        self.data = tkvue.Context(
            {
                'active_view': 'home',
            }
        )
        self.backup = Backup()
        super().__init__(*args, **kwargs)
        self.root.tk.eval('tk::PlaceWindow %s center' % (self.root))

    def set_active_view(self, name):
        assert name in ['home', 'patterns', 'schedule', 'settings']
        self.data.active_view = name

    def show_help(self):
        help_url = self.backup.get_help_url()
        webbrowser.open(help_url)
