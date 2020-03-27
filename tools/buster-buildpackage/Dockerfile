FROM buildpack-deps:buster

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        dh-make dh-virtualenv dh-systemd \
        python3-pip python3-dev python3-setuptools \
        libffi-dev libldap2-dev libsasl2-dev \
        git build-essential lsb-release && \
    rm -rf /var/lib/apt/lists/*

# Needed. Otherwise break python3 encoding.
# see https://bugs.python.org/issue19846
ENV LANG=C.UTF-8
