# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import contextlib


@contextlib.contextmanager
def disable(parent):
    try:
        # Place Window on top of parent
        if parent and parent.get_root_window():
            # Disable the Window
            window = parent.get_root_window()
            window.children[0].disabled = True
        yield
    finally:
        # Restore state of parent window
        if parent and parent.get_root_window():
            window.children[0].disabled = False
