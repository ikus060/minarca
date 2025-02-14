# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import sys

IS_WINDOWS = sys.platform in ['win32']
IS_LINUX = sys.platform in ['linux', 'linux2']
IS_MAC = sys.platform == 'darwin'

if IS_WINDOWS:
    from ._dialogs_win import (  # noqa
        error_dialog,
        file_dialog,
        folder_dialog,
        info_dialog,
        question_dialog,
        username_password_dialog,
        warning_dialog,
    )
elif IS_LINUX:
    from ._dialogs_linux import (  # noqa
        error_dialog,
        file_dialog,
        folder_dialog,
        info_dialog,
        question_dialog,
        warning_dialog,
    )
elif IS_MAC:
    from ._dialogs_cocoa import (  # noqa
        error_dialog,
        file_dialog,
        folder_dialog,
        info_dialog,
        question_dialog,
        warning_dialog,
    )
