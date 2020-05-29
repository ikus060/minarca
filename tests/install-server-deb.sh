#!/bin/bash
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
set -e
set -x

# Install webserver package=
apt-get update && apt-get install -y curl
apt install -y "./$1"

# Start minarca
su -c "/opt/minarca/bin/rdiffweb --config=/etc/minarca/minarca-server.conf" minarca &

# Sleep a bit to let the service start
sleep 5

# Query website 
curl -v http://localhost:8080 | grep 'Minarca'