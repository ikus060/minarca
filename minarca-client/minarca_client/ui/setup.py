import functools
import logging
import tkinter.messagebox

import pkg_resources

from minarca_client.core import Backup
from minarca_client.core.exceptions import (
    HttpAuthenticationError,
    HttpConnectionError,
    HttpInvalidUrlError,
    RepositoryNameExistsError,
    SshConnectionError,
)
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
        self.data = tkvue.Context(
            {
                'remoteurl': self.backup.get_settings('remoteurl') or '',
                'remoteurl_valid': tkvue.computed(lambda context: context.remoteurl and 0 < len(context.remoteurl)),
                'username': self.backup.get_settings('username') or '',
                'username_valid': tkvue.computed(lambda context: context.username and 0 < len(context.username)),
                'password': '',
                'password_valid': tkvue.computed(lambda context: context.password and 0 < len(context.password)),
                'repository_name': _default_repository_name(),
                'repository_name_valid': tkvue.computed(
                    lambda context: context.repository_name and 0 < len(context.repository_name)
                ),
                'valid_form': tkvue.computed(
                    lambda context: context.remoteurl_valid
                    and context.username_valid
                    and context.password_valid
                    and context.repository_name_valid
                ),
                'help_message': tkvue.computed(lambda context: SetupDialog._validate_form(context)),
                'linking': False,  # True during linking process
            }
        )
        super().__init__(master=master)
        self.root.tk.eval('tk::PlaceWindow %s center' % (self.root))

    def link(self, force=False):
        self.get_event_loop().create_task(self._link_task(force=force))

    async def _link_task(self, force):
        self.data.linking = True
        try:
            # Asynchronously link to Minarca Server
            remoteurl = (
                self.data.remoteurl if self.data.remoteurl.startswith('http') else 'https://' + self.data.remoteurl
            )
            call = functools.partial(
                self.backup.link,
                remoteurl=remoteurl,
                username=self.data.username,
                password=self.data.password,
                repository_name=self.data.repository_name,
                force=force,
            )
            await self.get_event_loop().run_in_executor(None, call)
            # Link completed - Close Window.
            self.close()
        except RepositoryNameExistsError:
            logger.info('repository name `%s` already exists' % self.data.repository_name)
            self._prompt_link_force()
        except HttpInvalidUrlError:
            self.data.linking = False
            tkinter.messagebox.showwarning(
                master=self.root,
                icon='warning',
                title=_('Invalid remote server URL !'),
                message=_('Invalid remote server URL !'),
                detail=_(
                    "The remote server URL you entered for the connection is not valid. Check that you have entered the correct value. The URL must begin with `http://` or `https://` followed by a domain name."
                ),
            )
        except HttpConnectionError as e:
            self.data.linking = False
            logger.exception('http connection error')
            tkinter.messagebox.showwarning(
                master=self.root,
                icon='info',
                title=_('Failed to connect to remote server'),
                message=_('Failed to connect to remote server'),
                detail=_(
                    "Your computer cannot establish a connection to the remote server. Make sure your Internet connection is working and that the following URL is accessible with a Web browser: %s"
                )
                % (e.args and e.args[0]),
            )
        except HttpAuthenticationError as e:
            self.data.linking = False
            logger.warning('authentication failed')
            tkinter.messagebox.showwarning(
                master=self.root,
                icon='warning',
                title=_('Invalid username or password'),
                message=_('Invalid username or password'),
                detail=_(
                    "The username or password you entered to connect to the remote server is not valid.\n\nDetails: %s"
                )
                % str(e),
            )
        except SshConnectionError as e:
            self.data.linking = False
            logger.exception('ssh connection error')
            remotehost = self.backup.get_settings().get('remotehost', '')
            tkinter.messagebox.showwarning(
                master=self.root,
                icon='warning',
                title=_('Failed to connect to remote server'),
                message=_('Failed to connect to remote server'),
                detail=_("Your computer cannot establish a connection to the remote server: %s\n\n%s")
                % (remotehost, str(e)),
            )
        except Exception as e:
            self.data.linking = False
            logger.exception('fail to connect')
            tkinter.messagebox.showwarning(
                master=self.root,
                icon='warning',
                title=_('Unknown problem when connecting to the remote server'),
                message=_('Unknown problem when connecting to the remote server'),
                detail=_("An error occurred during the connection to Minarca server.\n\nDetails: %s") % str(e),
            )

    def close(self, event=None):
        """
        Close this window.
        """
        self.data.linking = False
        self.root.destroy()

    def _prompt_link_force(self):
        button_idx = tkinter.messagebox.askyesno(
            master=self.root,
            icon='question',
            title=_('Repository name already exists'),
            message=_('Do you want to replace the existing repository ?'),
            detail=_(
                "The repository name you have entered already exists on "
                "the remote server. If you continue with this repository, "
                "you will replace it's content using this computer. "
                "Otherwise, you must enter a different repository name."
            ),
        )
        if not button_idx:
            # Operation cancel by user
            self.data.linking = False
            return
        self.link(force=True)
