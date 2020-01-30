#!/bin/bash
# Integration test to verify if the server accept link from minarca-client.
#
# Copyright (C) 2019 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
set -e
set -x

# Default variables
MINARCA_REMOTE_URL=${MINARCA_REMOTE_URL:-https://test.minarca.net}
MINARCA_USERNAME=${MINARCA_USERNAME:-admin}
MINARCA_PASSWORD=${MINARCA_PASSWORD:-admin123}
MINARCA_REPOSITORYNAME=${MINARCA_REPOSITORYNAME:-test}

# Link minarca
minarca link --remoteurl $MINARCA_REMOTE_URL --username $MINARCA_USERNAME --password $MINARCA_PASSWORD --name $MINARCA_REPOSITORYNAME
