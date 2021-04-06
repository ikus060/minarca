set -ex
if [ "${MINARCA_CLIENT_DIST}" == "win32" ]; then
    export MINARCA_CLIENT_DIST="ikus060/docker-wine-maven:3-jdk-8"
fi

export MINARCA_SERVER_VERSION=${MINARCA_SERVER_VERSION:-latest}
export MINARCA_CLIENT_VERSION=${MINARCA_CLIENT_VERSION:-latest}
export CLIENT_DIST=${MINARCA_CLIENT_DIST:-debian:buster}
docker-compose -f ./docker-compose.yml --project-name minarca_test_buster up --build --abort-on-container-exit --force-recreate