# Copyleft (C) 2023 IKUS Software. All lefts reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging
import tkinter.filedialog
import tkinter.messagebox

from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class StepIndicator(tkvue.Component):
    template = """<Frame >
<Label for="{{ i in range(0, maximum) }}" style="{{ 'H1.info.default.TLabel' if i == value else 'H1.default.default.TLabel' }}" text="\u2022" pack="side:left; padx:4" font="Arial 28"/>
</Frame>
"""
    maximum = tkvue.state(3)
    value = tkvue.state(1)

    @tkvue.attr('maximum')
    def set_maximum(self, value):
        assert int(value) >= 0
        self.maximum.value = int(value)

    @tkvue.attr('value')
    def set_value(self, value):
        assert int(value) >= 0
        self.value.value = int(value)


class ThemeExample(tkvue.Component):
    template = """<Frame style="white.TFrame" padding="25">
<Label text="Theme example" style="h1.default.white.TLabel" justify="center" />
<ScrolledFrame pack="fill:both; expand:1; pady:5 0">
    <Frame  pack="pady:0 15">
        <Label text="H1 example" style="h1.default.default.TLabel" justify="center" />
        <Label text="H2 example" style="h2.default.default.TLabel" justify="center" />
        <Label text="H3 example" style="h3.default.default.TLabel" justify="center" />
        <Label text="Default example" style="default.default.TLabel" justify="center" />
        <Label text="small example" style="sm.default.default.TLabel" justify="center" />
        <Label text="x-small example" style="xs.default.default.TLabel" justify="center" />
    </Frame>

    <Frame pack="pady:0 15">
        <Button text="Large button" style="lg.default.TButton" pack="padx:5; side:left"/>
        <Button text="Default button" style="default.TButton" pack="padx:5; side:left"/>
        <Button text="Small button" style="sm.default.TButton" pack="padx:5; side:left"/>
    </Frame>

    <Frame pack="pady:0 15">
        <Button text="Default link button" style="TLink" pack="padx:5; side:left"/>
        <Button text="Secondary link button" style="secondary.default.TLink" pack="padx:5; side:left"/>
        <Button text="Success link button" style="success.default.TLink" pack="padx:5; side:left"/>
        <Button text="Info link button" style="info.default.TLink" pack="padx:5; side:left"/>
        <Button text="Warning link button" style="warning.default.TLink" pack="padx:5; side:left"/>
        <Button text="Danger link button" style="danger.default.TLink" pack="padx:5; side:left"/>
        <Button text="Light link button" style="light.default.TLink" pack="padx:5; side:left"/>
    </Frame>

    <Frame pack="pady:0 15">
        <Button text="Default button" style="default.TButton" pack="padx:5; side:left"/>
        <Button text="Secondary button" style="secondary.TButton" pack="padx:5; side:left"/>
        <Button text="Success button" style="success.TButton" pack="padx:5; side:left"/>
        <Button text="Info button" style="info.TButton" pack="padx:5; side:left"/>
        <Button text="Warning button" style="warning.TButton" pack="padx:5; side:left"/>
        <Button text="Danger button" style="danger.TButton" pack="padx:5; side:left"/>
        <Button text="Light button" style="light.TButton" pack="padx:5; side:left"/>
    </Frame>

    <Frame pack="pady:0 15">
        <Button text="Outline button" style="default.TOutlineButton" pack="padx:5; side:left"/>
        <Button text="Outline White button" style="white.TOutlineButton" pack="padx:5; side:left"/>
        <Button text="Outline Light info button" style="light-info.TOutlineButton" pack="padx:5; side:left"/>
        <Button text="Outline Light success button" style="light-success.TOutlineButton" pack="padx:5; side:left"/>
        <Button text="Outline Light warning button" style="light-warning.TOutlineButton" pack="padx:5; side:left"/>
        <Button text="Outline Light danger button" style="light-danger.TOutlineButton" pack="padx:5; side:left"/>
    </Frame>
    <Frame pack="pady:0 15">
        <Label text="Default label" style="TLabel" pack="padx:5; side:left"/>
        <Label text="Secondary label" style="secondary.default.TLabel" pack="padx:5; side:left"/>
        <Label text="Success label" style="success.default.TLabel" pack="padx:5; side:left"/>
        <Label text="Info label" style="info.default.TLabel" pack="padx:5; side:left"/>
        <Label text="Warning label" style="warning.default.TLabel" pack="padx:5; side:left"/>
        <Label text="Danger label" style="danger.default.TLabel" pack="padx:5; side:left"/>
        <Label text="Light label" style="light.default.TLabel" pack="padx:5; side:left"/>
    </Frame>

    <Frame pack="pady:0 15">
        <Checkbutton text="Default check" variable="{{checked}}" style="TCheckbutton" pack="fill:x; side:left"/>
        <Checkbutton text="Secondary check" variable="{{checked}}" style="secondary.default.TCheckbutton" pack="fill:x; side:left"/>
        <Checkbutton text="Success check" variable="{{checked}}" style="success.default.TCheckbutton" pack="fill:x; side:left"/>
        <Checkbutton text="Info check" variable="{{checked}}" style="info.default.TCheckbutton" pack="fill:x; side:left"/>
        <Checkbutton text="Warning check" variable="{{checked}}" style="warning.default.TCheckbutton" pack="fill:x; side:left"/>
        <Checkbutton text="Danger check" variable="{{checked}}" style="danger.default.TCheckbutton" pack="fill:x; side:left"/>
        <Checkbutton text="Light check" variable="{{checked}}" style="light.default.TCheckbutton" pack="fill:x; side:left"/>
    </Frame>
    <Frame pack="pady:0 15">
        <Radiobutton text="Disabled radio" variable="{{checked}}" value="0" style="TRadiobutton" pack="fill:x; side:left" />
        <Radiobutton text="Secondary radio" variable="{{checked}}" value="0" style="secondary.default.TRadiobutton" pack="fill:x; side:left"/>
        <Radiobutton text="Success radio" variable="{{checked}}" value="1" style="success.default.TRadiobutton" pack="fill:x; side:left"/>
        <Radiobutton text="Info radio" variable="{{checked}}" value="0" style="info.default.TRadiobutton" pack="fill:x; side:left"/>
        <Radiobutton text="Warning radio" variable="{{checked}}" value="1" style="warning.default.TRadiobutton" pack="fill:x; side:left"/>
        <Radiobutton text="Danger radio" variable="{{checked}}" value="0" style="danger.default.TRadiobutton" pack="fill:x; side:left"/>
        <Radiobutton text="Light radio" variable="{{checked}}" value="1" style="light.default.TRadiobutton" pack="fill:x; side:left"/>
    </Frame>
    <Frame pack="pady:0 15">
        <Checkbutton text="Default check" variable="{{checked}}" style="default.white.Roundtoggle.TCheckbutton" pack="fill:x; side:left"/>
        <Checkbutton text="Info check" variable="{{checked}}" style="info.white.Roundtoggle.TCheckbutton" pack="fill:x; side:left"/>
    </Frame>
    <Frame pack="pady:0 15">
        <Entry text="Default text; fill:x; side:left"/>
        <Button text="File browser" command="{{_open_file_browser}}" pack="padx:5; side:left" />
        <Button text="Message box" command="{{_open_message_box}}" pack="padx:5; side:left" />
        <Combobox textvariable="{{selected_color}}" values="blue red green" pack="padx:5; side:left" />
        <Combobox textvariable="{{selected_color}}" values="blue red green" pack="padx:5; side:left" state="readonly" />
    </Frame>
    <Frame pack="pady:0 15; fill:x">
        <Progressbar orient="horizontal" mode="indeterminate" style="TProgressbar" pack="fill:x; pady:5"/>
        <Progressbar orient="horizontal" mode="indeterminate" style="secondary.Horizontal.TProgressbar" pack="fill:x; pady:5"/>
        <Progressbar orient="horizontal" mode="determinate"  value="{{progress}}" style="success.Horizontal.TProgressbar" pack="fill:x; pady:5"/>
        <Progressbar orient="horizontal" mode="indeterminate" style="info.Horizontal.TProgressbar" pack="fill:x; pady:5"/>
        <Progressbar orient="horizontal" mode="determinate" value="{{progress}}" style="warning.Horizontal.TProgressbar" pack="fill:x; pady:5"/>
        <Progressbar orient="horizontal" mode="indeterminate" style="danger.Horizontal.TProgressbar" pack="fill:x; pady:5" />
    </Frame>
    <Frame pack="pady:0 15; fill:x">
        <Frame style="white.TLabelframe" pack="fill:x; expand:1" padding="10 25" pack="padx:0 5; side:left">
            <Label text="Default label in card" background="#ffffff" />
            <Label text="Light label in card" style="light.white.TLabel"/>
            <Checkbutton text="Default check" variable="{{checked}}" style="default.white.TCheckbutton" pack="fill:x; side:left"/>
        </Frame>
        <Frame style="light-info.TLabelframe" pack="fill:x; expand:1" padding="10 25" pack="padx:5 0; side:left">
            <Label text="Default label in card" style="default.light-info.TLabel"/>
            <Label text="Info label in card" style="info.light-info.TLabel"/>
            <Checkbutton text="Info check" variable="{{checked}}" style="info.light-info.TCheckbutton" pack="fill:x; side:left"/>
        </Frame>
        <Frame style="light-warning.TLabelframe" pack="fill:x; expand:1" padding="10 25" pack="padx:5 0; side:left">
            <Label text="Default label in card" style="default.light-warning.TLabel"/>
            <Label text="Warning label in card" style="warning.light-warning.TLabel"/>
            <Checkbutton text="Warning check" variable="{{checked}}" style="warning.light-warning.TCheckbutton" pack="fill:x; side:left"/>
        </Frame>
        <Frame style="light-danger.TLabelframe" pack="fill:x; expand:1" padding="10 25" pack="padx:5 0; side:left">
            <Label text="Default label in card" style="default.light-danger.TLabel"/>
            <Label text="Danger label in card" style="danger.light-danger.TLabel"/>
            <Checkbutton text="Danger check" variable="{{checked}}" style="danger.light-danger.TCheckbutton" pack="fill:x; side:left"/>
        </Frame>
        <Frame style="light-success.TLabelframe" pack="fill:x; expand:1" padding="10 25" pack="padx:5 0; side:left">
            <Label text="Default label in card" style="default.light-success.TLabel"/>
            <Label text="Success label in card" style="success.light-success.TLabel"/>
            <Checkbutton text="Success check" variable="{{checked}}" style="success.light-success.TCheckbutton" pack="fill:x; side:left"/>
        </Frame>
    </Frame>
    <Frame pack="pady:0 15; fill:x">
        <Frame pack="side:left">
            <StepIndicator maximum="3" value="1" />
        </Frame>
        <Label style="success.white.TLabel" image="check-circle-fill-success" text="Success" compound="left" pack="side:left; padx:5" />
        <Label style="danger.white.TLabel" image="x-circle-fill-danger" text="Fail" compound="left" pack="side:left; padx:5" />
        <Label style="default.white.TLabel" image="chevron-right" pack="side:left; padx:5" />
        <Label style="default.white.TLabel" image="trash" pack="side:left; padx:5" />
        <Label style="danger.white.TLabel" image="trash-danger" text="Delete" compound="left" pack="side:left; padx:5" />
    </Frame>
    <Frame pack="pady:0 15; fill:x">
        <Frame pack="side:left" padding="15">
            <Label text="Left content" />
        </Frame>
        <Separator orient="vertical" pack="side:left; fill:y"/>
        <Frame style="white.TFrame" padding="15" pack="side:left; fill:x;; expand:1">
            <Label text="Right content" style="white.TLabel" />
        </Frame>
    </Frame>
    <Frame pack="pady:0 15; fill:x">
        <Button text="Backup Configuration" compound="right" style="info.play-circle.TListitem" pack="fill:x; expand:1" padding="10" />
        <Button text="Backup Configuration" image="check-circle-fill-success" compound="right" style="white.TListitem" pack="fill:x; expand:1" padding="10" />
        <Button text="Light Success list item" style="light-success.TListitem" pack="fill:x; expand:1" padding="10" />
        <Button text="Light info list item" style="light-info.TListitem" pack="fill:x; expand:1" padding="10" />
        <Button text="Light warning list item" style="light-warning.TListitem" pack="fill:x; expand:1" padding="10" />
    </Frame>
</ScrolledFrame>
</Frame>"""

    checked = tkvue.state(1)
    progress = tkvue.state(45)
    selected_color = tkvue.state("blue")

    def __init__(self, master=None, backup=None):
        assert backup is not None
        super().__init__(master)

    @tkvue.command
    def _open_file_browser(self):
        tkinter.filedialog.askdirectory(
            title='Example of dialog using default theme.',
            parent=self.root,
            mustexist=True,
        )

    @tkvue.command
    def _open_message_box(self):
        tkinter.messagebox.askyesno(
            parent=self.root,
            title='Message box title',
            message='Short message displayed to user',
            detail="Detailed message displayed to the user to provide more information or context to help user take a decision.",
        )

    # TODO Date selection (round, select vs not select)
