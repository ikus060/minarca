# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Mar 22, 2021

Snippet test to validate Text behavior.

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from minarca_client.ui.widgets import Dialog, B, show_info, TRASH

from minarca_client.ui.theme import BUTTON_SUCCESS


class ButtonDialog(Dialog):

    def _layout(self):
        layout = [
            [B('Default Button', metadata=self._show_alert)],
            [B('Success Button', **BUTTON_SUCCESS, metadata=self._show_alert)],

            [B(TRASH, metadata=self._show_alert)],

        ]
        return layout

    def _show_alert(self, event, values):
        show_info(self.window, 'Title', 'Button clicked !')


if __name__ == "__main__":
    dlg = ButtonDialog()
    dlg.open()
