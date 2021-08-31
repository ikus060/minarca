# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Mar 22, 2021

Snippet test to validate Text behavior.

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from minarca_client.ui.widgets import Dialog, T, HR

from minarca_client.ui.theme import TEXT_HEADER1, TEXT_DEFAULT, TEXT_STRONG,\
    TEXT_SMALL, TEXT_SUCCESS, TEXT_DANGER, TEXT_WARNING


class TextDialog(Dialog):

    def _layout(self):
        layout = [
            [T('Header1', **TEXT_HEADER1)],
            [T('Strong text', **TEXT_STRONG)],
            [T('Small text', **TEXT_SMALL)],
            [T('Success text', **TEXT_SUCCESS)],
            [T('Warning text', **TEXT_WARNING)],
            [T('Danger text', **TEXT_DANGER)],
            [T('Default text', **TEXT_DEFAULT)],
            [HR(pad=(0, 5))],
            # Check ellipsis
            [T('This is a long text to check ellipsis at end', size=(25, 1),
               ellipsis='end', **TEXT_DEFAULT)],
            [T('This is a long text to check ellipsis in center', size=(25, 1),
               ellipsis='center', **TEXT_DEFAULT)],
            [T('This is a long text to check ellipsis at start', size=(25, 1),
               ellipsis='start', **TEXT_DEFAULT)],
            [HR(pad=(0, 5))],
            # Check tooltip
            [T('Text with tooltip', size=(25, 1),
               ellipsis='start', tooltip='My tooltip', ** TEXT_DEFAULT)],
            [T('This is a long text with custom tooltip.', size=(25, 1),
               ellipsis='start', tooltip='My tooltip', ** TEXT_DEFAULT)],
            # Wrap
            [T('This is a very long test that should wrap on multiple time. To make this work Text() widget must be created in a special way.',
               size=(None, 3), expand_x=True, expand_y=True, **TEXT_DEFAULT)],
        ]
        return layout


if __name__ == "__main__":
    dlg = TextDialog()
    dlg.open(size=(500, 500))
