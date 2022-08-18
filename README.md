![Minarca Logo](minarca-client/doc/_static/banner.png)

<p align="center">
  <strong>
    <a href="https://www.ikus-soft.com/en/minarca/">website</a>
    •
    <a href="https://www.ikus-soft.com/en/minarca/doc">docs</a>
    •
    <a href="https://groups.google.com/forum/#!forum/rdiffweb">community</a>
  </strong>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/ikus060/minarca"></a>
  <a href="https://gitlab.com/ikus-soft/minarca/pipelines"><img alt="Build" src="https://gitlab.com/ikus-soft/minarca/badges/master/pipeline.svg"></a>
  <a href="https://sonar.ikus-soft.com/dashboard?id=minarca"><img alt="Quality Gate Minarca" src="https://sonar.ikus-soft.com/api/project_badges/measure?project=minarca&metric=alert_status"></a>
  <a href="https://sonar.ikus-soft.com/dashboard?id=minarca"><img alt="Coverage" src="https://sonar.ikus-soft.com/api/project_badges/measure?project=minarca&metric=coverage"></a>
</p>

<h1 align="center">
  Welcome to Minarca Backup Software!
</h1>

Minarca is a **free and open-source** backup software providing end-to-end integration to put you in control of your backup strategy. This **Self-Hosted** software may suit the needs of service providers or small business. 

**Simple** to install, to configure and to manage, Minarca will not waste your time. Minarca makes user data easily accessible by providing a rich **web interface** to recover the files.

**Minarca client** may be used to simplify the integration of new computers running **Windows or Linux Debian**. It's user interface and command line interface allow simple usage for **desktop users or headless servers**. Minarca also keep interoperability with legacy installation of [rdiff-backup](https://rdiff-backup.net/).

