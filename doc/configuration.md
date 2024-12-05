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

In addition to configuration files, you may pass environment variables. The options name must be uppercase and prefixed with `MINARCA_`. As an example, if you want to change the port used to listen for HTTP request for 8081, you must define `server-port` option as follow.

   MINARCA_SERVER_PORT=8081

## Command line arguments

When launching `minarca-server` executable, you may pass as many arguments as you want on the command line. The options must be prefixed with double dash (`--`) and you must single dash (-) to separate words.

E.g. `--server-port 8081` or `--server-port=8081` are valid


## Configure listening port and interface

For security reasons, Minarca listen on port `8080` for HTTP request on loopback interface (127.0.0.1) by default. Consider configuring a reverse proxy like Nginx or Apache2 if you want to make Minarca listen on port 80 for HTTP and port 443 for HTTPS request.

| Option | Description | Example |
| --- | --- | --- |
| server-host | Define the IP address to listen to. Use `0.0.0.0` to listen on all interfaces. Use `127.0.0.1` to listen on loopback interface. | 0.0.0.0 |
| server-port | Define the port to listen for HTTP request. Default to `8080` | 9090 |

## Configure External URL

To display the correct URL when sending Email Notification to Minarca users,
you must provide Minarca with the URL your users use to reach the web application.
You can use the IP of your server, but a Fully Qualified Domain Name (FQDN) is preferred.

| Option | Description | Example |
| --- | --- | --- |
| external-url | Define the base URL used to reach your Minarca application | `https://minarca.mycompagny.com` |

## Configure administrator username and password

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

### Enable Debugging

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

```{toctree}
---
titlesonly: true
---
configuration-ldap
```

## Configure User Session

A user session is a sequence of request and response transactions associated with a single user. The user session is the means to track each authenticated user.

| Option | Description | Example |
| --- | --- | --- |
| session-idle-timeout | This timeout defines the amount of time a session will remain active in case there is no activity in the session. User Session will be revoke after this period of inactivity, unless the user selected "remember me". Default 10 minutes. | 5 |
| session-absolute-timeout | This timeout defines the maximum amount of time a session can be active. After this period, user is forced to (re)authenticate, unless the user selected "remember me". Default 20 minutes. | 30 |
| session-persistent-timeout | This timeout defines the maximum amount of time to remember and trust a user device. This timeout is used when user select "remember me". Default 30 days | 43200 |

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
| email-catch-all | When defined, all notification email will be sent to this email address using Blind carbon copy (Bcc) |

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

* `RDIFFWEB_USERID`: minarca user id. e.g.: `34`
* `RDIFFWEB_USERNAME`: minarca username. e.g.: `patrik`
* `RDIFFWEB_USERROOT`: user's root directory. e.g.: `/backups/patrik/`
* `RDIFFWEB_ROLE`: user's role e.g.: `10` 1:Admin, 5:Maintainer, 10:User
* `RDIFFWEB_QUOTA`: only available for `quota-set-cmd`. Define the new quota value in bytes. e.g.: 549755813888  (0.5 TiB)

Continue reading about how to configure quotas for EXT4. We generally
recommend making use of project quotas with Minarca to simplify the management of permission and avoid running Minarca with root privileges.  The next section
presents how to configure project quota. Keep in mind it's also possible to
configure quota using either user's quota or project quota.

### Configure prjquota

#### For EXT4

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

### EXT4

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


## Configure Rate-Limit

Minarca could be configured to rate-limit access to anonymous to avoid bruteforce
attacks and authenticated users to avoid Denial Of Service attack.

| Option | Description | Example |
| --- | --- | --- |
| rate-limit | maximum number of requests per hour that can be made on sensitive endpoints. When this limit is reached, an HTTP 429 message is returned to the user or the user is logged out. This security measure is used to limit brute force attacks on the login page and the RESTful API. | 20 |
| rate-limit-dir | location where to store rate-limit information. When undefined, data is kept in memory. | /var/lib/minarca/session |

## Custom user's password length limits

By default, Minarca supports passwords with the following lengths:

* Minimum: 8 characters
* Maximum: 128 characters

Changing the minimum or maximum length does not affect existing users' passwords. Existing users are not prompted to reset their passwords to meet the new limits. The new limit only applies when an existing user changes their password.

| Option | Description | Example |
| --- | --- | --- |
| password-min-length | Minimum length of the user's password | 8 |
| password-max-length | Maximum length of the user's password | 128 |
| password-score      | Minimum zxcvbn's score for password. Value from 0 to 4. Default value 1. | 4 |

