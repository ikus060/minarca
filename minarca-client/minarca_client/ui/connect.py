import logging
import threading
import tkinter.messagebox

import pkg_resources
from minarca_client.core import Backup, RepositoryNameExistsError
from minarca_client.core.exceptions import HttpAuthenticationError
from minarca_client.locale import _
from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


def _default_repository_name():
    """
    Return a default value for the repository name.
    """
    try:
        import socket
        hostname = socket.gethostname()
    except Exception:
        import platform
        hostname = platform.node()
    return hostname.split('.')[0]


class SetupDialog(tkvue.Component):
    template = pkg_resources.resource_string('minarca_client.ui', 'templates/setup.html')

    def __init__(self, master=None):
        self.backup = Backup()
        self.data = tkvue.Context({
            'remoteurl': self.backup.get_settings('remoteurl') or '',
            'remoteurl_valid': tkvue.computed(lambda context: context.remoteurl and (context.remoteurl.startswith('http://') or context.remoteurl.startswith('https://'))),
            'username': self.backup.get_settings('username') or '',
            'username_valid': tkvue.computed(lambda context: context.username and 0 < len(context.username)),
            'password': '',
            'password_valid': tkvue.computed(lambda context: context.password and 0 < len(context.password)),
            'repository_name': _default_repository_name(),
            'repository_name_valid': tkvue.computed(lambda context: context.repository_name and 0 < len(context.repository_name)),
            'valid_form': tkvue.computed(lambda context: context.remoteurl_valid and context.username_valid and context.password_valid and context.repository_name_valid),
            'help_message': tkvue.computed(lambda context: SetupDialog._validate_form(context)),
            'linking': False,  # True during linking process
            'minarca_image_path': pkg_resources.resource_filename('minarca_client.ui', 'images/minarca_128.png'),
            'animated_gif_path': pkg_resources.resource_filename('minarca_client.ui', 'images/spin_32.gif')
        })
        super().__init__(master=master)
        # Bind a couple of event form multi thread processing.
        self.root.bind('<<prompt_link_force>>', self._prompt_link_force)
        cmd = self.root.register(self._show_warning)
        self.root.bind('<<show_warning>>', cmd + " %d")
        self.root.bind('<<close>>', self.close)

    def link(self, force=False):
        self.data.linking = True
        # Start background thread.
        self._thread = threading.Thread(
            target=self._link,
            daemon=True,
            kwargs={'force': force}
        ).start()

    def _link(self, force):
        """
        This function should be called in a separate thread to avoid blocking the UI.
        """
        try:
            self.backup.link(
                remoteurl=self.data.remoteurl,
                username=self.data.username,
                password=self.data.password,
                repository_name=self.data.repository_name,
                force=force)
            # Link completed - Close Window.
            self.root.event_generate('<<close>>')
        except RepositoryNameExistsError:
            logger.info('repository name `%s` already exists' %
                        self.data.repository_name)
            self.root.event_generate('<<prompt_link_force>>')
        except (HttpAuthenticationError) as e:
            logger.exception('authentication failed')
            self._event_generate_show_warning(
                title=_('Invalid connection information !'),
                message=_('Invalid connection information !'),
                detail=_("The information you have entered for the connection to Minarca are invalid.\n\n%s" % str(e)))
        except Exception as e:
            logger.exception('fail to connect')
            self._event_generate_show_warning(
                title=_('Failed to connect to remote server'),
                message=_('Failed to connect to remote server'),
                detail=_("An error occurred during the connection to Minarca "
                         "server.\n\nDetails: %s" % str(e)))

    def close(self, event=None):
        """
        Close this window.
        """
        self.data.linking = False
        self.root.destroy()

    def _prompt_link_force(self, event):
        button_idx = tkinter.messagebox.askyesno(
            master=self.root,
            icon='question',
            title=_('Repository name already exists'),
            message=_('Do you want to replace the existing repository ?'),
            detail=_("The repository name you have entered already exists on "
                     "the remote server. If you continue with this repository, "
                     "you will replace it's content using this computer. "
                     "Otherwise, you must enter a different repository name.")
        )
        if not button_idx:
            # Operation cancel by user
            self.data.linking = False
            return
        self._link(force=True)

    def _event_generate_show_warning(self, title, message, detail):
        self.root.event_generate(
            '<<show_warning>>',
            data={'title': title, 'message': message, 'detail': detail})

    def _show_warning(self, event_data):
        self.data.linking = False
        event_data = eval(event_data)
        tkinter.messagebox.showwarning(
            master=self.root,
            icon='warning',
            **event_data
        )
