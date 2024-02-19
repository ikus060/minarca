# Copyleft (C) 2023 IKUS Software. All lefts reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging
import tkinter.messagebox
import webbrowser

from minarca_client.core import BackupInstance
from minarca_client.core.compat import IS_WINDOWS
from minarca_client.core.exceptions import RemoteRepositoryNotFound
from minarca_client.locale import _
from minarca_client.ui import tkvue

from .side_pannel import SidePanel  # noqa

logger = logging.getLogger(__name__)


class BackupSettings(tkvue.Component):
    template = """
<Frame pack="expand:1; fill:both">
    <SidePanel create="{{create}}" is-remote="{{is_remote}}" text="Configure your backup settings for personalized data protection." step="2" maximum="3" pack="side:left; fill:y" />
    <Separator orient="vertical" pack="side:left; fill:y" />

    <!-- Form -->
    <Scrolledframe id="test" style="white.TFrame" pack="side:right; expand:1; fill:both" visible="{{ not working }}">
        <Frame style="white.TFrame" padding="50" pack="expand:1; fill:both" >
            <Label text="Backup configuration" style="h3.info.white.TLabel" pack="fill:x; pady:0 20"/>

            <Label text="Backup Frequency" style="white.TLabel" pack="fill:x; pady:0 10"/>
            <Combobox values="{{schedule_choices.values()}}" textvariable="{{ schedule_text }}" readonly="1" pack="fill:x; pady:0 20"/>

            <Label text="Excluded Days of the Week" style="white.TLabel" pack="fill:x; pady:0 10"/>
            <Frame style="white.TFrame" pack="fill:x; pady:0 20">
                <Checkbutton text="Monday" variable="{{ignore_weekday[0]}}" style="white.TCheckbutton" grid="row:0; column:0; sticky:w; padx:0 10"/>
                <Checkbutton text="Tuesday" variable="{{ignore_weekday[1]}}" style="white.TCheckbutton" grid="row:0; column:1; sticky:w; padx:0 10"/>
                <Checkbutton text="Wednesday" variable="{{ignore_weekday[2]}}" style="white.TCheckbutton" grid="row:0; column:2; sticky:w; padx:0 10"/>
                <Checkbutton text="Thrusday" variable="{{ignore_weekday[3]}}" style="white.TCheckbutton" grid="row:0; column:3; sticky:w; padx:0 10"/>
                <Checkbutton text="Friday" variable="{{ignore_weekday[4]}}" style="white.TCheckbutton" grid="row:1; column:0; sticky:w; padx:0 10"/>
                <Checkbutton text="Satursday" variable="{{ignore_weekday[5]}}" style="white.TCheckbutton" grid="row:1; column:1; sticky:w; padx:0 10"/>
                <Checkbutton text="Sunday" variable="{{ignore_weekday[6]}}" style="white.TCheckbutton" grid="row:1; column:2; sticky:w; padx:0 10"/>
            </Frame>

            <Label text="Data Retention Duration" style="white.TLabel" pack="fill:x; pady:0 10"/>
            <Combobox values="{{keepdays_choices.values()}}" textvariable="{{ keepdays_text }}" readonly="1" pack="fill:x; pady:0 29"/>

            <Label text="Inactivity Notification Period" style="white.TLabel" pack="fill:x; pady:0 10"/>
            <Combobox values="{{maxage_choices.values()}}" textvariable="{{ maxage_text }}" readonly="1" pack="fill:x; pady:0 20"/>

            <!-- Buttons -->
            <Frame style="white.TFrame" pack="pady:0 30; fill:x">
                <Button text="{{ _('Back') if create else _('Cancel') }}" command="{{cancel}}" style="default.TButton" pack="side:left; padx:0 10;" cursor="hand2" />
                <Button text="{{ _('Create') if create else _('Save') }}" command="{{save}}" style="info.TButton" pack="side:left" cursor="hand2" />
                <Button text="Edit configuration online" command="{{_edit_online}}" style="white.TLink" pack="side:right;anchor:e" cursor="hand2" visible="{{ is_remote and not create }}"/>
            </Frame>

            <Button text="Delete backup settings" image="trash-danger" compound="left" command="{{forget_instance}}" style="danger.white.TLink" pack="fill:x" cursor="hand2" visible="{{ not create }}"/>
        </Frame>
    </Scrolledframe>

    <Frame style="white.TFrame" padding="50" pack="expand:1; fill:both;" visible="{{ working }}">
        <Label image="spinner-64" style="white.TLabel" pack="expand:1; fill:both; pady:0 10" anchor="s"/>
        <Label text="Starting initial backup." style="light.white.TLabel" pack="fill:x;" anchor="n" />
        <Label text="Please Wait" style="light.white.TLabel" pack="expand:1; fill:both;" anchor="n" />
    </Frame>

</Frame>
"""
    create = tkvue.state(False)
    is_remote = tkvue.state(True)
    schedule = tkvue.state(24)
    keepdays = tkvue.state(-1)
    maxage = tkvue.state(3)
    ignore_weekday = tkvue.state([False, False, False, False, False, True, True])
    working = tkvue.state(False)

    # Only for Windows
    show_run_if_logged_out = tkvue.state(IS_WINDOWS)
    run_if_logged_out = tkvue.state(False)

    def __init__(self, master=None, backup=None, instance=None, create=False):
        """Edit or create backup configuration for the given instance"""
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        # Initialise the state.
        self.instance = instance
        self.create.value = create
        self.is_remote.value = instance.is_remote()
        self.schedule.value = self.instance.settings.schedule
        self.run_if_logged_out.value = IS_WINDOWS and self.backup.scheduler.run_if_logged_out

        # When editing current settings, load values from local settings or remote server.
        if not create:
            if instance.is_local():
                self.maxage.value = self.instance.settings.maxage
                self.keepdays.value = self.instance.settings.keepdays
            elif instance.is_remote():
                # FIXME Need to get this information from API.
                pass

        # Create the view
        super().__init__(master)

        # TODO For remote , we need to load settings from remote.
        # TODO Also check user role if user is allowed to change the retention period.

    @tkvue.computed_property
    def schedule_choices(self):
        return {1: _("Hourly"), 12: _("Twice a day"), 24: _("Once a day")}

    @tkvue.computed_property
    def schedule_text(self):
        return self.schedule_choices.value.get(self.schedule.value)

    @schedule_text.setter
    def schedule_text(self, new_text):
        for value, text in self.schedule_choices.value.items():
            if new_text == text:
                self.schedule.value = value
                break

    @tkvue.computed_property
    def maxage_choices(self):
        return dict(
            [
                (0, _('Never')),
                (1, _('1 day')),
                (2, _('2 days')),
                (3, _('3 days')),
                (4, _('4 days')),
                (5, _('5 days')),
                (6, _('6 days')),
                (7, _('1 week')),
                (14, _('2 weeks')),
                (21, _('3 weeks')),
                (28, _('4 weeks')),
                (31, _('1 month')),
            ]
        )

    @tkvue.computed_property
    def maxage_text(self):
        return self.maxage_choices.value.get(self.maxage.value)

    @maxage_text.setter
    def maxage_text(self, new_text):
        for value, text in self.maxage_choices.value.items():
            if new_text == text:
                self.maxage.value = value
                break

    @tkvue.computed_property
    def keepdays_choices(self):
        return dict(
            [
                (-1, _("Forever")),
                (1, _("1 day")),
                (2, _("2 days")),
                (3, _("3 days")),
                (4, _("4 days")),
                (5, _("5 days")),
                (6, _("6 days")),
                (7, _("1 week")),
                (14, _("2 weeks")),
                (21, _("3 weeks")),
                (30, _("1 month")),
                (60, _("2 months")),
                (90, _("3 months")),
                (120, _("4 months")),
                (150, _("5 months")),
                (180, _("6 months")),
                (210, _("7 months")),
                (240, _("8 months")),
                (270, _("9 months")),
                (300, _("10 months")),
                (330, _("11 months")),
                (365, _("1 year")),
                (730, _("2 years")),
                (1095, _("3 years")),
                (1460, _("4 years")),
                (1825, _("5 years")),
            ]
        )

    @tkvue.computed_property
    def keepdays_text(self):
        return self.keepdays_choices.value.get(self.keepdays.value)

    @keepdays_text.setter
    def keepdays_text(self, new_text):
        for value, text in self.keepdays_choices.value.items():
            if new_text == text:
                self.keepdays.value = value
                break

    @tkvue.command
    def cancel(self):
        if self.create.value:
            # In create mode, return backup to pattern view.
            toplevel = self.root.winfo_toplevel()
            toplevel.set_active_view('BackupPatterns', instance=self.instance, create=True)
        else:
            # Otherwise, go to dashboard view.
            toplevel = self.root.winfo_toplevel()
            toplevel.set_active_view('DashboardView')

    @tkvue.command
    def save(self):
        if self.working.value:
            # Operation should not be accessible if already working.
            return
        self.working.value = True
        self._task = self.get_event_loop().create_task(self._save())

    async def _save(self):
        try:
            # Ignore_weekday use a different format in settings.
            ignore_weekday = [idx for idx, value in enumerate(self.ignore_weekday.value) if value]
            # In create mode, save change and go to backup settings.
            with self.instance.settings as t:
                t.schedule = self.schedule.value
                t.ignore_weekday = ignore_weekday
                t.maxage = self.maxage.value
                t.keepdays = self.keepdays.value
                # Asynchronously start backup when creating.
                if self.create.value:
                    self.instance.start(force=True)
                # Asynchronously push settings to remote server.
                if self.instance.is_remote():
                    # Wait only if repository is getting created.
                    wait = self.create.value
                    await self.get_event_loop().run_in_executor(None, self.instance.save_remote_settings, wait)

            # Redirect user to dashboard.
            toplevel = self.root.winfo_toplevel()
            toplevel.set_active_view('DashboardView')
        except RemoteRepositoryNotFound as e:
            logger.warning('fail to save settings remotely', exc_info=1)
            tkinter.messagebox.showwarning(
                parent=self.root,
                title=_('Cannot save settings'),
                message=_('A problem occured while trying to save the backup settings.'),
                detail=str(e),
            )
        except TimeoutError:
            logger.warning('fail to save settings remotely', exc_info=1)
            tkinter.messagebox.showwarning(
                parent=self.root,
                title=_('Cannot save settings'),
                message=_('A problem occured while trying to save the backup settings.'),
                detail=_('The operation timeout.'),
            )
        except Exception as e:
            logger.exception('problem occured while saving backup settings.')
            tkinter.messagebox.showwarning(
                parent=self.root,
                title=_('Cannot save settings'),
                message=_('A problem occured while trying to save the backup settings.'),
                detail=str(e),
            )
        finally:
            self.working.value = False

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

    @tkvue.command
    def _edit_online(self):
        url = self.instance.get_repo_url('settings')
        webbrowser.open(url)
