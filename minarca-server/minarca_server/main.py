# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import rdiffweb.main

from minarca_server.app import MinarcaApplication


def main(args=None):
    rdiffweb.main.main(args, app_class=MinarcaApplication)


if __name__ == "__main__":
    main()
