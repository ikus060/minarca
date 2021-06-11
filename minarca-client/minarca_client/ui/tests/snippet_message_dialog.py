# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Mar 22, 2021

Snippet test to validate Text behavior.

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from minarca_client.ui.widgets import Dialog, B, show_info


class ButtonDialog(Dialog):

    def _layout(self):
        layout = [
            [B('Default message dialog', metadata=(
                show_info, 'title', 'message', ['OK', 'Cancel']))],
        ]
        return layout


if __name__ == "__main__":
    dlg = ButtonDialog()
    dlg.open()
