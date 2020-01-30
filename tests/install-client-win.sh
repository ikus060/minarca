#!/bin/bash
# Integration test to verify installation of exe in wine
#
# Copyright (C) 2019 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
set -e
set -x

# Download the client
MINARCA_EXE_FILE=${MINARCA_EXE_FILE:-./minarca-latest-install.exe}
if [ ! -e "$MINARCA_EXE_FILE" ]; then
    apt update && apt install -y wget
    wget -O $MINARCA_EXE_FILE http://www.patrikdufresne.com/archive/minarca/${MINARCA_EXE_FILE##*/}
fi

# Install wine
dpkg --add-architecture i386
apt update
apt install -y --no-install-recommends wine wine32 xauth winbind cabextract wget xvfb ca-certificates

export WINEARCH=win32
export WINEDEBUG=fixme-all

# Install minarca exe in wine
export DISPLAY=:1
Xvfb :1 -screen 0 1280x960x24 &
wine ./$MINARCA_EXE_FILE /S

# Add wine shortcut
echo 'wine "C:\\users\\root\\Local Settings\\Application Data\\minarca\\bin\\minarca.exe" "$@"' > /usr/bin/minarca
chmod +x /usr/bin/minarca

# Show version
minarca --version
