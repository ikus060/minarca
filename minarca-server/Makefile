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
# Define the distribution to be build: buster, stretch, sid, etc.
SHELL = /bin/sh
DIST ?= $(shell env -i bash -c '. /etc/os-release; echo $$VERSION_CODENAME')
PYTHON ?= py3

# List package dependencies
SERVER_DEPENDS = libldap2-dev libsasl2-dev rdiff-backup
SERVER_BUILD_DEPENDS = dh-make dh-virtualenv dh-systemd python3-pip python3-dev python3-setuptools libffi-dev libldap2-dev libsasl2-dev git build-essential lsb-release

#
# == Variables ==
#

# Name few docker images that get reused
ifeq ($(DIST),stretch)
DIST_VERSION = 9
else ifeq ($(DIST),buster)
DIST_VERSION = 10
else ifeq ($(DIST),bullseye)
DIST_VERSION = 11
endif
IMAGE_PYTHON = ikus060/python:debian${DIST_VERSION}-${PYTHON}

IMAGE_BUILDPACKAGE = buildpack-deps:${DIST}

# Check if running in gitlab CICD
define docker_run
docker run -i --rm -e TOXENV -v=`pwd`/..:/build/ -w=/build/minarca-server $(1) bash -c "$(2)"
endef

# Version of pacakges base on git tags.
VERSION := $(shell curl -L https://gitlab.com/ikus-soft/maven-scm-version/-/raw/master/version.sh 2>/dev/null | bash)

# Release date for Debian pacakge
RELEASE_DATE = $(shell date '+%a, %d %b %Y %H:%M:%S') +0000

# Version specific to debian pacakges
# That include the distribution name
DEB_VERSION = ${VERSION}+${DIST}

MINARCA_SERVER_DEB_FILE = ../minarca-server_${DEB_VERSION}_amd64.deb

COMMA := ,
TOXFACTOR = ${PYTHON}
TOXENV=$(shell $(call docker_run,${IMAGE_PYTHON}, tox --listenvs | grep '${TOXFACTOR}' | tr '\n' '${COMMA}'))

UID = $(shell id -u)

#
# == Main targets ==
#

all: test bdist test-bdist

test:
	export TOXENV="${TOXENV}"; \
	$(call docker_run,${IMAGE_PYTHON},apt update && apt -y install ${SERVER_DEPENDS} --no-install-recommends && tox)

bdist: ${MINARCA_SERVER_DEB_FILE}

${MINARCA_SERVER_DEB_FILE}: 
	sed "s/%VERSION%/${VERSION}/" debian/changelog.in | sed "s/%DATE%/${RELEASE_DATE}/" > debian/changelog
	$(call docker_run,${IMAGE_BUILDPACKAGE},apt update && apt -y install ${SERVER_BUILD_DEPENDS} --no-install-recommends && dpkg-buildpackage -us -uc -b && dpkg-buildpackage -Tclean)
	$(call docker_run,${IMAGE_BUILDPACKAGE},chown ${UID} ../minarca-server_${VERSION}_amd64.deb)
	mv -f ../minarca-server_${VERSION}_amd64.deb ${MINARCA_SERVER_DEB_FILE}
	rm -f debian/changelog

test-bdist: ${MINARCA_SERVER_DEB_FILE}
	$(call docker_run,${IMAGE_BUILDPACKAGE},bash ./tests/install-server-deb.sh ${MINARCA_SERVER_DEB_FILE})

clean:
	$(call docker_run,${IMAGE_PYTHON},rm -Rf debian/changelog ${MINARCA_SERVER_DEB_FILE} .tox .eggs minarca_server.egg-info .coverage coverage*.xml nosetests*.xml)

version:
	@echo ${VERSION}

.PHONY: all test bdist 

