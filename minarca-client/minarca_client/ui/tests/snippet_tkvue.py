from minarca_client.ui import tkvue


class RootDialog(tkvue.Component):
    template = """
<TopLevel geometry="970x500" title="TKVue Test" className="TKVue">
    <Frame pack-fill="both" pack-expand="true" padding="10">
        <Frame pack-fill="y" pack-side="left">
            <Button style="{{'primary.TButton' if active_view == 'list' else 'secondary.TButton'}}"
                command="set_active_view('list')" pack-fill="x" pack-padx="4" pack-pady="2" width="22" text="Dynamic list"
                cursor="hand2" />
            <Button style="{{'primary.TButton' if active_view == 'styles' else 'secondary.TButton'}}"
                command="set_active_view('styles')" pack-fill="x" pack-padx="4" pack-pady="2" width="22" text="Widgets styles"
                cursor="hand2" />
            <Button style="{{'primary.TButton' if active_view == 'widgets' else 'secondary.TButton'}}"
                command="set_active_view('widgets')" pack-fill="x" pack-padx="4" pack-pady="2" width="22" text="Widgets"
                cursor="hand2" />
        </Frame>
        <Frame pack-fill="both" pack-side="right" pack-expand="1" pack-padx="3">
            <Frame pack-fill="both" pack-expand="1" visible="{{active_view == 'list'}}">
                <Frame pack-fill="x">
                    <Frame pack-fill="x" for="p in people" pack-expand="1">
                        <Label text="{{p}}" pack-side="left">
                            <ToolTip text="{{len(p)}}" />
                        </Label>
                        <Button text="Del" command="delete_people(p)" pack-side="right"/>
                    </Frame>
                    <Frame pack-fill="x">
                        <Entry textvariable="{{new_people_name}}" pack-side="left" pack-expand="1" pack-fill="x" />
                        <Button text="Add" command="add_people(new_people_name)" pack-side="right"/>
                    </Frame>
                    <Frame pack-fill="x">
                        <Label text="New Value:" pack-side="left"/>
                        <Label text="{{new_people_name}}" pack-side="left"/>
                    </Frame>
                </Frame>
            </Frame>
            <Frame pack-fill="both" pack-expand="1" visible="{{active_view == 'styles'}}">
                <Frame pack-fill="x" for="item in ['primary', 'secondary', 'info', 'warning', 'danger']">
                    <Button text="{{item + '.TButton'}}" style="{{item + '.TButton'}}"
                        width="20" pack-padx="2" pack-pady="2" pack-side="left"/>
                    <Label text="{{item + '.TLabel'}}" style="{{item + '.TLabel'}}"
                        pack-side="left" width="20" pack-padx="2" pack-pady="2"/>
                    <Entry textvariable="{{text_entry}}" style="{{item + '.TEntry'}}"
                        pack-side="left" width="20" pack-padx="2" pack-pady="2"/>
                </Frame>
                <Separator pack-fill="x" pack-expand="1" />
            </Frame>
            <Frame pack-fill="both" pack-expand="1" visible="{{active_view == 'widgets'}}">
                <Frame pack-fill="x" >
                    <Label text="{{text_password}}" pack-side="left" />
                    <Entry show="•" textvariable="{{text_password}}" pack-side="left"/>
                </Frame>
                <Separator pack-fill="x" pack-expand="1" />
                <Frame pack-fill="x" >
                    <ComboBox textvariable="{{style_variable}}" values="primary secondary info warning danger"/>
                    <Radiobutton variable="{{style_variable}}" style="primary.TRadiobutton" value="primary" text="primary"/>
                    <Radiobutton variable="{{style_variable}}" style="secondary.TRadiobutton" value="secondary" text="secondary"/>
                    <Radiobutton variable="{{style_variable}}" style="info.TRadiobutton" value="info" text="info"/>
                    <Radiobutton variable="{{style_variable}}" style="warning.TRadiobutton" value="warning" text="warning"/>
                    <Radiobutton variable="{{style_variable}}" style="danger.TRadiobutton" value="danger" text="danger"/>
                    <Label text="{{style_variable}}" pack-side="bottom" style="{{style_variable + '.TLabel'}}"/>
                </Frame>
                <Separator pack-fill="x" pack-expand="1" />
                <Frame pack-fill="x" >
                    <Checkbutton variable="{{on_off_variable}}" pack-side="top" style="primary.TCheckbutton" text="primary.TCheckbutton"/>
                    <Checkbutton variable="{{on_off_variable}}" pack-side="top" style="info.Toolbutton" text="info.Toolbutton" />
                    <Checkbutton variable="{{on_off_variable}}" pack-side="top" style="warning.Roundtoggle.Toolbutton" text="warning.Roundtoggle.Toolbutton" />
                    <Checkbutton variable="{{on_off_variable}}" pack-side="top" text="danger.Squaretoggle.Toolbutton" />
                </Frame>
                <Separator pack-fill="x" pack-expand="1" />
                <Label text="Label with wrap=1, Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum." wrap="1" />
                <Separator pack-fill="x" pack-expand="1" />
                <ScrolledFrame pack-fill="x" pack-expand="1">
                    <Label pack-fill="x" pack-expand="1" for="i in range(1,100)" text="{{i}}" />
                </ScrolledFrame>
            </Frame>
        </Frame>
    </Frame>
</TopLevel>


    """
    data = tkvue.Context(
        {
            'active_view': 'list',
            'new_people_name': '',
            'text_entry': 'value',
            'text_password': 'password',
            'people': ['patrik', 'annik', 'michel'],
            'style_variable': 'primary',
            'on_off_variable': 'on',
        }
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_active_view(self, name):
        assert name in ['list', 'styles', 'widgets']
        self.data.active_view = name

    def delete_people(self, name):
        people = self.data.people.copy()
        people.remove(name)
        self.data.people = people

    def add_people(self, name):
        people = self.data.people.copy()
        people.append(name)
        self.data.people = people
        self.data.new_people_name = ''


if __name__ == "__main__":
    dlg = RootDialog()
    dlg.mainloop()
