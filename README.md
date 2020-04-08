![Minarca Logo](doc/resources/banner.png)

<p align="center">
  <strong>
    <a href="http://www.patrikdufresne.com/en/minarca/">website</a>
    •
    <a href="https://github.com/ikus060/minarca/blob/master/doc/index.md">docs</a>
    •
    <a href="https://groups.google.com/forum/#!forum/rdiffweb">community</a>
  </strong>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/ikus060/minarca"></a>
  <a href="https://github.com/ikus060/minarca/blob/master/doc/index.md"><img alt="Documentation" src="https://img.shields.io/badge/code-documented-brightgreen.svg?style=flat-square"></a>
  <a href="https://git.patrikdufresne.com/pdsl/minarca/pipelines"><img alt="Build" src="https://git.patrikdufresne.com/pdsl/minarca/badges/master/pipeline.svg"></a>
</p>

<h1 align="center">
  Welcome to Minarca Backup Software!
</h1>

Minarca is a **free and open-source** backup software providing end-to-end integration to put you in control of your backup strategy. This **Self-Hosted** software may suit the needs of service providers or small business. 

**Simple** to install, to configure and to manage, Minarca will not waste your time. Minarca makes user data easily accessible by providing a rich **web interface** to recover the files.

**Minarca client** may be used to simplify the integration of new computers running **Windows or Linux Debian**. It's user interface and command line interface allow simple usage for **desktop users or headless servers**. Minarca also keep interoperability with legacy installation of rdiff-backup.

## Getting started

Check how Minarca is working without installing the server. We have setup a testing environment for you. You may login to https://test.minarca.net/ using the default username / password: admin / admin123

