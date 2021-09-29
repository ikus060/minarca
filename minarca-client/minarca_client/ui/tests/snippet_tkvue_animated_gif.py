from minarca_client.ui import tkvue

import pkg_resources


class RootDialog(tkvue.Component):
    template = """
<Tk geometry="970x500" title="TKVue Test" className="TKVue">
    <Frame pack-fill="both" pack-expand="true" padding="10">
        <Checkbutton text="Show animation" variable="{{show}}" />
        <Label image="{{animated_gif_path}}" visible="{{show}}"/>
    </Frame>
</Tk>
    """
    data = tkvue.Context({
        'show': True,
        'animated_gif_path': pkg_resources.resource_filename('minarca_client.ui', 'images/spin_32.gif')
    })


if __name__ == "__main__":
    dlg = RootDialog()
    dlg.mainloop()
