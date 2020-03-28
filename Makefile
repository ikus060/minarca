# Define the distribution to be build: buster, stretch, sid, etc.
DIST := stretch
PYTHON := python3
CI_PIPELINE_IID := 1
CI_PROJECT_NAME := minarca

#
# == Variables ==
#
VERSION := $(shell curl http://git.patrikdufresne.com/pdsl/maven-scm-version/raw/master/version.sh | bash)

RELEASE_DATE := $(shell date '+%a, %d %b %Y %X') +0000

# Tag of the docker file
ifdef $(DOCKER_REGISTRY)
DOCKER_IMAGE_NAME := ${CI_PROJECT_NAME}-build-${CI_PIPELINE_IID}
else
DOCKER_TAG_BUILDPACKAGE := ${DOCKER_REGISTRY}/pdsl/${CI_PROJECT_NAME}-build-${CI_PIPELINE_IID}
endif

# Version specific to debian pacakges
# That include the distribution name
DEB_VERSION := ${VERSION}+${DIST}

# Build the appropriate TOX env value based
# on python target
ifeq ($(PYTHON), python3)
TOXENV=py3
endif
ifeq ($(PYTHON), python2)
TOXENV=py2
endif

# Check if Authenticate is provided to sign the
# exe in windows build
ifdef $(AUTHENTICODE_CERT)
MAVEN_CLIENT_ARGS := -Dsign.certs.path=authenticode-certs.pem -Dsign.key.path=authenticode.pem -Dsign.passphrase=${AUTHENTICODE_PASSPHRASE}
endif

#
# == Main targets ==
#

all: minarca-server_${DEB_VERSION}_amd64.deb

clean:
	rm -f minarca-server/debian/changelog
	rm -f authenticode-certs.pem
	rm -f authenticode.pem

docker-%: tools/%
	docker build -t ${CI_PROJECT_NAME}-build:$*  $<

#
# == Minarca server ==
#
test-server: docker-${DIST}-${PYTHON}
	docker run \
	    -v=`pwd`:/build \
	    -w=/build/minarca-server \
	    minarca-build:${DIST}-${PYTHON} \
	    tox --sitepackages -e ${TOXENV}

test-quota-api: 
	docker run \
	    -v=`pwd`:/build \
	    -w=/build/minarca-quota-api \
	    minarca-build:${DIST}-${PYTHON} \
	    tox --sitepackages -e ${TOXENV}

minarca-server/debian/changelog:
	sed "s/%VERSION%/${DEB_VERSION}/" minarca-server/debian/changelog.in | sed "s/%DATE%/${RELEASE_DATE}/" > minarca-server/debian/changelog

build-server-deb: minarca-server/debian/changelog docker-${DIST}-buildpackage
	docker run \
		-v=`pwd`:/build \
		-w=/build/minarca-server \
		-e DH_VIRTUALENV_INSTALL_ROOT=/opt/ \
		-e SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION} \
		minarca-build:${DIST}-buildpackage \
		bash -c "dpkg-buildpackage -us -uc && dpkg-buildpackage -Tclean"

#
# == Minarca client ==
#
test-client:
	docker run \
		-v=`pwd`:/build \
		-w=/build/minarca-client \
		minarca-build:${DIST}-java \
		mvn -B -Drevision=${VERSION} clean verify sonar:sonar

package-client: docker-${DIST}-java
ifdef $(AUTHENTICODE_CERT)
	echo "$AUTHENTICODE_CERT" | tr -d '\r' > authenticode-certs.pem
	echo "$AUTHENTICODE_KEY" | tr -d '\r' > authenticode.pem
endif
	docker run \
		-v=`pwd`:/build \
		-w=/build/minarca-client \
		minarca-build:${DIST}-java \
		mvn -B -Drevision=${VERSION} ${MAVEN_CLIENT_ARGS} clean install
	mv minarca-installation-package-deb/target/minarca-installation-package-deb_${REVISION}_all.deb minarca-client_${REVISION}_all.deb
	mv minarca-client/minarca-installation-package/target/minarca-client-${VESRION}.exe minarca-client-${VESRION}.exe 
		
