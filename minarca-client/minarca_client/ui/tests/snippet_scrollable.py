

from minarca_client.ui import tkvue


class RootDialog(tkvue.Component):
    template = """
<Tk geometry="970x500" title="TKVue Test" className="TKVue">
    <Frame pack-fill="both" pack-expand="true" padding="10">
        <Label text="Static text on top of scrollable" />
        <ScrolledFrame pack-fill="both" pack-expand="1">
            <Label pack-fill="x" pack-expand="1" for="i in range(1,100)" text="{{i}}" />
        </ScrolledFrame>
    </Frame>
</Tk>


    """
    data = tkvue.Context({
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


if __name__ == "__main__":
    dlg = RootDialog()
    dlg.mainloop()
