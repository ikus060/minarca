FROM buildpack-deps:stretch

RUN apt-get update && \
    apt-get install -y --no-install-recommends python-dev libldap2-dev libsasl2-dev rdiff-backup build-essential curl && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py && \
    pip install virtualenv nose coverage tox --upgrade && \
    rm -rf /var/lib/apt/lists/*

# Needed. Otherwise break python3 encoding.
# see https://bugs.python.org/issue19846
ENV LANG=C.UTF-8
