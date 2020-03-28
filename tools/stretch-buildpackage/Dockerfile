FROM buildpack-deps:stretch

RUN apt-get update && \
    apt-get install -y dh-make dh-virtualenv dh-systemd \
        python3 python3-pip python3-dev python3-setuptools python3-setuptools-scm \
        libffi-dev libldap2-dev libsasl2-dev \
        git build-essential && \
    rm -rf /var/lib/apt/lists/*
    
# Needed. Otherwise break python3 encoding.
# see https://bugs.python.org/issue19846
ENV LANG=C.UTF-8
