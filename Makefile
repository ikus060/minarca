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
CLIENT_DEPENDS = osslsigncode icoutils nsis cron gettext
SERVER_DEPENDS = libldap2-dev libsasl2-dev rdiff-backup
SERVER_BUILD_DEPENDS = dh-make dh-virtualenv dh-systemd python3-pip python3-dev python3-setuptools libffi-dev libldap2-dev libsasl2-dev git build-essential lsb-release
QUOTA_DEPENDS = 

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

# Define java/maven image to be used
ifeq ($(DIST),windows)
IMAGE_JAVA = ikus060/docker-wine-maven:3-jdk-8
else
IMAGE_JAVA = maven:3-jdk-8
endif

IMAGE_BUILDPACKAGE = buildpack-deps:${DIST}
IMAGE_DEBIAN = buildpack-deps:${DIST}

# Check if running in gitlab CICD
define docker_run
docker run --rm -e TOXENV -v=`pwd`:/build -w=/build/$(1) $(2) bash -c "$(3)"
endef

# Version of pacakges base on git tags.
VERSION := $(shell curl -L https://gitlab.com/ikus-soft/maven-scm-version/-/raw/master/version.sh 2>/dev/null | bash)

# Release date for Debian pacakge
RELEASE_DATE = $(shell date '+%a, %d %b %Y %X') +0000

# Version specific to debian pacakges
# That include the distribution name
DEB_VERSION = ${VERSION}+${DIST}

#
# == Main targets ==
#

all: test build

test: test-server test-quota-api test-client

build: build-client build-server

clean:
	rm -f minarca-server/debian/changelog
	rm -f authenticode-certs.pem
	rm -f authenticode.pem
	$(call docker_run,minarca-server,${DIST}-buildpackage,dpkg-buildpackage -Tclean)

version:
	@echo "${VERSION}"
	
debfile:
	@echo "${MINARCA_SERVER_DEB_FILE}"

.PHONY: all test build  test-server test-quota-api test-client test-client-deb test-client-exe build-client build-server

#
# == Tox ==
#
COMMA := ,
TOXFACTOR = ${PYTHON}
TOXENV=$(shell $(call docker_run,minarca-server,${IMAGE_PYTHON}, tox --listenvs | grep '${TOXFACTOR}' | tr '\n' '${COMMA}'))

test-server:
	export TOXENV="${TOXENV}"; \
	#$(call docker_run,minarca-server,${IMAGE_PYTHON},apt update && apt -y install ${SERVER_DEPENDS} && tox)

test-quota-api: 
	export TOXENV="${TOXENV}"; \
	$(call docker_run,minarca-quota-api,${IMAGE_PYTHON},tox)
	
#
# == Client ==
#
MINARCA_CLIENT_DEB_FILE = minarca-client_${VERSION}_all.deb
MINARCA_CLIENT_EXE_FILE = minarca-client_${VERSION}.exe

MAVEN_ARGS=-Drevision=${VERSION} -Duser.home=/tmp
ifneq ($(SONAR_URL),)
MAVEN_TEST_ARGS=-Dsonar.host.url=${SONAR_URL} -Dsonar.login=${SONAR_TOKEN} org.jacoco:jacoco-maven-plugin:prepare-agent install sonar:sonar
else
MAVEN_TEST_ARGS=org.jacoco:jacoco-maven-plugin:prepare-agent install org.jacoco:jacoco-maven-plugin:report
endif
	
test-client: 
	$(call docker_run,minarca-client,${IMAGE_JAVA},apt update && apt -y install ${CLIENT_DEPENDS} && mvn ${MAVEN_ARGS} ${MAVEN_TEST_ARGS})
	
# Check if Authenticate is provided to sign the
# exe in windows build
ifdef AUTHENTICODE_CERT
MAVEN_BUILD_ARGS = -Dsign.certs.path=authenticode-certs.pem -Dsign.key.path=authenticode.pem -Dsign.passphrase=${AUTHENTICODE_PASSPHRASE}
endif
	
build-client: 
ifdef AUTHENTICODE_CERT
	echo "$${AUTHENTICODE_CERT}" > minarca-client/authenticode-certs.pem
	echo "$${AUTHENTICODE_KEY}" > minarca-client/authenticode.pem
endif
	$(call docker_run,minarca-client,${IMAGE_JAVA},apt update && apt -y install ${CLIENT_DEPENDS} && mvn ${MAVEN_ARGS} ${MAVEN_BUILD_ARGS} clean install)
	$(call docker_run,.,${IMAGE_JAVA},mv minarca-client/minarca-installation-package-deb/target/minarca-installation-package-deb_*_all.deb ${MINARCA_CLIENT_DEB_FILE})
	$(call docker_run,.,${IMAGE_JAVA},mv minarca-client/minarca-installation-package/target/minarca-client-*.exe ${MINARCA_CLIENT_EXE_FILE})

${MINARCA_CLIENT_DEB_FILE}: build-client
${MINARCA_CLIENT_EXE_FILE}: build-client

test-client-deb: ${MINARCA_CLIENT_DEB_FILE}
	$(call docker_run,.,${IMAGE_DEBIAN},bash ./tests/install-server-deb.sh ${MINARCA_SERVER_DEB_FILE})

test-client-exe: ${MINARCA_CLIENT_EXE_FILE}
	$(call docker_run,.,${IMAGE_WINDOWS},bash ./tests/install-server-deb.sh ${MINARCA_SERVER_DEB_FILE})

#
# == Server ==
#
MINARCA_SERVER_DEB_FILE = minarca-server_${DEB_VERSION}_amd64.deb

${MINARCA_SERVER_DEB_FILE}: 
	sed "s/%VERSION%/${VERSION}/" minarca-server/debian/changelog.in | sed "s/%DATE%/${RELEASE_DATE}/" > minarca-server/debian/changelog
	$(call docker_run,minarca-server,${IMAGE_BUILDPACKAGE},apt update && apt -y install ${SERVER_BUILD_DEPENDS} && dpkg-buildpackage -us -uc -b)
	mv minarca-server_${VERSION}_amd64.deb minarca-server_${DEB_VERSION}_amd64.deb

build-server: ${MINARCA_SERVER_DEB_FILE}


#
# == Translation ==
#
gettext: gettext-client

gettext-client:
	$(call docker_run,minarca-client/minarca-core,${IMAGE_JAVA},mvn ${MAVEN_ARGS} gettext:gettext)
	$(call docker_run,minarca-client/minarca-core,${IMAGE_JAVA},mvn ${MAVEN_ARGS} gettext:merge)
	$(call docker_run,minarca-client/minarca-ui,${IMAGE_JAVA},mvn ${MAVEN_ARGS} gettext:gettext)
	$(call docker_run,minarca-client/minarca-ui,${IMAGE_JAVA},mvn ${MAVEN_ARGS} gettext:merge)

