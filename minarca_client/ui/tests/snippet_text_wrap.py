import PySimpleGUI as sg  # @UnresolvedImport


def main():
    # Create initial layout
    layout = [[sg.Text('This is a very long test that should wrap on multiple time. To make this work Text() widget must be created in a special way.', size=(None, 3), expand_x=True)]]

    # Create windows
    window = sg.Window('Window Title', layout, size=(200, 200))
    event, values = window.read(timeout=0)

    while True:  # Event Loop
        event, values = window.read(timeout=100)
        if event in (None, 'Exit'):
            break

    window.close()


if __name__ == "__main__":
    main()
