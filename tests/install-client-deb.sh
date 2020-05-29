#!/bin/bash
# Integration test to verify if deb can be installed.
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
set -e
set -x

apt update
apt install -y ./$MINARCA_DEB_FILE
/opt/minarca/bin/minarca --version