You may want to read more about [zxcvbn](https://github.com/dropbox/zxcvbn) score value.

## Configure Minarca Branding

A number of options are available to customize the appearance of Minarca to your
need. Most likely, you will want to make it closer to your business brand.

| Option | Description | Example |
| --- | --- | --- |
| welcome-msg | Replace the headline displayed in the login page. It may contains HTML. | Custom message displayed on login page.|
| brand-header-name | Define the application name displayed in the title bar and header menu. | My Backup |
| brand-default-theme | Define the theme. Either: `default`, `blue` or `orange`. Define the css file to be loaded in the web interface. | orange |
| brand-favicon | Define the FavIcon to be displayed in the browser title | /etc/minarca/my-fav.ico |
| brand-logo | location of an image (preferably a .png) to be used as a replacement for the Minarca logo displayed in Login page. | /etc/minarca/logo2.png |
| brand-header-logo | location of an image (preferably a .png) to be used as a replacement for the Minarca header logo displayed in navigation bar. | /etc/minarca/logo1.png |
| brand-link-color | define a CSS color to be used for link. | #eeffee |
| brand-btn-fg-color | define a CSS color to use for the button text. Default to white if undefined | #ffffff |
| brand-btn-bg-color | define a CSS color to use for the background of the button. Default to `link-color` if undefined | #eeeeff |
| brand-btn-radius | activate or deactivate the rounded corners of the buttons | 0 |

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

## Configure repository lookup depthness

When defining the UserRoot value for a user, Minarca will scan the content of this directory recursively to lookups for rdiff-backup repositories. For performance reason, Minarca limits the recursiveness to 3 subdirectories. This default value should suit most use cases. If you have a particular use case, it's possible to allow Minarca to scan for more subdirectories by defining a greater value for the option `max-depth`. Make sure to pick a reasonable value for your use case as it may impact the performance.

| Parameter | Description | Example |
| --- | --- | --- |
| --max-depth | Define the maximum folder depthness to search into the user's root directory to find repositories. This is commonly used if your repositories are organised with multiple sub-folders. Default: 3 | 10 |

## Configure default language

By default, the web application uses the HTTP Accept-Language headers to determine the best language to use for display. Users can also manually select a preferred language to use for all communication. The `default-language` setting is used when the user has not selected a preferred language and none of the Accept-Language headers match a translation.

| Parameter | Description | Example |
| --- | --- | --- |
| --default-lang | default application locale. e.g.: `fr` | es |

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

## Configure Storage

```{toctree}
---
titlesonly: true
---
configuration-storage
```

## Configure Version Check

Minarca include a feature to check version and notify administrator if an upgrade is available.

```{toctree}
---
titlesonly: true
---
configuration-latest
```

## Advance Minarca Configuration

Minarca automatically configure where user's backups get stored. You may customize this
by using the following settings. Unless you know what you are doing it's not
recommanded to change any of these settings.

| Parameter | Description | Example |
| --- | --- | --- |
| minarca-user-setup-dir-mode | Permission to be set on the user's folder created by Minarca. (Default: 0700) | 448 (equals to 0700) |
| minarca-user-base-dir | Folder where users repositories should be created. You may need to change this value if you already have your repositories created in a different location or if you are migrating from rdiffweb. Otherwise it's recommended to keep the default value. (Default: /backups/) | /backups/ |
| minarca-restricted-to-based-dir | Used to enforce security by limiting the user's home directories to inside `UserBaseDir`. It's highly recommended to keep this feature enabled. (Default: True) | True |
| minarca-shell | Location of `minarca-shell` used to limit SSH server access. (Default: /opt/minarca-server/minarca-shell) | /opt/minarca-server/minarca-shell |
| minarca-auth-options | Default SSH auth options. This is used to limit the user's permission on the SSH Server, effectively disabling X11 forwarding, port forwarding and PTY. | default='no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty' |
| minarca-remote-host | URL defining the remote SSH identity. This value is queried by Minarca Client to link and back up to the server. If not provided, the HTTP URL is used as a base. You may need to change this value if the SSH server is accessible using a different IP address or if not running on port 22. | ssh.example.com:2222 |
| minarca-remote-host-identity | Location of SSH server identity. This value is queried by Minarca Client to authenticate the server. You may need to change this value if SSH service and the Web service are not running on the same server. (Default: /etc/ssh) | /etc/ssh |