Then start a backup in few minutes by installing minarca client for [Windows](http://www.patrikdufresne.com/archive/minarca/minarca-latest-install.exe) or [Linux/Debian](http://www.patrikdufresne.com/archive/minarca/minarca-client_latest_all.deb). 

## Download & Install

**Minarca Server**

<a href="http://www.patrikdufresne.com/archive/minarca/minarca-server_latest_amd64.deb"><img alt="Minarca Server for Ubuntu/Debian Linux version" src="https://img.shields.io/badge/download-Minarca%20server-brightgreen"></a>

Read more about [how to installation Minarca server](doc/installation.md).

Note: While it's possible to get Minarca Server working on other Linux distributions, only Debian-based distribution is officially supported.

**Minarca Client**

<a href="http://www.patrikdufresne.com/archive/minarca/minarca-client_latest_all.deb"><img alt="Minarca Client for Linux/Debian" src="https://img.shields.io/badge/download-Minarca%20for%20Debian-brightgreen"></a>
<br/>
<br/>
<a href="http://www.patrikdufresne.com/archive/minarca/minarca-latest-install.exe"><img alt="Minarca Client for Windows" src="https://img.shields.io/badge/download-Minarca%20for%20Windows-brightgreen"></a>

Note: While it's possible to get Minarca Client working on other Linux distributions, only Debian-based distribution will be supported.

# Support

## Bug Reports

Bug reports should be reported on the Minarca development web site at https://github.com/ikus060/minarca/issues

## Professional support

Professional support for Minarca is available by contacting [Patrik Dufresne Service Logiciel](http://www.patrikdufresne.com/en/support/#form).

# About Minarca

Minarca Server is written in Python and is released as open source project under the 
GNU AFFERO GENERAL PUBLIC LICENSE (AGPLv3). All source code and documentation are
Copyright Patrik Dufresne Service Logiciel inc. <info@patrikdufresne.com>

Minarca Server is actively developed by [Patrik Dufresne](http://patrikdufresne.com)
since April 2015.

The Minarca Server source code is hosted on [private Gitlab](https://git.patrikdufresne.com/pdsl/minarca)
and mirrored to [Github](https://github.com/ikus060/minarca).

The Minarca website is http://www.patrikdufresne.com/en/minarca/.

# Changelog

## Server / Client v3.5.0 (2020-04-08)

This release focus mostly on providing a Debian Buster compatible packages. A good effort was made to provide an easy-to-use package for Debian and making sure it's well tested in an automated way to avoid regression and speedup further release.

 * Server: Upgrade the rdiffweb v1.2.2
     * Restore file and folder in a subprocess to make the download start faster
     * Fix encoding of archive on Python3.6 (CentOS 7) by using PAX format
     * Add support to restore files and folders using rdiff-backup2
     * Remove obsolete dependencies `pysqlite2`
     * Fix issue creating duplicate entries of repository in database
 * Server: Remove `python-pysqlite2` from debian package dependencies
 * Server: Fix to make sure the `minarca-server` service unit is enabled and started after installation.
 * Server: Force owner and group recursively on Minarca's folder during installation
 * Client: Add username and hostname in the status info to ease debugging
 * Documentation: Add information about [how to run minarca-client when users are not logged](doc/minarca-client.md#why-is-my-backup-not-running-)
 * Documentation: Provide default user and password to login after [installation](doc/installation.md#install-minarca-server)

## Server / Client v3.4.3 (2020-03-08)

Continue to stabilize the previous release with little bug fixes and minor improvement for the end user.

 * Server: Upgrade the rdiffweb v1.2.2
     * Enhance the repository to invite users to refresh the repository when the view is empty.
     * Deprecate support for cherrypy 4, 5, 6 and 7
     * Improve loading of repository data (cache status and entries)
     * Restore compatibility with SQLite 3.7 (CentOS7)
 * Client: Linux - Raise an error when the patterns don't match any files instead of silently succeeding without backuping anything.
 * Client: Linux - Move logs to /var/log when running as root.
 * Client: Linux - Silently ignore error when failing to inhibit on Linux when d-bus is not available.
 * Client: Linux - From command line adds a "continue logging..." to help the user know where to look for logs.
 * Client: Linux - When running from cron do not print "continue logging..." to avoid sending email to root user.
 * Client: Windows - Install Java 8 Update 241 when Java is not available.
 * Client: Windows - Enable TLS1.2 during installation to allow download and installation of Java
 * Client: When linking for the first time, make sure to create a scheduled task even when the repository already exists.

## Server / Client v3.4.1 (2020-02-08)

Little bug fixes following the previous release.

 * Server: Upgrade the rdiffweb v1.2.1
     * Fix 404 error when trying to access other users repo as admin
     * Fix logging format for cherrypy logs to matches rdiffweb format
     * Add log rotation by default
 * Server: Enforce permissions on `/etc/minarca` and `/var/log/minarca` to reduce visibility to only minarca user
 * Client: Fix cryptic character installation due to bad encoding for French locale
 * Client: Fix year in about dialog for French locale
 * Client: Document the `--force` command line option for `link` operation
 * Client: Relocate the configuration under `/etc/minarca` when ran as root
 * Client: Add default symlink to `minarca` in `/usr/sbin/` to make is part of PATH for root user

## Server / Client v3.4.0 (2020-01-30)

 * Server: Upgrade to rdiffweb v1.2.0
     * Add explicit testing for Debian Stretch & Buster
     * Change the persistence layers
       * Minimize number of SQL queries
       * Add object lazy loading
       * Add object data caching
     * Fix bugs with SQLite <= 3.16 (Debian Stretch)
 * Server: Add port to EmailHost` by default
 * Client: Windows - To avoid unexpected interruption inhibits computers from sleep during backup.
 * Client: Windows - Replace usage of `tasklist.exe` by JNA calls to improve portability and responsiveness
 * Client: Windows - Allow the installer to be silent using `minarca-client-install.exe /S`
 * Client: Windows - For portability downgrade OpenSSH client to 32-bit version
 * Client: Windows - To reduce package footprints, remove unused text files from Windows installation.
 * Client: Linux- To avoid unexpected interruption inhibits computers from sleep during backup on Gnome Desktop using D-Bus calls.
 * Client: to improve SSH handshake, enforce client to use public key authentication 
 * Automate testing of Windows 
 * Update documentation

## Server / Client v3.3.0 (2019-11-06)

 * Server: Upgrade to rdiffweb v1.1.0
	 * Change repository URL to username/repo-name - in preparation to add ACL in future release
	 * Add repository view to allow administrator to browse, restore, edit other user repositories
	 * Add system information (version, configuration, operating system info, etc.) to the admin area
	 * Add server logs to admin area (rdiff-backup.log & rdiff-backup-access.log)
	 * Improve the user's view layout
	 * Check local database credentials before LDAP credentials
	 * Reduce footprint of confirmation dialog box
	 * Reduce code smells reported by Sonarqube
	 * Improve main menu structure
	 * Change default login page headline
	 * Support Jinja2 version >= 2.10 (add integration test for 2.6 to 2.10)
	 * Update documentation
 * Server: Add `tail` packages as a dependency
 * Server: Replace headline on the login page, adding link to website, documentation and community
 * Client: Re-create scheduled task on startup if it was removed by the user
 * Client: Upgrade apache client version to v4.3.6 mitigate security risk repported by Github vulnerability scan
 * Client: Fix default minarca launcher to call `minarcaui` instead or `minarca`
 * Client & Server: Allow backup over non-default SSH port (22)
 
## Server v3.0.1 - Bug fixes (2019-10-04)

 * Upgrade to rdiffweb v1.0.3.
 * Update the authorized_keys when user's home directory get updated.
 * Force user's home directory owner and group. Allow minarca web interface to run as root.
 * Minarca-shell: Fix repository name validation.
 * Minarca-shell: Add SUDO_OWNERSHIP to sets the owner and group. Allow better quota management.
 * Pipeline: Add integration testing with server and client linking.

## Client v3.2.4 (2019-10-01)

* Client: Update french translation

## Client v3.2.3 (2019-09-25)

* Client: Add "cron" as dependencies in debian package

## Client v3.2.2 (2019-09-15)

* Client: Add "java-headless" and ssh-client as dependencies in debian package
* Client: Remove dependencies to AWT (to work in headless mode)
* Client: Bump JRE version to 1.8 in Windows installer

## Server v3.0.0 / Client v3.2.1 - First public version (2019-09-14)

 * Support cherrypy v16
 * Provide debian packages
 * Manage SSH Keys for minarca user
 * Provide minarca-shell as an SSH entrypoint
 * Improve SSH server security
 * Add /api/ to be used by minarca-client
 * Update Minarca icon
 * Client: Fix pid verification to avoid multiple instance to be running
 
## Client v3.2.0 - First public release (2019-09-12)

* Client: Provide debian packages
* Client: Replace Form request by API calls
* Client: Make it work with minarca-shell
* Client: Use patches version of rdiff-backup 1.2.8
* Client: Replace proprietary licence by GPLv3
* Client: Replace Minarca icon
* Client: Improve configuration UI
* Client: Improve linking UI
* Client: Update default ignored patterns
* Client: Update french translation
* Client: Add command line interface 
* Client: Verify if process is running using pid file on all platform
