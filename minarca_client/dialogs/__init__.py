# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import sys

IS_WINDOWS = sys.platform in ['win32']
IS_LINUX = sys.platform in ['linux', 'linux2']
IS_MAC = sys.platform == 'darwin'

if IS_WINDOWS:
    from ._dialogs_win import *  # noqa
elif IS_LINUX:
    # TODO Should check if Zenity is available
    from ._dialogs_zenity import *  # noqa

    # TODO Should provide a KDE alternative.
elif IS_MAC:
    from ._dialogs_cocoa import *  # noqa
else:
    # TODO provide kivy implementation
    pass
