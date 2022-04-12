# Configuration

There are several entry points available for administrator to manage the configuration of Minarca. This section aims to outline those configurations and explain each option available and what it does.

Since version 4.0.0, Minarca configuration is more flexible. You may configure every option using the configuration file, command line argument or environment variable.

Take note that configuration options are distinct from the runtime setting, available from the web interface. The configuration options here usually meant to be static and set before starting the server. You may get the list of configuration options by calling `minarca-server --help`.

Note: If an option is specified in more than one place, the command line arguments override the environment variable, environment variables override config files, and config files override default value.

## Configuration file

To use configuration files, you may call `minarca-server` with `-f` or `--config` to define the configuration file location. When not defined, Minarca loads all configuration files from these locations by default:

* /etc/minarca/minarca-server.conf
* /etc/minarca/conf.d/*.conf

Configuration file syntax must define a key and a value. The key is case-sensitive, and you may use underscore (_) or dash (-) seemlessly. All lines beginning with '#' are comments and are intended for you to read. All other lines are configuration for Minarca.

E.g.:

    # This is a comment
    server_port=8081
    log_level=DEBUG

## Environment variables

In addition to configuration files, you may pass environment variables. The options name must be uppercase and prefixed with `RDIFFWEB_`. As an example, if you want to change the port used to listen for HTTP request for 8081, you must define `server-port` option as follow.

    RDIFFWEB_SERVER_PORT=8081

## Command line arguments

When launching `minarca-server` executable, you may pass as many arguments as you want on the command line. The options must be prefixed with double dash (`--`) and you must single dash (-) to separate words.

E.g. `--server-port 8081` or `--server-port=8081` are valid


## Configure listening port and interface

For security reasons, Minarca listen on port `8080` for HTTP request on loopback interface (127.0.0.1) by default. Consider configuring a reverse proxy like Nginx or Apache2 if you want to make Minarca listen on port 80 for HTTP and port 443 for HTTPS request.

| Option | Description | Example |
| --- | --- | --- |
| server-host | Define the IP address to listen to. Use `0.0.0.0` to listen on all interfaces. Use `127.0.0.1` to listen on loopback interface. | 0.0.0.0 |
| server-port | Define the port to listen for HTTP request. Default to `8080` | 9090 |

## Configure administrator username & password

Using configuration file, you may setup a special administrator which cannot be
deleted or renamed from the web interface. You may also configure a specific
password for this user that cannot be updated from the web interface either.

In addition, you may also create other administrator users to manage Minarca.

| Parameter | Description | Example |
| --- | --- | --- | 
| admin-user | Define the name of the default admin user to be created | admin |
| admin-password | administrator encrypted password as SSHA. Read online documentation to know more about how to encrypt your password into SSHA or use <http://projects.marsching.org/weave4j/util/genpassword.php> When defined, administrator password cannot be updated using the web interface. When undefined, default administrator password is `admin123` and it can be updated using the web interface. | modification |


## Configure logging

Minarca can be configured to send logs to specific location. By default, logs are sent to `/var/log/minarca` folder.

| Option | Description | Example |
| --- | --- | --- |
| log-level | Define the log level. ERROR, WARN, INFO, DEBUG | DEBUG |
| log-file | Define the location of the log file. | /var/log/minarca/access.log |
| log-access-file | Define the location of the access log file. | /var/log/minarca/server.log |

In addition, `minarca-shell` and `minarca-quota-api` are also configure to sent log to the same folder.

**Enable Debugging log**

A specific option is also available if you want to enable the debugging log. We do not recommend to enable this option in production as it may leak information to the user whenever an exception is raised.

| Option | Description | Example |
| --- | --- | --- |
| debug | enable debug mode - change the log level to DEBUG, print exception stack trace to the web interface and show SQL query in logs. | |
| environment | Define the type of environment: `development` or `production`. This is used to limit the information shown to the user when an error occurs. Default: production | development |

## Configure database

Minarca use SQL database to store user preferences. The embedded SQLite database is well suited for small deployment (1-100 users). If you intended to have a large deployment, you must consider using a PostgreSQL database instead.

| Option | Description | Example |
| --- | --- | --- |
| database-uri | Location of the database used for persistence. SQLite and PostgreSQL database are supported officially. To use a SQLite database, you may define the location using a file path or a URI. e.g.: `/srv/minarca/file.db` or `sqlite:///srv/minarca/file.db`. To use PostgreSQL server, you must provide a URI similar to `postgresql://user:pass@10.255.1.34/dbname` and you must install required dependencies. By default, Minarca uses a SQLite embedded database located at `/etc/minarca/rdw.db`. | postgresql://user:pass@10.255.1.34/dbname | 

### SQLite

To use embedded SQLite database, pass the option `database-uri` with a URI similar to `sqlite:///etc/minarca/rdw.db` or `/etc/minarca/rdw.db`.

### PostgreSQL

To use an external PostgreSQL database, pass the option `database-uri` with a URI similar to `postgresql://user:pass@10.255.1.34/dbname`.

You may need to install additional dependencies to connect to PostgreSQL. Step to install dependencies might differ according to the way you installed Minarca.

**Using Debian repository:**

    apt install python3-psycopg2

**Using Pypi repository:**

    pip install psycopg2-binary

## Configure LDAP Authentication

Minarca may integrates with LDAP server to support user authentication.

This integration works with most LDAP-compliant servers, including:

* Microsoft Active Directory
* Apple Open Directory
* Open LDAP
* 389 Server

### LDAP options

| Option | Description | Example |
| --- | --- | --- |
| ldap-add-missing-user | `True` to create users from LDAP when the credential is valid. | True |
| ldap-add-user-default-role | Role to be used when creating a new user from LDAP. Default: user | maintainer |
| ldap-add-user-default-userroot | Userroot to be used when creating a new user from LDAP. Default: empty | /backups/{cn[0]} |
| ldap-base-dn | The DN of the branch of the directory where all searches should start from. | dc=my,dc=domain |
| ldap-bind-dn | An optional DN used to bind to the server when searching for entries. If not provided, will use an anonymous bind. | cn=manager,dc=my,dc=domain |
| ldap-bind-password | A bind password to use in conjunction with `LdapBindDn`. Note that the bind password is probably sensitive data,and should be properly protected. You should only use the LdapBindDn and LdapBindPassword if you absolutely need them to search the directory. | mypassword |
| ldap-encoding | encoding used by your LDAP server. Default to utf-8 | cp1252 |
| ldap-filter | A valid LDAP search filter. If not provided, defaults to `(objectClass=*)`, which will search for all objects in the tree. | (objectClass=*) |
| ldap-group-attribute-is-dn | True if the content of the attribute ldap-group-attribute is a DN. | true |
| ldap-group-attribute | name of the attribute defining the groups of which the user is a member. Should be used with ldap-required-group and ldap-group-attribute-is-dn. | member |
| ldap-network-timeout | Optional timeout value. Default to 10 sec. | 10 |
| ldap-protocol-version | Version of LDAP in use either 2 or 3. Default to 3. | 3 |
| ldap-required-group | name of the group of which the user must be a member to access Minarca. Should be used with ldap-group-attribute and ldap-group-attribute-is-dn. | minarca |
| ldap-scope | The scope of the search. Can be either `base`, `onelevel` or `subtree`. Default to `subtree`. | onelevel |
| ldap-timeout | Optional timeout value. Default to 300 sec. | 300 |
| ldap-tls | `true` to enable TLS. Default to `false` | false |
| ldap-uri | URIs containing only the schema, the host, and the port. | ldap://localhost:389 |
| ldap-username-attribute | The attribute to search username. If no attributes are provided, the default is to use `uid`. It's a good idea to choose an attribute that will be unique across all entries in the subtree you will be using. | cn |
| ldap-version | version of LDAP in use either 2 or 3. Default to 3.| 3 |

### Automatically create user in Minarca

If you have a large number of users in your LDAP, you may want to configure Minarca to automatically create user in database that has valid LDAP credentials. The user will get created on first valid login.

You may optionally pass other options like `ldap-add-user-default-role` and `ldap-add-user-default-userroot` to automatically define the default user role and default user root for any new user created from LDAP.

Here a working configuration:

    ldap-add-missing-user=true
    ldap-add-user-default-role=user
    ldap-add-user-default-userroot=/backups/{cn[0]}

### Restrict access to a specific LDAP group

If you are making use of LDAP credentials validation, you will usually want to limit the access to member of a specific LDAP group. Minarca support such scenario with the use of `ldap-required-group`, `ldap-group-attribute` and `ldap-group-attribute-is-dn`.

Here is an example of how you may limit Minarca access to members of *Admin_Backup* group. This configuration is known to work with LDAP PosixAccount and PosixGroup.

    ldap-required-group=cn=Admin_Backup,ou=Groups,dc=nodomain
    ldap-group-attribute=memberUid
    ldap-group-attribute-is-dn=false

## Configure email notifications

You may configure Minarca to send an email notification to the users when their backups did not complete successfully for a period of time.
When enabled, Minarca will also send email notification for security reason when user's password is changed.

| Option | Description | Example |
| --- | --- | --- |
| email-encryption | Type of encryption to be used when establishing communication with SMTP server. Available values: `none`, `ssl` and `starttls` | starttls |
| email-host | SMTP server used to send email in the form `host`:`port`. If the port is not provided, default to standard port 25 or 465 is used. | smtp.gmail.com:587 |
| email-sender | email addres used for the `From:` field when sending email. | Minarca <example@gmail.com> |
| email-notification-time | time when the email notification should be sent for inactive backups. | 22:00 |
| email-username | username used for authentication with the SMTP server. | example@gmail.com |
| email-password | password used for authentication with the SMTP server. | CHANGEME |
| email-send-changed-notification | True to send notification when sensitive information get change in user profile. Default: false | True |

To configure the notification, you need a valid SMTP server. In this example, you are making use of a Gmail account to send emails.

    email-host=smtp.gmail.com:587
    email-encryption=starttls
    email-sender=example@gmail.com
    email-username=example@gmail.com
    email-password=CHANGEME
    email-send-changed-notification=true

Note: notifications are not sent if the user doesn't have an email configured in his profile.

## Configure user quota

Since v2.1, it's now possible to customize how user quota is controller for
your system without a custom plugin. By defining `quota-set-cmd`, `quota-get-cmd`
and `QuotaUsedCmd` configuration options, you have all the flexibility to
manage the quota the way you want by providing custom command line to be executed to respectively set the quota, get the quota and get quota usage.

| Option | Description | Example |
| --- | --- | --- |
| quota-set-cmd | Command line to set the user's quota. | Yes. If you want to allow administrators to set quota from the web interface. |
| quota-get-cmd | Command line to get the user's quota. Should print the size in bytes to console. | No. Default behaviour gets quota using operating system statvfs that should be good if you are using setquota, getquota, etc. For ZFS and other more exotic file system, you may need to define this command. |
| quota-used-cmd | Command line to get the quota usage. Should print the size in bytes to console. | No. |

When Minarca calls the scripts, special environment variables are available. You should make use of this variables in a custom script to get and set the disk quota.

* `RDIFFWEB_USERID`: rdiffweb user id. e.g.: `34`
* `RDIFFWEB_USERNAME`: rdiffweb username. e.g.: `patrik`
* `RDIFFWEB_USERROOT`: user's root directory. e.g.: `/backups/patrik/`
* `RDIFFWEB_ROLE`: user's role e.g.: `10` 1:Admin, 5:Maintainer, 10:User
* `RDIFFWEB_QUOTA`: only available for `quota-set-cmd`. Define the new quota value in bytes. e.g.: 549755813888  (0.5 TiB)

Continue reading about how to configure quotas for EXT4. We generally
recommend making use of project quotas with Minarca to simplify the management of permission and avoid running Minarca with root privileges.  The next section
presents how to configure project quota. Keep in mind it's also possible to
configure quota using either user's quota or project quota.

### Configure user quota for EXT4

This section is not a full documentation about how to configure ext4 project quota,
but provide enough guidance to help you.

1. Enabled project quota feature  
   You must enable project quota feature for the EXT4 partition where your backup resides using:  
   `tune2fs -O project -Q prjquota /dev/sdaX`  
   The file system must be unmounted to change this setting and may require you
   to boot your system with a live-cd if your backups reside on root file system (`/`).  
   Also, add `prjquota` options to your mount point configuration `/etc/fstab`.
   Something like `/dev/sdaX   /   ext4    errors=remount-ro,prjquota     0    1`
2. Turn on the project quota after reboot  
   `quotaon -Pv -F vfsv1 /`
3. Check if the quota is working  
   `repquota -Ps /`
4. Add `+P` attribute on directories to enabled project quotas  
   `chattr -R +P /backups/admin`
5. Then set the project id on directories  
   `chattr -R -p 1 /backups/admin` where `1` is the Minarca user's id

Next, you may configure Minarca quota command line for your need. For EXT4
project quotas, you only need to define `quota-set-cmd` with something similar
to the following. `quota-get-cmd` and `quota-used-cmd` should not be required
with EXT4 quota management.

    quota-set-cmd=setquota -P $RDIFFWEB_USERID $((RDIFFWEB_QUOTA / 1024)) $((RDIFFWEB_QUOTA / 1024)) 0 0 /

This effectively, makes use of Minarca user's id as project id.

### Configure user quota for ZFS

This section is not a full documentation about how to configure ZFS project quotas,
but provide enough guidance to help you. This documentation uses `tank/backups`
as the dataset to store Minarca backups.

1. Quota feature is a relatively new feature for ZFS On Linux. Check your
   operating system to verify if your ZFS version support it. You may need
   to upgrade your pool and dataset using:  

   `zpool upgrade tank`
   `zfs upgrade tank/backups`

2. Add `+P` attribute on directories to enabled project quotas  
   `chattr -R +P /backups/admin`
   `chattr -R -p 1 /backups/admin`
   OR
   `zfs project -p 1 -rs /backups/admin`
   Where `1` is the Minarca user's id

Take note, it's better to enable project quota attributes when the repositories are empty.

## Configure user's session persistence.

Minarca could be configured to persist the user's session information either in
memory or on disk. When the user's session persists in memory, all user's
session get reset if the web server restart. If you want to persist the user's
session even if the web server gets restarted, you may persist them on disk with
`session-dir` option.

| Option | Description | Example |
| --- | --- | --- |
| session-dir | location where to store user session information. When undefined, the user sessions are kept in memory. | /var/lib/minarca/session |

## Configure Minarca appearance

A number of options are available to customize the appearance of Minarca to your
need. Most likely, you will want to make it closer to your business brand.

| Option | Description | Example |
| --- | --- | --- |
| header-name | Define the application name displayed in the title bar and header menu. | My Backup |
| default-theme | Define the theme. Either: `default`, `blue` or `orange`. | orange |
| welcome-msg | Replace the headline displayed in the login page. It may contains HTML. | Custom message displayed on login page.|
| favicon | Define the FavIcon to be displayed in the browser title | /etc/minarca/my-fav.ico |

## Configure repositories clean-up job

Using the web interface, users may configure a retention period on individual repository to keep only a fixed number of days in backup. This is useful to control the growth of a repository disk usage.

To support this feature, Minarca schedule a job to clean-up the repositories in backup. This job is ran once a day. You may change the default time when this schedule job is running by defining another value for option `remove-older-time`.

| Parameter | Description | Example |
| --- | --- | --- |
| remove-older-time | Time when to execute the remove older task | 22:00 |

## Configure temporary folder location

To restore file or folder, Minarca needs a temporary directory to create the file to be downloaded. By default, Minarca will use your default temporary folder defined using environment variable `TMPDIR`, `TEMP` or `TMP`. If none of these environment variables are defined, Minarca fallback to use `/tmp`.

If you want to enforce a different location for the temporary directory, you may define the option `tempdir` with a different value. Take note, this directory must be created with the right ownership and permissions to allow Minarca to use it. Also make sure enough disk space is available. Usually, a 32GiB is enough.

| Parameter | Description | Example |
| --- | --- | --- |
| tempdir | alternate temporary folder to be used when restoring files. Might be useful if the default location has limited disk space| /tmp/minarca/ |

## Configure repository lookup depthness.

When defining the UserRoot value for a user, Minarca will scan the content of this directory recursively to lookups for rdiff-backup repositories. For performance reason, Minarca limits the recursiveness to 5 subdirectories. This default value should suit most use cases. If you have a particular use case, it's possible to allow Minarca to scan for more subdirectories by defining a greater value for the option `max-depth`. Make sure to pick a reasonable value for your use case as it may impact the performance.

| Parameter | Description | Example |
| --- | --- | --- |
| --max-depth | Define the maximum folder depthness to search into the user's root directory to find repositories. This is commonly used if your repositories are organised with multiple sub-folders. Default: 5 | 10 |

## Configure Minarca's help

It's also possible to customized how the users are reaching your company by
defining a custom web page. By defining this option, users needing your help
from the Minarca client application will be redirect to this page instead of
the default Minarca web site.

| Parameter | Description | Example |
| --- | --- | --- |
| minarca-help-url | Define URL where to redirect users| <https://my-company.com/support> |

## Quota Management

Minarca provide user based quota management. This allow you to define fixed
amount of disk space for each user. If a user backup reach the quota, the
backup will fail.

This feature might be used by service provider to define the maximum disk space
allocated to a user based on the price of the service.

Default implementation of users quota support only ZFS storage. But you may
customize this to fit your file system and deployment by configure the command
line to be executed.

First, install `minarca-quota-api` on the storage server. This might be the
same server as Minarca Web Server or a different one depending on your setup.

In Minarca web server configuration file `/etc/minarca/minarca-server.conf`,
you must define the location of the quota API service to be used to set and
fetch the disk usage.

| Parameter | Description | Example |
| --- | --- | --- |
| minarca-quota-api-url | URL to access `minarca-quota-api` service either. | <http://minarca:secret@localhost:8081/> |

## Advance Minarca Configuration

Minarca automatically configure where user's backups get stored. You may customize this
by using the following settings. Unless you know what you are doing it's not
recommanded to change any of these settings.

| Parameter | Description | Example |
| --- | --- | --- |
| minarca-user-setup-dir-mode | Permission to be set on the user's folder created by Minarca. (Default: 0700) | 448 (equals to 0700) |
| minarca-user-base-dir | Folder where users repositories should be created. You may need to change this value if you already have your repositories created in a different location or if you are migrating from rdiffweb. Otherwise it's recommended to keep the default value. (Default: /backups/) | /backups/ |
| minarca-restricted-to-based-dir | Used to enforce security by limiting the user's home directories to inside `UserBaseDir`. It's highly recommended to keep this feature enabled. (Default: True) | True |
| minarca-shell | Location of `minarca-shell` used to limit SSH server access. (Default: /opt/minarca-server/bin/minarca-shell) | /opt/minarca-server/bin/minarca-shell |
| minarca-auth-options | Default SSH auth options. This is used to limit the user's permission on the SSH Server, effectively disabling X11 forwarding, port forwarding and PTY. | default='no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty' |
| minarca-remote-host | URL defining the remote SSH identity. This value is queried by Minarca Client to link and back up to the server. If not provided, the HTTP URL is used as a base. You may need to change this value if the SSH server is accessible using a different IP address or if not running on port 22. | ssh.example.com:2222 |
| minarca-remote-host-identity | Location of SSH server identity. This value is queried by Minarca Client to authenticate the server. You may need to change this value if SSH service and the Web service are not running on the same server. (Default: /etc/ssh) | /etc/ssh |
