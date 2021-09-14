# Minarca Server Configuration options

Minarca Server is configured by setting the relevant options in `/etc/minarca/minarca-server.conf`.
New installation will have a new file created with default values to get started.

## Customize Minarca Server with your brand

As a service provider, you may like to cutomized the look and feel of Minarca's
web interfaces to matches your branding.

You may start by replacing "Minarca" with your company name by setting the 
`HeaderName` configuration. This value will be used in page's title and
in the navigation bar.

    HeaderName=My Company name - Backups

You may also provide your own logo to replace the default one. You must have a
`.png` file and a `.ico` file deployed on the server.

	FavIcon=/etc/minarca-server/my-brand.ico
	HeaderLogo=/etc/minarca-server/my-logo-22.png

You may also replace the welcome message displayed in the login page where users
are redirected to authenticate. You may include HTML tags in this option to
provide link to your website as an example. You may also provide localized
value for this options using `[..]`.

    WelcomeMsg=A <b>welcome</b> message to be displayed to the user.
    WelcomeMsg[fr]=Un message <b>de bienvenue</b> à afficher à l'utilisateur.

You may also pick a different color scheme to matches your branding. Only two
theme are available: `default`, `blue`, `orange`. You may request a new color scheme
using a [support request](https://www.ikus-soft.com/en/support/#form).

    DefaultTheme=default
    
It's also possible to customized how the users are reaching your company by
defining a custom web page. By defining this option, users needing your help
from the Minarca client application will be redirect to this page instead of
the default Minarca web site.

    MinarcaHelpURL = https://my-company.com/support

## Configure email notification

To allow Minarca server to send notifications to the users regarding broken
backups, password or email changes, you must first configure the SMTP settings.

Note: the value `HeaderName` is used in email's template. You may want to
change this option for your compagny's name.

**EmailSendChangedNotification**

Define if email should be sent when user's password or user's email are updated.

Default value: `false`

Valid options: `false`, `true`

**EmailNotificationTime**

Define when Minarca should send notifications about the backup being broken.

Default value: `23:00`

## SMTP settings

If you want Minarca to send email via an SMTP server for notifications, add the following configuration information to `/etc/minarca/minarca-server.conf`.

    EmailHost=smtp.server:465
    EmailEncryption=starttls
    EmailSender=example@gmail.com
    EmailUsername=example@gmail.com
    EmailPassword=CHANGEME

**EmailHost**

Define the address of the SMTP server. Should define a valid FQDN or and IP address with a port.

e.g.: `smtp.server:465`

**EmailEncryption**

Define if encryption must be used to communicate with the SMTP server.

Default value: `none`

Valid options: `none`, `ssl`, `starttls`

**EmailSender**

Changes the 'From' fields with this setting. By default, the 'From' field will
include the `HeaderName` value.

**EmailUsername**

Define the username used to authenticate with the server.

**EmailPassword**

Define the password used to authenticate with the server.

### Example configurations

#### Gmail

Note: Gmail has strict [sending limits](https://support.google.com/a/answer/166852) that must be considered.

    #----- Enable Email Notification
    # The server can be configured to email user when their repositories have not
    # been backed up for a user-specified period of time. To enable this feature,
    # set below settings to correct values.
    EmailHost=smtp.gmail.com:587
    EmailEncryption=starttls
    EmailSender=example@gmail.com
    EmailUsername=example@gmail.com
    EmailPassword=CHANGEME

## Change logging settings

Minarca provide default logging location and logging level. You may adapt this for your need using the `LogAccessFile`, `LogFile` and `LogLevel`.

    LogAccessFile=/var/log/minarca/access.log
    LogFile=/var/log/minarca/server.log
    LogLevel=DEBUG

## Change Temporary Folder

Minarca is using the `/tmp` folder as a working directory to restore data. Depending of your setup, this folder might have limited disk space. To mitigate this problem you may provide an alternate folder to be used.

    TempDir=/var/tmp/

## Change database location

You may change the database location to be used. If the file doesn't exists,
Minarca will create a new own on startup.

    SQLiteDBFile=/full/path/to/sqlite.db

## Configure user's Home directory

Compare to rdiffweb, Minarca will automatically manage the user's home
directory for you. Minarca will create the directory with proper permissions
and ownership.

## Configure User's Quota (in developement)

Read the quota configuration.

## Advance Minarca settings

| Parameter | Description | Required | Example |
| --- | --- | --- | --- |
| MinarcaUserSetupDirMode | Permission to be set on the user's folder created by Minarca. (Default: 0700) | No | 448 (equals to 0700) |
| MinarcaUserBaseDir | Folder where users repositories should be created. You may need to change this value if you already have your repositories created in a different location or if you are migrating from rdiffweb. Otherwise it's recommended to keep the default value. (Default: /backups/) | No | /backups/ |
| MinarcaRestrictedToBasedDir | Used to enforce security by limiting the user's home directories to inside `UserBaseDir`. It's highly recommended to keep this feature enabled. (Default: True) | No | True |
| MinarcaShell | Location of `minarca-shell` used to limit SSH server access. (Default: /opt/minarca-server/bin/minarca-shell) | No | /opt/minarca-server/bin/minarca-shell | 
| MinarcaAuthOptions | Default SSH auth options. This is used to limit the user's permission on the SSH Server, effectively disabling X11 forwarding, port forwarding and PTY. | No | default='no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty' |
| MinarcaRemoteHost | URL defining the remote SSH identity. This value is queried by Minarca Client to link and back up to the server. If not provided, the HTTP URL is used as a base. You may need to change this value if the SSH server is accessible using a different IP address or if not running on port 22. | No | ssh.example.com:2222 |
| MinarcaRemoteHostIdentity | Location of SSH server identity. This value is queried by Minarca Client to authenticate the server. You may need to change this value if SSH service and the Web service are not running on the same server. (Default: /etc/ssh) | No | /etc/ssh |
