#!/bin/bash
# Integration test to verify installation of exe in wine
#
# Copyright (C) 2019 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
set -e
set -x

# Install wine
dpkg --add-architecture i386
apt update
apt install -y --no-install-recommends wine wine32 xauth winbind cabextract wget xvfb ca-certificates
wget -nv -O /usr/local/bin/winetricks 'https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks' 
chmod +x /usr/local/bin/winetricks

export WINEARCH=win32
export WINEDEBUG=fixme-all

# Install minarca exe in wine
Xvfb :1 -screen 0 1280x960x24 &
DISPLAY=:1 wine ./$MINARCA_EXE_FILE /S

# Show version
wine "C:\users\root\Local Settings\Application Data\minarca\bin\minarca.exe" --version
