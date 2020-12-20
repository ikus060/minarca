#!/bin/bash
# Integration test to verify if the server accept link from minarca-client.
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
set -e
set -x

# Default variables
MINARCA_REMOTE_URL=${MINARCA_REMOTE_URL:-http://localhost:8080}
MINARCA_USERNAME=${MINARCA_USERNAME:-admin}
MINARCA_PASSWORD=${MINARCA_PASSWORD:-admin123}
MINARCA_REPOSITORYNAME=${MINARCA_REPOSITORYNAME:-docker-$HOSTNAME}

if [ -z "$WINEPREFIX" ]; then

    # Install minarca client (For Linux)
    curl --fail -L https://www.ikus-soft.com/archive/minarca/get-minarca.sh -o /tmp/get-minarca.sh
    bash /tmp/get-minarca.sh --dev --package minarca-client --version "$MINARCA_VERSION"
    minarca --version
    
    # Link minarca
    minarca link --remoteurl $MINARCA_REMOTE_URL --username $MINARCA_USERNAME --password $MINARCA_PASSWORD --name $MINARCA_REPOSITORYNAME
    
    # Include files in backup
    minarca include /etc /var /home
    
    # Backup
    minarca backup --force

else
  
    # Install minarca client (For Windows)
    MINARCA_INSTALL_FILE=minarca-client_${MINARCA_VERSION}.exe
    if [ "${MINARCA_VERSION}" = "latest" ]; then
        MINARCA_INSTALL_FILE=minarca-latest-install.exe;
    fi
    curl --fail -L https://www.ikus-soft.com/archive/minarca/${MINARCA_INSTALL_FILE} -o /tmp/minarca-install.exe
    export DISPLAY=:1
    (Xvfb :1 -screen 0 1280x960x24 &)
    (wine /tmp/minarca-install.exe /S || true)
    echo '#!/bin/bash' > /usr/bin/minarca
    echo 'wine "C:\\users\\root\\Local Settings\\Application Data\\minarca\\bin\\minarca.exe" "$@"' >> /usr/bin/minarca
    chmod +x /usr/bin/minarca
    minarca --version

fi
