# Minarca Server

Minarca is a backup software for Windows and Linux to put you in control of
your backups. Minarca eases management of your backups, provides easy recovery
with a rich and powerful web interface.

Minarca Server is a web application to be installed on a centralized backup server.

Minarca Server is written in Python and is released as open source project under the 
GNU GENERAL PUBLIC LICENSE (GPLv3). All source code and documentation are
Copyright Patrik Dufresne Service Logiciel inc.

Minarca Server is actively developed by [Patrik Dufresne](http://patrikdufresne.com)
since April 2015.

The Minarca Server source code is hosted on [self-hosted Gitlab](https://git.patrikdufresne.com/pdsl/minarca-server)
and mirrored to [Github](https://github.com/ikus060/minarca-server).

The Minarca website is http://www.patrikdufresne.com/en/minarca/.

## Download

Minarca Server may be installed on Linux Debian.

* [Latest Linux Ubuntu/Debian version](http://www.patrikdufresne.com/archive/minarca/minarca-server_latest_all.deb)

While it's possible to get Minarca Server working on other Linux distributions, only Debian-based distribution will be officially supported.

# Installation

On a Linux debian server:

    wget http://www.patrikdufresne.com/archive/minarca/minarca-server_latest_all.deb
    apt install minarca-server_latest_all.deb

This should install minarca server and all requried dependencies. The server should be running on http://127.0.0.1:8080 listening on all interfaces.

You may stop start the service using systemd:

    sudo service minarca-server stop
    sudo service minarca-server start


# Configuration

Since Minarca Server is built on top of rdiffweb, you may take a look at [rdiffweb configiuration](https://github.com/ikus060/rdiffweb/).

In addition to rdiffweb cconfiguration, you may also change the following configuration that is specific to Minarca.

## Current Build Status

[![Build Status](https://git.patrikdufresne.com/pdsl/minarca-server/badges/master/pipeline.svg)](https://git.patrikdufresne.com/pdsl/minarca-server/pipelines)

# Support

## Bug Reports

Bug reports should be reported on the Minarca development web site at https://github.com/ikus060/minarca-server/issues

## Professional support

Professional support for Minarca is available by contacting [Patrik Dufresne Service Logiciel](http://www.patrikdufresne.com/en/support/#form).

# Changelog

## v3.11.0 - First public version

 * Support cherrypy v16
 * Provide debian packages
 * Manage SSH Keys for minarca user
 * Provide minarca-shell as an SSH entrypoint
 * Improve SSH server security
 * Add /api/ to be used by minarca-client
 * Update Minarca icon


