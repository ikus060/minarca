# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging
import webbrowser

import pkg_resources

from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class InstanceRestoreView(tkvue.Component):
    template = pkg_resources.resource_string('minarca_client.ui', 'templates/instance_restore.tkml').decode("utf-8")

    def __init__(self, *args, backup=None, url=None, **kwargs):
        assert backup is not None
        self.backup = backup
        super().__init__(*args, **kwargs)

    def partial_restore(self):
        """
        Redirect user to web interface.
        """
        remote_url = self.instance.get_repo_url()
        webbrowser.open(remote_url)

    def show_full_restore(self):
        """
        Show retorn pattern view.
        """
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('instancerestorepattern://%s' % self.instance.id)
