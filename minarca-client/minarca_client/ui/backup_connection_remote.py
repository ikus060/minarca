# Copyleft (C) 2023 IKUS Software. All lefts reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import functools
import logging
import tkinter.messagebox

from minarca_client.core.compat import get_default_repositoryname
from minarca_client.core.exceptions import (
    BackupError,
    HttpConnectionError,
    RepositoryNameExistsError,
    ConfigureBackupError,
)
from minarca_client.locale import _
from minarca_client.ui import tkvue

from .side_pannel import SidePanel  # noqa

logger = logging.getLogger(__name__)


class BackupConnectionRemote(tkvue.Component):
    template = """
<Frame pack="expand:1; fill:both">
    <SidePanel create="{{create}}" is-remote="True" text="Provide your login details to configure remote backup." step="0" maximum="3" pack="side:left; fill:y" />
    <Separator orient="vertical" pack="side:left; fill:y" />

    <!-- Form -->
    <Scrolledframe id="test" style="white.TFrame" pack="side:right; expand:1; fill:both" visible="{{ not working }}">
        <Frame style="white.TFrame" padding="50" pack="expand:1; fill:both" >
            <Label text="Server connexion" style="h3.info.white.TLabel" pack="fill:x; pady:0 20" />

            <!-- Reset -->
            <Button text="Reset server connexion" command="{{reset}}" style="sm.secondary.TButton" pack="anchor:w; pady:0 20" visible="{{ not edit }}"/>

            <!-- Errors -->
            <Frame style="light-danger.TLabelframe" pack="fill:x; pady:0 15" padding="10">
                <Label text="{{error_message}}" style="white.danger.TLabel" wrap="1" pack="fill:x; pady:0 15" padding="12" visible="{{error_message}}" />
                <Label text="{{error_detail}}" style="danger.white.TLabel" wrap="1" pack="fill:x; pady:0 20" visible="{{error_detail}}" />
            </Frame>

            <!-- Reponame -->
            <Label text="Backup name" style="white.TLabel" pack="fill:x" disabled="{{not edit}}"/>
            <Entry textvariable="{{repositoryname}}" pack="fill:x; pady:10" disabled="{{not edit}}"/>

            <!-- URL -->
            <Label text="Address (IP or domain)" style="white.TLabel" pack="fill:x" disabled="{{not edit}}"/>
            <Entry textvariable="{{remoteurl}}" pack="fill:x; pady:10" disabled="{{not edit}}"/>

            <!-- Username -->
            <Label text="Username" style="white.TLabel" pack="fill:x" disabled="{{not edit}}"/>
            <Entry textvariable="{{username}}" pack="fill:x; pady:10" disabled="{{not edit}}"/>

            <!-- Password -->
            <Label text="Password (or Access token)" style="white.TLabel" pack="fill:x" disabled="{{not edit}}"/>
            <Entry textvariable="{{password}}" show="•" pack="fill:x; pady:10" disabled="{{not edit}}"/>

            <!-- Buttons -->
            <Frame style="white.TFrame" pack="fill:x; pady:20 0;">
                <Button text="{{ _('Back') if create else _('Cancel') }}" command="{{cancel}}" style="default.TButton" pack="side:left; padx:0 10;" cursor="hand2" />
                <Button text="{{ _('Next') if create else _('Save') }}" command="{{save}}" style="info.TButton" pack="side:left" state="{{'!disabled' if valid else 'disabled'}}" cursor="{{'hand2' if valid else 'arrow'}}" visible="{{ edit }}"/>
            </Frame>

            <!-- Forget -->
            <Button text="Delete backup settings" image="trash-danger" compound="left" command="{{forget_instance}}" style="danger.white.TLink" pack="fill:x; pady:30 0;" cursor="hand2" visible="{{ not create }}"/>

        </Frame>
    </Scrolledframe>

    <Frame style="white.TFrame" padding="50" pack="expand:1; fill:both;" visible="{{ working }}">
        <Label image="spinner-64" style="white.TLabel" pack="expand:1; fill:both; pady:0 10" anchor="s"/>
        <Label text="Verify connection to remote server." style="light.white.TLabel" pack="fill:x;" anchor="n" />
        <Label text="Please Wait" style="light.white.TLabel" pack="expand:1; fill:both;" anchor="n" />
    </Frame>
</Frame>
"""
    edit = tkvue.state(True)
    create = tkvue.state(False)
    repositoryname = tkvue.state("")
    remoteurl = tkvue.state("")
    username = tkvue.state("")
    password = tkvue.state("")
    working = tkvue.state(False)
    error_message = tkvue.state(None)
    error_detail = tkvue.state(None)

    _test_connection_task = None

    def __init__(self, master=None, backup=None, create=False, instance=None):
        assert backup is not None
        self.backup = backup
        self.instance = instance
        self.create.value = create
        if self.instance is None:
            # If creating a new repo, provide default values
            self.edit.value = True
            self.repositoryname.value = get_default_repositoryname()
        else:
            # If editing a repo, fill values with existing settings.
            self.edit.value = False
            self.repositoryname.value = self.instance.settings.repositoryname
            self.remoteurl.value = self.instance.settings.remoteurl
            self.username.value = self.instance.settings.username
            self.password.value = '******'
        super().__init__(master)
        # Check connection to server when editing
        if not create:
            self._test_connection_task = self.get_event_loop().create_task(self._test_connection(instance))
            self.root.bind('<Destroy>', self._cancel_tasks, add="+")

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._test_connection_task:
            self._test_connection_task.cancel()

    async def _test_connection(self, instance):
        # Test connectivity with remote server.
        try:
            await self.get_event_loop().run_in_executor(None, instance.test_connection)
        except Exception as e:
            # Show error message.
            self.error_detail.value = str(e)

    @tkvue.computed_property
    def valid(self):
        """
        Used to check if the data is valid according to the current step.
        """
        return self.repositoryname.value and self.remoteurl.value and self.username.value and self.password.value

    @tkvue.command
    def reset(self):
        # When user click on Reset server connexion. Let enable editing.
        self.edit.value = True
        self.password.value = ''

    @tkvue.command
    def cancel(self):
        # When operation is cancel by user, redirect it.
        toplevel = self.root.winfo_toplevel()
        if self.create.value:
            toplevel.set_active_view('BackupCreate')
        else:
            toplevel.set_active_view('DashboardView')

    @tkvue.command
    def save(self, event=None):
        if not self.valid.value or self.working.value:
            # Operation should not be accessible if not valid.
            return
        coro = self._create_remote(
            remoteurl=self.remoteurl.value,
            username=self.username.value,
            password=self.password.value,
            repositoryname=self.repositoryname.value,
        )
        self.working.value = True
        self.error_message.value = None
        self.error_detail.value = None
        handle = self.get_event_loop().create_task(coro)
        self.root.bind('<Destroy>', lambda unused: handle.cancel(), add="+")

    @tkvue.command
    def forget_instance(self):
        assert not self.create.value
        # In edit mode, confirm operation, destroy the configuration and go to dashboard.
        return_code = tkinter.messagebox.askyesno(
            parent=self.root,
            title=_('Are you sure ?'),
            message=_('Are you sure you want to disconnect this Minarca agent?'),
            detail=_(
                'If you disconnect this computer, this Minarca agent will erase its identity and will no longer run backup on schedule.'
            ),
        )
        if not return_code:
            # Operation cancel by user.
            return
        self.instance.forget()
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('DashboardView')

    async def _create_remote(self, remoteurl, username, password, repositoryname, force=False):
        # Support IP or Domain name.
        remoteurl = remoteurl if remoteurl.startswith('http') else 'https://' + remoteurl
        try:
            # Create new instance if none exists yet.
            # Asynchronously link to Minarca Server
            call = functools.partial(
                self.backup.configure_remote,
                remoteurl=remoteurl,
                username=username,
                password=password,
                repositoryname=repositoryname,
                force=force,
                instance=self.instance,
            )
            self.instance = await self.get_event_loop().run_in_executor(None, call)
        except RepositoryNameExistsError as e:
            logger.warning(str(e))
            # If repo already exists remotely, ask to replace it.
            ret = tkinter.messagebox.askyesno(
                parent=self.root,
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
            if ret:
                await self._create_remote(remoteurl, username, password, repositoryname, force=True)
        except ConfigureBackupError as e:
            logger.warning(str(e))
            self.error_message.value = e.message
            self.error_detail.value = e.detail
        except BackupError as e:
            logger.warning(str(e))
            self.error_message.value =  _('Failed to establish connectivity with remote server.')
            self.error_detail.value = str(e)
        except Exception as e:
            logger.exception('unknown exception')
            self.error_message.value = _('Unknown problem occured when connecting to the remote server.')
            self.error_detail.value = _(
                "An error occurred during the connection to Minarca server.\n\nDetails: %s"
            ) % str(e)
        else:
            self.error_message.value = None
            self.error_detail.value = None
            # On success, go to next step
            if self.create.value:
                toplevel = self.root.winfo_toplevel()
                toplevel.set_active_view('BackupPatterns', instance=self.instance, create=self.create.value)
            else:
                toplevel = self.root.winfo_toplevel()
                toplevel.set_active_view('DashboardView')
        finally:
            self.working.value = False
