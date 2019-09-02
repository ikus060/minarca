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

## Current Build Status

[![Build Status](https://git.patrikdufresne.com/pdsl/minarca-server/badges/master/pipeline.svg)](https://git.patrikdufresne.com/pdsl/minarca-server/pipelines)

## Download

Minarca Server may be installed on Linux Debian.

* [Latest Ubuntu/Debian Linux version](http://www.patrikdufresne.com/archive/minarca/minarca-server_latest_all.deb)

While it's possible to get Minarca Server working on other Linux distributions, only Debian-based distribution is officially supported.

# Installation

On a Debian Linux server:

    wget http://www.patrikdufresne.com/archive/minarca/minarca-server_latest_all.deb
    apt install minarca-server_latest_all.deb

This should install Minarca server and all required dependencies. The server should be running on http://127.0.0.1:8080 listening on all interfaces.

You may stop start the service using systemd:

    sudo service minarca-server stop
    sudo service minarca-server start


# Configuration

Since Minarca Server is built on top of rdiffweb, you may take a look at [rdiffweb configiuration](https://github.com/ikus060/rdiffweb/).

You may also change Minarca's configuration in `/etc/minarca/minarca-server.conf`:

| Parameter | Description | Required | Example |
| --- | --- | --- | --- |
| MinarcaQuotaApiUrl | URL to a minarca-quota-api service to be used to get/set user's quota. | No | http://minarca:secret@localhost:8081/ | 
| MinarcaUserSetupDirMode | Permission to be set on the user's folder created by Minarca. (Default: 0700) | No | 0o0700 |
| MinarcaUserBaseDir | Folder where users repositories should be created. You may need to change this value if you already have your repositories created in a different location or if you are migrating from rdiffweb. Otherwise it's recommended to keep the default value. (Default: /var/opt/minarca) | No | /var/opt/minarca |
| MinarcaRestrictedToBasedDir | Used to enforce security by limiting the user's home directories to inside `UserBaseDir`. It's highly recommended to keep this feature enabled. (Default: True) | No | True |
| MinarcaShell | Location of `minarca-shell` used to limit SSH server access. (Default: /opt/minarca/bin/minarca-shell) | No | /opt/minarca/bin/minarca-shell | 
| MinarcaAuthOptions | Default SSH auth options. This is used to limit the user's permission on the SSH Server, effectively disabling X11 forwarding, port forwarding and PTY. | No | default='no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty' |
| MinarcaRemoteHost | URL defining the remote SSH identity. This value is queried by Minarca Client to link and back up to the server. If not provided, the HTTP URL is used as a base. You may need to change this value if the SSH server is accessible using a different IP address or if not running on port 22. | No | ssh.example.com:2222 |
| MinarcaRemoteHostIdentity | Location of SSH server identity. This value is queried by Minarca Client to authenticate the server. You may need to change this value if SSH service and the Web service are not running on the same server. (Default: /etc/ssh) | No | /etc/ssh | 

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
