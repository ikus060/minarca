![Minarca Logo](doc/resources/banner.png)

<p align="center">
  <strong>
    <a href="http://www.patrikdufresne.com/en/minarca/">website</a>
    •
    <a href="https://github.com/ikus060/minarca-server/blob/master/doc/index.md">docs</a>
    •
    <a href="https://groups.google.com/forum/#!forum/rdiffweb">community</a>
  </strong>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/ikus060/minarca-server"></a>
  <a href="https://github.com/ikus060/minarca-server/blob/master/doc/index.md"><img alt="Documentation" src="https://img.shields.io/badge/code-documented-brightgreen.svg?style=flat-square"></a>
  <a href="https://git.patrikdufresne.com/pdsl/minarca-server/pipelines"><img alt="Build" src="https://git.patrikdufresne.com/pdsl/minarca-server/badges/master/pipeline.svg"></a>
</p>

<h1 align="center">
  Welcome to Minarca Backup Software!
</h1>

Minarca is a **free and open-source** backup software providing end-to-end integration to put you in control of your backup strategy. This **Self-Hosted** software may suit the needs of service providers or small business. 

**Simple** to install, to configure and to manage, Minarca will not waste your time. Minarca makes user data easily accessible by providing a rich **web interface** to recover the files.

**Minarca client** may be used to simplify the integration of new computers running **Windows or Linux Debian**. It's user interface and command line interface allow simple usage for **desktop users or headless servers**. Minarca also keep interoperability with legacy installation of rdiff-backup.

## Getting started

Minarca Server may be installed on Linux Debian.

* [Latest Ubuntu/Debian Linux version](http://www.patrikdufresne.com/archive/minarca/minarca-server_latest_all.deb)

While it's possible to get Minarca Server working on other Linux distributions, only Debian-based distribution is officially supported.

# Support

## Bug Reports

Bug reports should be reported on the Minarca development web site at https://github.com/ikus060/minarca-server/issues

## Professional support

Professional support for Minarca is available by contacting [Patrik Dufresne Service Logiciel](http://www.patrikdufresne.com/en/support/#form).

# About Minarca

Minarca Server is written in Python and is released as open source project under the 
GNU AFFERO GENERAL PUBLIC LICENSE (AGPLv3). All source code and documentation are
Copyright Patrik Dufresne Service Logiciel inc. <info@patrikdufresne.com>

Minarca Server is actively developed by [Patrik Dufresne](http://patrikdufresne.com)
since April 2015.

The Minarca Server source code is hosted on [private Gitlab](https://git.patrikdufresne.com/pdsl/minarca-server)
and mirrored to [Github](https://github.com/ikus060/minarca-server).

The Minarca website is http://www.patrikdufresne.com/en/minarca/.

# Changelog

## v3.0.1 - Bug fixes (2019-10-04)

 * Upgrade to rdiffweb v1.0.3.
 * Update the authorized_keys when user's home directory get updated.
 * Force user's home directory owner and group. Allow minarca web interface to run as root.
 * Minarca-shell: Fix repository name validation.
 * Minarca-shell: Add SUDO_OWNERSHIP to sets the owner and group. Allow better quota management.
 * Pipeline: Add integration testing with server and client linking.

## v3.0.0 - First public version (2019-09-14)

 * Support cherrypy v16
 * Provide debian packages
 * Manage SSH Keys for minarca user
 * Provide minarca-shell as an SSH entrypoint
 * Improve SSH server security
 * Add /api/ to be used by minarca-client
 * Update Minarca icon
