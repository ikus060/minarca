FROM openjdk:8-jdk-buster

RUN apt-get update && \
    apt-get -qq install osslsigncode icoutils nsis cron gettext maven curl make && \
    rm -rf /var/lib/apt/lists/*

# Needed. Otherwise break python3 encoding.
# see https://bugs.python.org/issue19846
ENV LANG=C.UTF-8
