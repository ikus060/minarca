# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
# Pick the best matching and available dialog provided.

import os
import shutil

ZENITY = shutil.which("zenity")
KDIALOG = shutil.which("kdialog")
DESKTOP = os.environ.get("XDG_CURRENT_DESKTOP", os.environ.get("DESKTOP_SESSION", None))

desktop = None

if DESKTOP in ['kde', 'trinity'] and KDIALOG:
    from ._dialogs_linux_kdialog import (  # noqa
        error_dialog,
        file_dialog,
        folder_dialog,
        info_dialog,
        question_dialog,
        warning_dialog,
    )
else:
    # Fall back to zenity.
    from ._dialogs_linux_zenity import (  # noqa
        error_dialog,
        file_dialog,
        folder_dialog,
        info_dialog,
        question_dialog,
        warning_dialog,
    )
