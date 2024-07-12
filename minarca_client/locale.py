# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.


__all__ = ['_', 'gettext', 'ngettext']

import gettext as _gt
import locale
import os
import sys
from importlib.resources import files

# On MacOS, we need to get the language using native API. Because the LANG
# environment variable is not pass to the application bundle.
languages = None
if sys.platform == 'darwin':
    try:
        import Foundation

        sud = Foundation.NSUserDefaults.standardUserDefaults()  # @UndefinedVariable
        languages = [str(sud.stringForKey_('AppleLocale'))]
    except ImportError:
        pass
elif sys.platform == 'win32':
    try:
        import ctypes

        windll = ctypes.windll.kernel32
        languages = [locale.windows_locale[windll.GetUserDefaultUILanguage()]]
        # For testing we support environment variable too
        if os.environ.get('LANGUAGE', None):
            languages.insert(0, os.environ.get('LANGUAGE'))
    except ImportError:
        pass

# Load translations
localedir = files(__package__) / 'locales'
try:
    t = _gt.translation('messages', localedir, languages=languages)
except OSError:
    t = _gt.NullTranslations()

_ = gettext = t.gettext
ngettext = t.ngettext
