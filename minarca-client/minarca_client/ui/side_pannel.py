# Copyleft (C) 2023 IKUS Software. All lefts reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging

from minarca_client.locale import _
from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class SidePanel(tkvue.Component):
    template = """
<Frame padding="50" rowconfigure-weight="0 0 1 0 2 0">
    <Label text="{{ title }}" style="h1.default.default.TLabel" grid="row:0; pady:0 20; sticky:we" wrap="1" width="20" justify="center" anchor="center" />
    <Label text="{{ text }}" style="light.default.TLabel" grid="row:1; sticky:we" wrap="1" width="20" justify="center" anchor="center"/>
    <Label image="{{ icon }}" grid="row:3"/>
    <Frame grid="row:5" visible="{{create}}">
        <Label for="{{ i in range(0, maximum) }}" style="{{ 'H1.info.default.TLabel' if i == step else 'H1.default.default.TLabel' }}" text="\u2022" pack="side:left; padx:4" font="Arial 28"/>
    </Frame>
</Frame>
"""
    is_remote = tkvue.state(True)
    create = tkvue.state(False)
    text = tkvue.state("")
    step = tkvue.state(0)
    maximum = tkvue.state(0)

    @tkvue.computed_property
    def title(self):
        if self.is_remote.value:
            if self.create.value:
                return _('Create a remote backup')
            else:
                return _('Remote backup')
        else:
            if self.create.value:
                return _('Create a local backup')
            else:
                return _('Local backup')

    @tkvue.computed_property
    def icon(self):
        if self.is_remote.value:
            return 'remote-backup-logo-256'
        else:
            return 'local-backup-logo-256'

    @tkvue.attr('create')
    def set_create(self, value):
        self.create.value = value

    @tkvue.attr('is-remote')
    def set_is_remote(self, value):
        if isinstance(value, str):
            value = value.lower() in ['1', 'true']
        self.is_remote.value = value

    @tkvue.attr('text')
    def set_text(self, value):
        self.text.value = value

    @tkvue.attr('maximum')
    def set_maximum(self, value):
        assert int(value) >= 0
        self.maximum.value = int(value)

    @tkvue.attr('step')
    def set_step(self, value):
        assert int(value) >= 0
        self.step.value = int(value)
