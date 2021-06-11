# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Mar 22, 2021

Snippet to test the behaviour of PatternList.

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from minarca_client.ui.widgets import PatternList
import PySimpleGUI as sg  # @UnresolvedImport


def main():
    column = PatternList(size=(300, 330))
    column.set_patterns(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'])

    layout = [[column]] + [
        [sg.Button('Add row', key='-B1-')] + [sg.Button('Del row',
                                                        key='-B2-')] + [sg.Button('Default', key='-B3-')]
    ]

    count = 1

    window = sg.Window('Window Title', layout)
    while True:  # Event Loop
        event, values = window.read()
        if event in (None, 'Exit'):
            break
        if event == '-B1-':
            column.add('coucou %s' % count)
            count += 1
        elif event == '-B2-':
            count -= 1
            column.remove(-1)
        elif event == '-B3-':
            count -= 1
            column.set_patterns(['default %s' % i for i in range(1, 10)])
        elif event.startswith('X') and window[event].metadata:
            pattern = window[event].metadata
            column.remove(pattern)

    window.close()


if __name__ == "__main__":
    main()
