from minarca_client.ui import tkvue


class RootDialog(tkvue.Component):
    template = """
<Tk geometry="970x500" title="TKVue Test" className="TKVue">
    <Frame pack-fill="both" pack-expand="true" padding="10">
        <Label text="Label with tooltip">
            <Tooltip text="Tooltip text for label" />
        </Label>

        <Button text="Button with tooltip">
            <Tooltip text="{{tooltip_value}}" />
        </Button>
    </Frame>
</Tk>
    """
    data = tkvue.Context({
        'tooltip_value': 'Tooltip value to be displayed'
    })


if __name__ == "__main__":
    dlg = RootDialog()
    dlg.mainloop()
