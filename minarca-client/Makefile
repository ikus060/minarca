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

# List package dependencies
CLIENT_DEPENDS = osslsigncode icoutils nsis cron gettext

#
# == Variables ==
#

# Define java/maven image to be used
IMAGE_JAVA = maven:3-jdk-8
IMAGE_DEBIAN = buildpack-deps:${DIST}
IMAGE_WINDOWS = ikus060/docker-wine-maven:3-jdk-8

# Check if running in gitlab CICD
define docker_run
docker run -i --rm -e TOXENV -v=`pwd`/..:/build/ -w=/build/minarca-client $(1) bash -c "$(2)"
endef

# Version of pacakges base on git tags.
VERSION := $(shell curl -L https://gitlab.com/ikus-soft/maven-scm-version/-/raw/master/version.sh 2>/dev/null | bash)

MINARCA_CLIENT_DEB_FILE = ../minarca-client_${VERSION}_all.deb
MINARCA_CLIENT_EXE_FILE = ../minarca-client_${VERSION}.exe

MAVEN_ARGS=-Drevision=${VERSION} -Duser.home=/tmp
ifneq ($(SONAR_URL),)
MAVEN_TEST_ARGS=-Dsonar.host.url=${SONAR_URL} -Dsonar.login=${SONAR_TOKEN} org.jacoco:jacoco-maven-plugin:prepare-agent install sonar:sonar
else
MAVEN_TEST_ARGS=org.jacoco:jacoco-maven-plugin:prepare-agent install org.jacoco:jacoco-maven-plugin:report
endif

ifdef AUTHENTICODE_CERT
MAVEN_BUILD_ARGS = -Dsign.certs.path=authenticode-certs.pem -Dsign.key.path=authenticode.pem -Dsign.passphrase=${AUTHENTICODE_PASSPHRASE}
endif

UID = $(shell id -u)

#
# == Main targets ==
#

all: test bdist test-bdist clean

test:
	$(call docker_run,${IMAGE_JAVA},apt update && apt -y install ${CLIENT_DEPENDS} --no-install-recommends && mvn ${MAVEN_ARGS} ${MAVEN_TEST_ARGS})

bdist: ${MINARCA_CLIENT_DEB_FILE} ${MINARCA_CLIENT_EXE_FILE}

${MINARCA_CLIENT_DEB_FILE} ${MINARCA_CLIENT_EXE_FILE}:
ifdef AUTHENTICODE_CERT
	echo "$${AUTHENTICODE_CERT}" > authenticode-certs.pem
	echo "$${AUTHENTICODE_KEY}" > authenticode.pem
endif
	$(call docker_run,${IMAGE_JAVA},apt update && apt -y install ${CLIENT_DEPENDS} --no-install-recommends && mvn ${MAVEN_ARGS} ${MAVEN_BUILD_ARGS} clean install -DskipTests=true)
	$(call docker_run,${IMAGE_JAVA},mv -f ./minarca-installation-package-deb/target/minarca-installation-package-deb_*_all.deb ${MINARCA_CLIENT_DEB_FILE})
	$(call docker_run,${IMAGE_JAVA},mv -f ./minarca-installation-package/target/minarca-client-*.exe ${MINARCA_CLIENT_EXE_FILE})
	$(call docker_run,${IMAGE_JAVA},chown ${UID} ${MINARCA_CLIENT_EXE_FILE} ${MINARCA_CLIENT_DEB_FILE})

test-bdist: test-bdist-deb test-bdist-exe

test-bdist-deb: ${MINARCA_CLIENT_DEB_FILE}
	$(call docker_run,${IMAGE_DEBIAN},bash ./tests/install-client-deb.sh ${MINARCA_CLIENT_DEB_FILE})

test-bdist-exe: ${MINARCA_CLIENT_EXE_FILE}
	$(call docker_run,${IMAGE_WINDOWS},bash ./tests/install-client-win.sh ${MINARCA_CLIENT_EXE_FILE})

gettext:
	$(call docker_run,${IMAGE_JAVA},cd minarca-core && mvn ${MAVEN_ARGS} gettext:gettext)
	$(call docker_run,${IMAGE_JAVA},cd minarca-core && mvn ${MAVEN_ARGS} gettext:merge)
	$(call docker_run,${IMAGE_JAVA},cd minarca-ui && mvn ${MAVEN_ARGS} gettext:gettext)
	$(call docker_run,${IMAGE_JAVA},cd minarca-ui && mvn ${MAVEN_ARGS} gettext:merge)

clean:
	$(call docker_run,${IMAGE_JAVA},mvn ${MAVEN_ARGS} clean)
	rm -f authenticode-certs.pem
	rm -f authenticode.pem

.PHONY: all test bdist test-bdist test-bdist-deb test-bdist-exe gettext clean

