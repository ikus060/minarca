#!/bin/sh
# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
set -e 

call() {
    echo -n "$1 "
    shift
    $@ > /dev/null
    if [ $? -eq 0 ]
    then
        echo "OK"
    else
        echo $@
        echo "FAILED"
        exit 1
    fi
}

#
# Check if running as root
#
if ! [ $(id -u) = 0 ]; then
   >&2 echo "Error: This script must be run as root" 
   exit 1
fi

#
# Check linux distribution
#
if [ -f /etc/debian_version ]; then
    DEBIAN=1
    DEBIAN_VERSION=$(cat /etc/debian_version)
    case "$DEBIAN_VERSION" in
    9*)  DEBIAN_DISTRIBUTION=stretch;;
    10*) DEBIAN_DISTRIBUTION=buster;;
    11*) DEBIAN_DISTRIBUTION=bullseye;;
    bullseye*) DEBIAN_DISTRIBUTION=bullseye;;
    *)
      >&2 echo "Error: Debian Linux distribution not supported: $DEBIAN_VERSION"
      exit 1
      ;;
    esac
else
    >&2 echo "Error: Linux distribution not supported."
    exit 1
fi
  
#
# Check bitness
#
case "`uname -m`" in
  x86_64*) BITS=64;;
  *)
    >&2 echo "Error: OS bitness not supported. Only x86_64 is supported." 
    exit 1
    ;;
esac

#
# Parse arguments
#
DEV=0
PACKAGE="${PACKAGE:-minarca-server}"
VERSION="${VERSION:-latest}"
while [ $# -gt 0 ] ; do
  case "$1" in
    -h | --help)
      echo "Usage: get-minarca.sh [--dev] [--package PACKAGE] [--version VERSION]"
      exit 0
      ;;
    -d | --dev) DEV=1;;
    -p | --package)
      shift
      PACKAGE=$1;;
    -V | --version)
      shift
      VERSION=$1;;
    *)
      echo "Option $1 not supported. Ignored." >&2
      exit 1
      ;;
  esac
  shift
done

#
# Configure APT Repo
#
call "Updating repositories..." apt-get update

call "Installing packages for APT..." apt-get install -y apt-transport-https ca-certificates gnupg

echo -n "Installing Public PGP key..."
echo "-----BEGIN PGP PUBLIC KEY BLOCK-----

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
6AGo+q1G2pxg1iRc4nLxadLB0p0=
=EPRn
-----END PGP PUBLIC KEY BLOCK-----" | apt-key add - 

echo "deb https://nexus.ikus-soft.com/repository/apt-release-$DEBIAN_DISTRIBUTION/ $DEBIAN_DISTRIBUTION main" > /etc/apt/sources.list.d/minarca.list
if [ $DEV -eq 1 ]; then
    echo "deb https://nexus.ikus-soft.com/repository/apt-dev-$DEBIAN_DISTRIBUTION/ $DEBIAN_DISTRIBUTION main" >> /etc/apt/sources.list.d/minarca.list
fi

call "Updating repositories again..." apt-get update

if [ "$VERSION" != "latest" ]; then
  PACKAGE="$PACKAGE=$VERSION"
fi
call "Installing $PACKAGE..." apt-get install -y $PACKAGE

echo "Success!"
