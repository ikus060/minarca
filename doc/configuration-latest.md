# Server Version Check

The Minarca Version Check feature is designed to automatically check for
the latest version of Minarca and notify the administrator via email if
a new version is available. This feature is enabled by default and can be
customized according to your needs.

## How it works

The Version Check feature works by comparing the version number of the
Minarca Server installation against the latest available version number,
which is obtained from the URL specified in the "latest-version-url"
configuration option. If the version number of the Minarca installation
is lower than the latest available version number, an email notification
is sent to the administrator.

By default, the "latest-version-url" configuration option is set to
"https://latest.ikus-soft.com/minarca/latest_version". This URL contains
the latest version number of Minarca in a plain text format.

However, administrators can customize this option by editing the "minarca-server.conf"
configuration file and setting the "latest-version-url" option to a
different URL if desired.

## Disabling the feature

If you wish to disable the Version Check feature, you can do so by setting
the "latest-version-url" configuration option to an empty value.
This can be done by editing the "minarca-server.conf" configuration file and
setting the option like this:

```ini
latest-version-url = 
```

By setting the "latest-version-url" option to an empty value, Minarca will
no longer check for the latest version of the software and will not send
email notifications to the administrator if a new version is available.

It's important to note that disabling the Version Check feature means
that you will need to manually check for updates and upgrade Minarca when a
new version is available. Therefore, it's recommended to keep this feature
enabled to ensure that you are running the latest version of Minarca.
