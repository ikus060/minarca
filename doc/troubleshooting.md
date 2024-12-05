# Troubleshooting

## Minarca Server

For effective troubleshooting, it's crucial to know where to locate the logs and configuration files associated with your Minarca Server.

### Log Files

By default, all Minarca Server log files are stored in the `/var/log/minarca` directory.

- **server.log**: Logs related to the web interface server.
- **shell.log**: Logs from the `minarca-shell` component, which handles SSH connections. This file contains records of agents connecting to the server for data backups.
- **access.log**: An Apache-compatible access log that tracks all HTTP requests made to the web interface.
- **quota-api.log**: Logs from the `minarca-quota-api` component, if installed.

If you're experiencing issues with connecting your Minarca Client to the server, you may also need to review the `/var/log/auth.log` file. This file contains SSH authentication logs, which can help diagnose connectivity problems.

## Minarca Client

When troubleshooting, it is essential to know where to find the logs, settings, and status files. The locations of these files differ depending on the operating system you are using: Windows, Linux, or macOS.

### Windows

#### Windows Log File
The log file, which is essential for diagnosing issues, can be found at:
```
%LOCALAPPDATA%/minarca/minarca.log
```
Typically, `%LOCALAPPDATA%` defaults to `%HOME%/AppData/Local`.

#### Windows Settings Folder
The settings for Minarca are stored in the following directory:
```
%LOCALAPPDATA%/minarca/
```

#### Windows Status Folder
Status files, which help in understanding the current state of backups and other operations, are located at:
```
%LOCALAPPDATA%/minarca/
```

### Linux

#### Linux Log File
On Linux systems, the log file is generally stored in the following directory:
```
$XDG_DATA_HOME/minarca/minarca.log
```
`$XDG_DATA_HOME` typically defaults to `$HOME/.local/share`.

#### Linux Settings Folder
The settings files are found in the configuration directory:
```
$XDG_CONFIG_HOME/minarca/
```
`$XDG_CONFIG_HOME` typically defaults to `$HOME/.config/`.

#### Linux Status Folder
Status files are stored in the following directory:
```
$XDG_DATA_HOME/minarca/
```
`$XDG_DATA_HOME` typically defaults to `$HOME/.local/share`.

#### Running as Root on Linux

If Minarca is running as root, the file locations change as follows:

- **Log File:** `/var/log/minarca.log`
- **Settings Folder:** `/etc/minarca/`
- **Status Folder:** `/var/lib/minarca/`

### MacOS

#### MacOS Log File
On macOS, the log file for Minarca can be found at:
```
$HOME/Library/Logs/Minarca/minarca.log
```

#### MacOS Settings Folder
The settings files are stored in the preferences directory:
```
$HOME/Library/Preferences/Minarca
```

#### MacOS Status Folder
Status files are found in the following directory:
```
$HOME/Library/Minarca
```

### Customizing File Locations

On all platforms, it is possible to change the location of the settings and status folders using environment variables:

- **Settings Folder:** Set the `$MINARCA_CONFIG_HOME` environment variable.
- **Status Folder:** Set the `$MINARCA_DATA_HOME` environment variable.

### Additional Tips

By knowing where to find these essential files, troubleshooting Minarca Data Backup becomes a more straightforward process. If you encounter issues that cannot be resolved through these files, consider reaching out to Minarca support with the log and status files for further assistance.
