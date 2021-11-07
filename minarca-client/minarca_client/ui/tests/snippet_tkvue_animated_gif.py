from minarca_client.ui import tkvue


class RootDialog(tkvue.Component):
    template = """
<TopLevel geometry="970x500" title="TKVue Test">
    <Frame pack-fill="both" pack-expand="true" padding="10">
        <Checkbutton text="Show animation" variable="{{show}}" />
        <Label image="spinner-24" visible="{{show}}"/>
    </Frame>
</TopLevel>
    """
    data = tkvue.Context({
        'show': True,
    })


if __name__ == "__main__":
    dlg = RootDialog()
    dlg.mainloop()
