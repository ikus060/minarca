# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import re

from babel.messages.extract import extract_python


def custom_extractor(fileobj, keywords, comment_tags, options):

    # Process file using default python extractor that also include calls to 'Builder.load_string()'
    pattern = re.compile(r'_\(["\'](.*?)["\']\)')
    new_keywords = set(keywords)
    new_keywords.add('load_string')
    for lineno, funcname, message, comments in extract_python(fileobj, new_keywords, comment_tags, options):
        if funcname == 'load_string':
            matches = pattern.findall(message or '')
            for m in matches:
                yield lineno, '_', m, []
        else:
            yield lineno, funcname, message, comments
