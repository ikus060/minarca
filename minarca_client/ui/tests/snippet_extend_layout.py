import PySimpleGUI as sg  # @UnresolvedImport


def main():
    # Create initial layout
    childs = [
        [sg.Text('foo', key='foo')],
        [sg.Text('hello', key='hello')]
    ]
    scrollable = sg.Column(childs, scrollable=True,
                           key='scroll', expand_x=True, expand_y=True)
    layout = [[scrollable]]

    # Create windows
    window = sg.Window('Window Title', layout, size=(200, 200))
    event, values = window.read(timeout=0)

    # extend layout
    window.extend_layout(scrollable, [[sg.Text('bar', key='bar')]])

    # check value of ParentContainer
    print(window['foo'].ParentContainer.Key)
    print(window['hello'].ParentContainer.Key)
    print(window['bar'].ParentContainer.Key)
    window.visibility_changed()
    scrollable.contents_changed()

    while True:  # Event Loop
        event, values = window.read(timeout=100)
        if event in (None, 'Exit'):
            break

    window.close()


if __name__ == "__main__":
    main()
