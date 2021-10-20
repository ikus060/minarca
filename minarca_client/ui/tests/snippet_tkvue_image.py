

import pkg_resources
from minarca_client.ui import tkvue


class RootDialog(tkvue.Component):
    template = """
<Tk geometry="970x500" title="TKVue Test" className="TKVue">
    <Frame pack-fill="both" pack-expand="1">
        <!-- Load image from variable -->
        <Label id="label" pack-fill="both" pack-expand="1" text="foo" image="{{icon_path}}" />
        <Label text="coucou" />
    </Frame>
</Tk>
    """
    data = tkvue.Context({
        'icon_path': pkg_resources.resource_filename('minarca_client.ui', 'images/minarca_48.png')
    })


if __name__ == "__main__":
    dlg = RootDialog()
    dlg.mainloop()
