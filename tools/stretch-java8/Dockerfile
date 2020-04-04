FROM buildpack-deps:stretch

RUN apt-get update && \
    apt-get -qq install osslsigncode icoutils nsis cron gettext maven curl openjdk-8-jdk-headless && \
    rm /etc/java-8-openjdk/accessibility.properties && \
    rm -rf /var/lib/apt/lists/*

# Needed. Otherwise break python3 encoding.
# see https://bugs.python.org/issue19846
ENV LANG=C.UTF-8
