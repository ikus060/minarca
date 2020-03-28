# Define the distribution to be build: buster, stretch, sid, etc.
DIST := stretch

CI_JOB_NAME := local
CI_PIPELINE_IID := 1
CI_PROJECT_NAME := minarca


#
# == Variables ==
#
BUILD_PATH:=prebuild/${CI_JOB_NAME}
TAG:=prebuild:${CI_JOB_NAME}-$CI_PIPELINE_IID

PYTHON := python3

VERSION := $(shell python3 minarca-server/setup.py --version)

RELEASE_DATE := $(shell date '+%a, %d %b %Y %X') +0000

# Tag of the docker file
ifdef $(DOCKER_REGISTRY)
DOCKER_IMAGE_NAME := ${CI_PROJECT_NAME}-build
else
DOCKER_TAG_BUILDPACKAGE := ${DOCKER_REGISTRY}/pdsl/${CI_PROJECT_NAME}-build
endif

# Version specific to debian pacakges
# That include the distribution name
DEB_VERSION := ${VERSION}+${DIST}

ifeq ($(PYTHON), python3)
TOXENV=py3
endif
ifeq ($(PYTHON), python2)
TOXENV=py2
endif

#
# == Main targets ==
#

all: minarca-server_${DEB_VERSION}_amd64.deb

clean:
	rm -f minarca-server/debian/changelog

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

minarca-server/debian/changelog:
	sed "s/%VERSION%/$DEB_VERSION}/" minarca-server/debian/changelog.in | sed "s/%DATE%/${RELEASE_DATE}/" > minarca-server/debian/changelog

minarca-server_${DEB_VERSION}_amd64.deb: minarca-server/debian/changelog docker-${DIST}-buildpackage
	docker run \
		-v=`pwd`:/build \
		-w=/build/minarca-server \
		-e DH_VIRTUALENV_INSTALL_ROOT=/opt/ \
		-e SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION} \
		minarca-build:${DIST}-buildpackage \
		dpkg-buildpackage -us -uc

#
# == Minarca client ==
#

