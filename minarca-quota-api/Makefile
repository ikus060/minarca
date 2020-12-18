# Minarca Server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
SHELL = /bin/sh
DIST ?= $(shell env -i bash -c '. /etc/os-release; echo $$VERSION_CODENAME')

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
IMAGE_PYTHON = ikus060/python:debian${DIST_VERSION}-py3
IMAGE_BUILDPACKAGE = buildpack-deps:${DIST}

# Check if running in gitlab CICD
define docker_run
docker run -i --rm -v=`pwd`/..:/build/ -w=/build/minarca-quota-api $(1) bash -c "$(2)"
endef

# Version of pacakges base on git tags.
VERSION := $(shell curl -L https://gitlab.com/ikus-soft/maven-scm-version/-/raw/master/version.sh 2>/dev/null | bash -s DEB)

# Release date for Debian pacakge
RELEASE_DATE = $(shell date '+%a, %d %b %Y %H:%M:%S') +0000

MINARCA_QUOTA_API_DEB_FILE = ../minarca-quota-api_${VERSION}_amd64.deb

UID = $(shell id -u)

#
# == Main targets ==
#
all: test bdist clean

test:
	$(call docker_run,${IMAGE_PYTHON},tox)

bdist: ${MINARCA_QUOTA_API_DEB_FILE}

${MINARCA_QUOTA_API_DEB_FILE}: 
	sed "s/%VERSION%/${VERSION}/" debian/changelog.in | sed "s/%DATE%/${RELEASE_DATE}/" > debian/changelog
	$(call docker_run,${IMAGE_BUILDPACKAGE}, apt update && apt install -y devscripts && apt build-dep -y . && dpkg-buildpackage -b && dpkg-buildpackage -Tclean)
	$(call docker_run,${IMAGE_BUILDPACKAGE},chown ${UID} ${MINARCA_QUOTA_API_DEB_FILE})
	rm -f debian/changelog

clean:
	$(call docker_run,${IMAGE_PYTHON},rm -Rf .tox .eggs minarca_quota_api.egg-info .coverage coverage*.xml nosetests*.xml)


.PHONY: test bdist clean

