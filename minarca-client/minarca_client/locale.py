# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

__all__ = ['_', 'gettext', 'ngettext']

import pkg_resources
import gettext as _gt
localedir = pkg_resources.resource_filename(__name__, 'locales')
try:
    t = _gt.translation('messages', localedir)
except OSError:
    t = _gt.NullTranslations()

_ = gettext = t.gettext
ngettext = t.ngettext