Based on [rdiffweb](https://www.ikus-soft.com/en/rdiffweb/), **Minarca Server** may be used to browse, **restore your data easily** with a convenient web interface accessible from everywhere.

## Getting started

Check how Minarca is working without installing the server. We have setup a testing environment for you. You may login to https://test.minarca.net/ using the default username / password: admin / admin123

Then start a backup in few minutes by installing minarca client for [Windows](https://www.ikus-soft.com/archive/minarca/minarca-client_latest.exe) or [Linux/Debian](https://www.ikus-soft.com/archive/minarca/minarca-client_latest_all.deb).

## Download & Install

[Minarca Download Page](https://www.ikus-soft.com/en/minarca/download/)

[Minarca Server Installation steps](https://www.ikus-soft.com/archive/minarca/doc/installation.html)

[Minarca Agent Installation steps](https://www.ikus-soft.com/archive/minarca/doc/minarca-client.html#installation)

# Support

## Bug Reports

Bug reports should be reported on the Minarca development web site at https://github.com/ikus060/minarca/issues

## Professional support

Professional support for Minarca is available by contacting [IKUS Software inc.](https://www.ikus-soft.com/en/support/#form).

# About Minarca

Minarca Server is written in Python and is released as open source project under the 
GNU AFFERO GENERAL PUBLIC LICENSE (AGPLv3). All source code and documentation are
Copyright IKUS Software inc. <support@ikus-soft.com>

Minarca Server is actively developed by [IKU Software inc.](https://ikus-soft.com)
since April 2015.

The Minarca Server source code is hosted on [Gitlab](https://gitlab.com/ikus-soft/minarca)
and mirrored to [Github](https://github.com/ikus060/minarca).

The Minarca website is https://www.ikus-soft.com/en/minarca/.

# Changelog

## Next Release

* Add Ubuntu Jammy support
* Add Debian Bookworm support
* Adjust `librsync` dependencies for release upgrade
* Remove dependencies to unmaintained `snakeoil` library
* Drop Ubuntu Hirsute & Impish (End-of-life)

## 4.2.0 (2022-07-05)

* Upgrade Rdiffweb to [v2.4.0](https://rdiffweb.org/blog/rdiffweb-s-blog-6/new-security-features-and-continuous-improvement-53)
* Add support for Ubuntu Impish
* Upgrade pyinstaller to 4.8 to improve command line usage and fixing issues with UTF8 #175
* Allow usage of `--force` to force link event if client is already linked
* Update French translation #178
* Update Minarca documentation
* Improve code quality with `black` and `isort`

## 4.1.1 (2021-01-26)

* Create apt configuration file only when file doesn't exists to avoid overwriting user's config

## 4.1.0 (2022-01-18)

* Server: Upgrade to Rdiffweb v2.3.9
  * Fix `Chart.js` loading on Debian bullseye rdiffweb#164
  * Improve LDAP authentication to lookup entire directory
  * Fix usage of `--ldap-add-user-default-userroot` to avoid error related to wrong encoding
  * Improve authentication mechanics
  * Avoid raising an HTTP error 500 when login form receive invalid payload
  * Mitigate open redirect vulnerability in login form
  * Improve date parsing for `backup.log` to avoid printing exception in logs #170
  * Return HTTP error 403 for invalid symlink to avoid returning a misleading HTTP 500 Server Error #168
  * Show a user friendly error message when trying to create a new user with an existing username #169
  * Handle repository without last-backup date during the notification process to ensure notifications are sent #171
  * Replace CherryPy `storage_type` by `storage_class` to avoid warning in logs
  * Update code to avoid deprecation warning where applicable
  * Add Flake8 validation to improve code quality
* Fix Windows application startup cause by stdout redirection #161
* Upgrade OpenSSH to v8 to mitigate SSH error message #69 #65
* Add a help button to redirect user to custom help form #145
* Avoid printing `password:` twice during linking process with cli #162
* Update user interface to enhance user experience #163
* Check if a newer version is available on the startup #43
* Adding Debian APT repository when installing from `.deb` package to automate upgrade #159
* Avoid launching Minarca client from installers for Windows to mitigate permission issues while deleting Schedule Tasks #167
* Improve `rdiff-backup` error handling to provide more guidance when SSH connection fail #158
* Clear previous backup status when linking Minarca to a new server to better reflect the real status #168
* Fix translation loading on MacOS and Windows #171
* Upgrade pyinstaller to 4.7 to improve operating system integration #174
* Remove Ubuntu Groovy support

## v4.0.6

* Make output log quiet when minarca is launch within a cronjob to avoid receiving email for successful execution

## v4.0.5

* Add python3-distutil as dependencies for Debian package to avoid exception when starting `minarca` without it

## v4.0.4

* Improve stderr redirection when rdiff-backup is launch to avoid leaking threads
* Improve user interface testing

## v4.0.1

* Server: Upgrade to Rdiffweb v2.3.7
  * Mitigate CSRF vulnerability using cookies with `SameSite=Lax`
  * Mitigate CSRF vulnerability by validating the `Origin` header when a form is submited
  * Improve usage of WTForm for all form validation
* Generate docuemntation using Sphinx
* Remove usage of PySimpleGUI library to create user interface #160 #147
* Use ttkbootstrap to generate Tkinter Theme
* Display current version in Minarca user interface

## v4.0.0 (2021-09-20)

This new version include a new Minarca client with better integration with the operating system. This new version also include support for MacOS !

 * Server: Upgrade to Rdiffweb v2.3.4
   * Skip email notification if `email-host` configuration is not provided rdiffweb#157
   * Skip email notification when the new attribute value has the same value rdiffweb#159
   * USE LDAP `mail` attribute when creating new user from LDAP directory rdiffweb#156
   * Provide a new theme `blue` to match IKUS Soft colors rdiffweb#158
   * Automatically update user's repository list based on user's home directory
   * Update default `session-dir` location to `/var/lib/rdiffweb/session` to avoid using `/var/run` rdiffweb#148
   * Improve timezone handling to display date with local timezone using javascript rdiffweb#143
   * Improve charts by replacing d3js by chartkick rdiffweb#122
   * Replace the status view by something meaningful with chartkick rdiffweb#122
   * Provide Docker image with Rdiffweb `docker pull ikus060/rdiffweb` rdiffweb#55
   * Fix file and folder sorting rdiffweb#143
 * Server: Improve creation of SSH Chroot jail by creating `/dev/null` in the jail 
 * Server: Use new `blue` theme by default
 * Server: Fix installation stability on Debian Bullseye
 * Server: Update default minarca favicon
 * Server: Update french translatiom
 * Client: Re-implement minarca-client in python #87
 * Client: Sign MacOS Application Bundle #149
 * Client: Provide french translation

## v3.9.0 (2021-05-17)

This new version include alot of changes from Rdiffweb release (https://www.ikus-soft.com/en/blog/2021-05-11-rdiffweb-v220/)

 * Server: Upgrade to Rdiffweb v2.2.0
   * Use ConfigArgPare for configuration to support configuration file, environment variables and arguments to configure rdiffweb (rdiffweb#114)
   * Fix cache in localization module
   * Add `ldap-add-default-role` and `ldap-add-default-userroot` option to define default value for role and user root when creating user from LDAP (rdiffweb#125)
   * Support PostgreSQL database by replacing our storage layer by SQLAlchemy rdiffweb#126
   * Fix to retrieve user quota only for valid user_root (rdiffweb#135)
   * Add option `disable-ssh-keys` to disable SSH Key management
   * Use absolute URL everywhere
   * Add support for `X-Forward-For`, `X-Forward-proto` and other reverse proxy header when generating absolute URL
   * Drop Debian Strech support
   * Implement a new background scheduler using apscheduler rdiffweb#82
   * Use background job to send email notification to avoid blocking web page loading (rdiffweb#47)
   * Use background job to delete repository to avoid blocking web page loading (rdiffweb#48)
   * Allow deleting a specific file or folder from the history using `rdiff-backup-delete` (rdiffweb#128)
   * Improve support for `session-dir` (rdiffweb#131)
   * Add option `admin-password` to define administrator password for better security
   * Improve performance of repository browsing 
   * Add a new view to display logs of a specific repository
   * Allow downloading the log
   * Define a default limit to graph statistics to make it display faster
   * Fix `get-quota-cmd` option to properly return a value
 * Server: Migrate APT repository to `https://nexus.ikus-soft.com/repository/apt-release-buster`
 * Server: Transparently support `rdiff-backup` v1.2.8 and v2.0.5 (#134)
 * Server: Update `authorization_keys` file on restart
 * Server: Drop Debian Stretch support
 * Server: Add support for Debian Bullseye
 * Server: Provide default `session-dir` to persist user session between restart
 * Server: Upgrade Debian packaging
 * Server: Fix timezone detection in minarca-shell causing all date to be displayed as UTC in web interface.
 * Client: Support `rdiff-backup` v1.2.8 or v2.0.5
 * Client: Improve command line help
 * Client: Improve detection of already running process to avoid exeution of multiple minarca client instance
 * Client: Support repository name starting with number

## v3.8.0 (2021-02-17)

This new version bring two major features Minarca: A user quota management ready for production and a more secure minarca-shell to handle incoming SSH connection.

 * Server: Upgrade to rdiffweb v2.1.0
    * Re-implement logic to update repositories views to remove duplicates and avoid nesting repo. #107
    * Handle elapsed time of days in the graph. Thanks [Nathaniel van Diepen](https://github.com/Eeems) contributions.
    * Rebrand all link to ikus-soft.com
    * Update documentation to install rdiffweb
    * Remove obsolete minify dependency
    * Drop support for python2
    * Provide null translation if translation catalogues are not found
    * Pass a LANG environment variable to rdiff-backup restore process to fix encoding issue #112
    * Remove obsolete python shebang
    * Remove execution bit (+x) on python modules
    * Provide `--help` and `--version` on `rdiffweb` executable
    * Improve cherrypy version detection
    * Do not update translation files (.mo) during build
    * Debian package: Remove dh-systemd from Debian build dependencies (https://bugs.debian.org/871312we)
    * Improve Quota management:
      * `QuotaSetCmd`, `QuotaGetCmd` and `QuotaUsedCmd` options could be used to customize how to set the quota for your environment.
      * Display user's quota in User View
      * Display user's quota in Admin View
      * Allow admin to update user quota from Admin View when `QuotaSetCmd` is defined.
      * Allow admin to define user quota using human readable value (e.g.: GiB, TiB, etc.)
      * Improve logging around quota management
    * Improve robustness when service is starting
    * Improve robustness when repository has wrong permission defined (e.g.: when some files not readable)
    * Add user id in Admin view
    * Replace `UserObject(1)` by the actual username in log file to improve debugging
 * Server: Drops support for python 2.7
 * Server: Improve ZFS Quota Management to use project quota. #95
 * Server: Add minarca-quota-api and minarca-shell logs to admin view #126
 * Server: Adjust the logging format to be similar in all components
 * Server: Re-impleent minarca-shell in pure python to be more integrated with rdiffweb/minarca
 * Server: Update authorized_keys when server get restarted to reflect any config or database change #127
 * Server: Increase security of SSH connexion by user user namespace to create chroot jail #121
 * Server: Define `$HOME` when creating user namespace to work arround python calling `getpwuid()`
 * Client: Improve error message when Scheduled Task refused to be created in Windows
 * Client: Fix `minarca` command line parsing for include|exclude #125 #120
 * Client: Adjust the logging format to be similar to server log
 * Client: Create log file to /var/log/minarca.log when the `uid` is root
 * Doc: Update installation steps rdiffweb/#109
 * Doc: Provide mode architectural details #70

## v3.7.0 (2020-06-24)

This new release officially adds the installation of Minarca using an APT repository for Debian Stretch and Debian Buster.
Take a look at the updated [installation steps](doc/installation.md). Quickly, the installation become easy as `curl https://www.ikus-soft.com/archive/minarca/get-minarca.sh | sh -`.

 * Server: Upgrade to rdiffweb v1.5.0
     * Change formatting of Last Backup date for "Updated 3 weeks ago" to ease the readability
     * Add support for Debian Bullseye
     * Add support for Python 3.8 (rdiffweb#104)
     * Add warning in the users list view when a root directory is invalid (rdiffweb#30)
     * Add options to control search depthness (rdiffweb#1)
     * Print a warning in the log when the "DefaultTheme" value is not valid (rdiffweb#90)
 * Client: Upgrade to NSIS v3 installers to provide a better integration for Windows 10 
 * Client: Icons are up to date with better resolutions
 * Client: Provide more details about the error when the first backup is failing during linking
 * Doc: Replace PDSL by IKUS Software Inc. in licensing and documentation

## v3.6.0 (2020-05-20)

 * Server: Upgrade to rdiffweb v1.4.0
     * Fix lookup of executable rdiff-backup and rdiffweb-restore to search in current virtualenv first
     * Fix repository view when multiple repo paths are conflicting
     * Fix logging of rdiffweb-restore subprocess
     * Fix single repository discovery when a user's home is a rdiff-backup repository
     * [SPONSORED] Add a new setting at the user level to define the user's role. Admin,
       Maintainer and User. Admin are allowed to do everything. Maintainer are
       allowed to browse and delete repo. Users are only allowed to browse. #94
     * Add "Powered by" in the web interface footer #91
     * Display a nice error message when trying to delete admin user #93
     * Introduce usage of wtforms and flash in admin users for better form validation. #96 #97
 * Server: Fix default permission during installation on Debian for /etc/minarca, /var/log/minarca, /backups/ to define the proper owner and restrict permission.
 * Client: Clarify the application purpose for the user by renaming the link to "Minarca Backup"
 * Start publishing DEB into [APT repositories](https://nexus.ikus-soft.com/#browse/search/apt=format%3Dapt%20AND%20version%3D3.6.0*)
 * [SPONSORED] Server: Allow redirection of http://localhost:8080/help to a custom help page for your business
 * [SPONSORED] Client: Redirect the help button (?) to your business custom help page
 * Client: Minor changes to the layout to improve user's usability
 * Update French translation

## v3.5.0 (2020-04-08)

This release focus mostly on providing a Debian Buster compatible packages. A good effort was made to provide an easy-to-use package for Debian and making sure it's well tested in an automated way to avoid regression and speedup further release.

 * Server: Upgrade the rdiffweb v1.3.1
     * Restore file and folder in a subprocess to make the download start faster
     * Fix encoding of archive on Python3.6 (CentOS 7) by using PAX format
     * Add support to restore files and folders using rdiff-backup2
     * Remove obsolete dependencies `pysqlite2`
     * Fix issue creating duplicate entries of repository in database
     * Enforce password encryption by using {SSHA} scheme
 * Server: Remove `python-pysqlite2` from debian package dependencies
 * Server: Fix to make sure the `minarca-server` service unit is enabled and started after installation.
 * Server: Force owner and group recursively on Minarca's folder during installation
 * Client: Add username and hostname in the status info to ease debugging
 * Documentation: Add information about [how to run minarca-client when users are not logged](doc/minarca-client.md#why-is-my-backup-not-running-)
 * Documentation: Provide default user and password to login after [installation](doc/installation.md#install-minarca-server)

## v3.4.3 (2020-03-08)

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

## v3.4.1 (2020-02-08)

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

## v3.4.0 (2020-01-30)

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

## v3.3.0 (2019-11-06)

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

# Related projects

* [rdiffweb](https://www.ikus-soft.com/en/rdiffweb/): web interface 
* [rdiff-backup](https://rdiff-backup.net/): core engine used to run the backup

