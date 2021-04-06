# Minarca Server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
# Targets:
#    
#    test: 		Run the tests for all components.
#
#    build:		Generate distribution packages for all components 
#
# Define the distribution to be build: buster, sid, etc.
SHELL = /bin/sh
DIST ?= $(shell env -i bash -c '. /etc/os-release; echo $$VERSION_CODENAME')

# List package dependencies
SERVER_BUILD_DEPENDS = dh-make dh-virtualenv dh-systemd python3-pip python3-dev python3-setuptools libffi-dev libldap2-dev libsasl2-dev git build-essential lsb-release

#
# == Variables ==
#

# Name few docker images that get reused
ifeq ($(DIST),buster)
DIST_VERSION = 10
else ifeq ($(DIST),bullseye)
DIST_VERSION = 11
endif
IMAGE_PYTHON = ikus060/python:debian${DIST_VERSION}-py3
IMAGE_BUILDPACKAGE = buildpack-deps:${DIST}

# Check if running in gitlab CICD
define docker_run
docker run -i --privileged --rm -v=`pwd`/..:/build/ -w=/build/minarca-server $(1) bash -c "$(2)"
endef

# Version of pacakges base on git tags.
VERSION := $(shell curl -L https://gitlab.com/ikus-soft/maven-scm-version/-/raw/master/version.sh 2>/dev/null | bash -s DEB)

# Release date for Debian pacakge
RELEASE_DATE = $(shell date '+%a, %d %b %Y %H:%M:%S') +0000

# Version specific to debian pacakges
# That include the distribution name
MINARCA_SERVER_DEB_FILE = ../minarca-server_${VERSION}_amd64.deb

UID = $(shell id -u)

#
# == Main targets ==
#

all: test bdist clean

test:
	$(call docker_run,${IMAGE_PYTHON},apt update && apt -y install libldap2-dev libsasl2-dev rdiff-backup --no-install-recommends && PIP_EXTRA_INDEX_URL=https://nexus.ikus-soft.com/repository/pypi-group/simple/ tox)

bdist: ${MINARCA_SERVER_DEB_FILE}

${MINARCA_SERVER_DEB_FILE}: 
	sed "s/%VERSION%/${VERSION}/" debian/changelog.in | sed "s/%DATE%/${RELEASE_DATE}/" > debian/changelog
	$(call docker_run,${IMAGE_BUILDPACKAGE},apt update && apt -y install ${SERVER_BUILD_DEPENDS} --no-install-recommends && PIP_EXTRA_INDEX_URL=https://nexus.ikus-soft.com/repository/pypi-group/simple/ dpkg-buildpackage -us -uc -b && dpkg-buildpackage -Tclean)
	$(call docker_run,${IMAGE_BUILDPACKAGE},chown ${UID} ${MINARCA_SERVER_DEB_FILE})
	rm -f debian/changelog

clean:
	$(call docker_run,${IMAGE_PYTHON},rm -Rf debian/changelog ${MINARCA_SERVER_DEB_FILE} .tox .eggs minarca_server.egg-info .coverage coverage*.xml nosetests*.xml)

version:
	@echo ${VERSION}

.PHONY: all test bdist 

