# Minarca Server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
SHELL = /bin/sh
DIST ?= $(shell env -i bash -c '. /etc/os-release; echo $$VERSION_CODENAME')
PYTHON ?= py3

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

# Check if running in gitlab CICD
define docker_run
docker run --rm -e TOXENV -v=`pwd`/..:/build/ -w=/build/minarca-quota-api $(1) bash -c "$(2)"
endef

COMMA := ,
TOXFACTOR = ${PYTHON}
TOXENV=$(shell $(call docker_run,minarca-server,${IMAGE_PYTHON}, tox --listenvs | grep '${TOXFACTOR}' | tr '\n' '${COMMA}'))

#
# == Main targets ==
#
all: test bdist test-bdist clean

test:
	export TOXENV="${TOXENV}"; \
	$(call docker_run,${IMAGE_PYTHON},tox)

bdist:
	echo "TODO implement distribution package for quota api"

test-bdist:
	echo "TODO implement binary distribution test for quota api"

clean:
	rm -Rf .tox .eggs minarca_quota_api.egg-info .coverage coverage*.xml nosetests*.xml

.PHONY: test bdist test-bdist clean

