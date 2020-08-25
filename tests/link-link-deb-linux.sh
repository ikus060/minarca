#!/bin/bash
# Integration test to verify if the server accept link from minarca-client.
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
set -e
set -x

# Default variables
MINARCA_DEB_FILE=${MINARCA_DEB_FILE:-./minarca-client_latest_all.deb}
MINARCA_REMOTE_URL=${MINARCA_REMOTE_URL:-https://test.minarca.net}
MINARCA_USERNAME=${MINARCA_USERNAME:-admin}
MINARCA_PASSWORD=${MINARCA_PASSWORD:-admin123}
MINARCA_REPOSITORYNAME=${MINARCA_REPOSITORYNAME:-test}


# Install minarca-client
if [ ! -e "$MINARCA_DEB_FILE" ]; then
    apt update && apt install -y wget
    wget -O $MINARCA_DEB_FILE https://www.ikus-soft.com/archive/minarca/${MINARCA_DEB_FILE##*/}
fi
apt update && apt install -y $MINARCA_DEB_FILE

# Link minarca
/opt/minarca/bin/minarca link --remoteurl $MINARCA_REMOTE_URL --username $MINARCA_USERNAME --password $MINARCA_PASSWORD --name $MINARCA_REPOSITORYNAME
