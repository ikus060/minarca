import pkg_resources

from minarca_client.ui import tkvue


class RootDialog(tkvue.Component):
    template = """
<TopLevel geometry="970x500" title="TKVue Test">
    <Frame pack-fill="both" pack-expand="1">
        <!-- Load image from variable -->
        <Label id="label" pack-fill="both" pack-expand="1" text="gastonf" image="{{icon_path}}" compound="left"/>
    </Frame>
</TopLevel>
    """
    data = tkvue.Context({'icon_path': pkg_resources.resource_filename('minarca_client.ui', 'theme/minarca-22.png')})


if __name__ == "__main__":
    dlg = RootDialog()
    dlg.mainloop()
