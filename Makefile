# Minarca Server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
TOPTARGETS := all test bdist clean

SUBDIRS := $(subst /Makefile,,$(wildcard */Makefile))

MINARCA_VERSION ?= latest

integration-tests:
	MINARCA_VERSION=${MINARCA_VERSION} SERVER_DIST=buster CLIENT_DIST=stretch docker-compose -f ./tests/docker-compose.deb.yml   --project-name buster_stretch up --build --abort-on-container-exit --force-recreate
	MINARCA_VERSION=${MINARCA_VERSION} SERVER_DIST=buster CLIENT_DIST=buster  docker-compose -f ./tests/docker-compose.deb.yml   --project-name buster_buster  up --build --abort-on-container-exit --force-recreate
	MINARCA_VERSION=${MINARCA_VERSION} SERVER_DIST=buster                     docker-compose -f ./tests/docker-compose.win32.yml --project-name buster_win32   up --build --abort-on-container-exit --force-recreate

$(TOPTARGETS): $(SUBDIRS)
$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

.PHONY: $(TOPTARGETS) $(SUBDIRS)

