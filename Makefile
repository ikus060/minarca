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
	MINARCA_VERSION=${MINARCA_VERSION} CLIENT_DIST=buildpack-deps:buster  docker-compose -f ./tests/docker-compose.yml --project-name minarca_test_buster  up --build --abort-on-container-exit --force-recreate
	MINARCA_VERSION=${MINARCA_VERSION} CLIENT_DIST=ikus060/docker-wine-maven:3-jdk-8 docker-compose -f ./tests/docker-compose.yml --project-name minarca_test_win32   up --build --abort-on-container-exit --force-recreate

$(TOPTARGETS): $(SUBDIRS)
$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

.PHONY: $(TOPTARGETS) $(SUBDIRS)

