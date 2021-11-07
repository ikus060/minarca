

from minarca_client.ui import tkvue
from minarca_client.ui.theme import style


class RootDialog(tkvue.Component):
    template = """
<TopLevel geometry="970x500" title="TKVue Test" className="TKVue">
    <Frame pack-fill="both" pack-expand="true" padding="10">
        <Label text="Static text on top of scrollable" />
        <ScrolledFrame pack-fill="both" pack-expand="1" pack-side="left">
            <Label pack-fill="x" pack-expand="1" for="i in range(1,100)" text="{{ 'left %s' % i }}" />
        </ScrolledFrame>
        <ScrolledFrame pack-fill="both" pack-expand="1" pack-side="right">
            <Label pack-fill="x" pack-expand="1" for="i in range(1,5)" text="{{ 'right %s' % i }}" />
        </ScrolledFrame>
    </Frame>
</TopLevel>


    """
    data = tkvue.Context({
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style(self.root)


if __name__ == "__main__":
    dlg = RootDialog()
    dlg.mainloop()
