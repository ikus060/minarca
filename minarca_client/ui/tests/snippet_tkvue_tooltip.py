from minarca_client.ui import tkvue


class RootDialog(tkvue.Component):
    template = """
<TopLevel geometry="970x500" title="TKVue Test">
    <Frame pack-fill="both" pack-expand="true" padding="10">
        <Label text="Label with tooltip">
            <Tooltip text="Tooltip text for label" />
        </Label>

        <Button text="Button with tooltip">
            <Tooltip text="{{tooltip_value}}" />
        </Button>

        <Label text="Tooltip with width">
            <Tooltip wrap="1" width="50" text="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum" />
        </Label>
    </Frame>
</TopLevel>
    """
    data = tkvue.Context({
        'tooltip_value': 'Tooltip value to be displayed'
    })


if __name__ == "__main__":
    dlg = RootDialog()
    dlg.mainloop()
