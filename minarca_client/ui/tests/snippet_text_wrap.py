import PySimpleGUI as sg
from minarca_client.ui.widgets import Text


def main():

    layout = [[Text('This is a very long test that should wrap on multiple time. To make this work Text() widget must be created in a special way.',
                    wrap=True, expand_x=True, size=(-1, -1), key='TEXT')]]
    window = sg.Window('Window Title', layout, size=(
        200, 200), resizable=True, finalize=True)

    while True:
        event, values = window.read(timeout=100)
        if event in (None, 'Exit'):
            break

    window.close()


if __name__ == "__main__":
    main()
