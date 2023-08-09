# Command Line Interface

Minarca provide a command-line tool designed to manage your computer's backups by linking your system with a centralized server and executing backups on a specified schedule. This documentation outlines the various sub-commands and their associated options for interacting with Minarca.

## Installation

Before using Minarca, ensure it is properly installed on your system. The executable should be accessible in your `PATH` environment variable.

## Usage

```sh
minarca [-h] [-v] [-d] {command} ...
```

- `-h`, `--help`: Show the help message and exit.
- `-v`, `--version`: Show the program's version number and exit.
- `-d`, `--debug`: Enable debug mode.

## Commands

The following commands are available in the Minarca CLI:

### `start`

Start a backup in background mode.

```sh
minarca start [-h] [--force]
```

- `-h`, `--help`: Show the help message and exit.
- `--force`: Force the execution of a backup even if it's not time to run.

### `backup`

Start a backup in foreground mode.

```sh
minarca backup [-h] [--force]
```

- `-h`, `--help`: Show the help message and exit.
- `--force`: Force the execution of a backup even if it's not time to run.

### `exclude`

Exclude files from the backup.

```sh
minarca exclude [-h] pattern [pattern ...]
```

- `-h`, `--help`: Show the help message and exit.
- `pattern`: File pattern(s) to be excluded. Wildcards (`*` or `?`) can be used.

### `include`

Include files in the backup.

```sh
minarca include [-h] pattern [pattern ...]
```

- `-h`, `--help`: Show the help message and exit.
- `pattern`: File pattern(s) to be included. Wildcards (`*` or `?`) can be used.

### `link`

Link the Minarca backup with a Minarca server.

```sh
minarca link [-h] [-r REMOTEURL] [-u USERNAME] [-p PASSWORD] [-n NAME] [--force]
```

- `-h`, `--help`: Show the help message and exit.
- `-r REMOTEURL`, `--remoteurl REMOTEURL`: URL to the remote Minarca server.
- `-u USERNAME`, `--username USERNAME`: User name for authentication.
- `-p PASSWORD`, `--password PASSWORD`: Password or access token for authentication. Will prompt if not provided.
- `-n NAME`, `--name NAME`: Repository name to be used.
- `--force`: Link to the remote server even if the repository name already exists.

### `patterns`

List the includes/excludes patterns.

```sh
minarca patterns [-h]
```

- `-h`, `--help`: Show the help message and exit.

### `restore`

Restore data from backup.

```sh
minarca restore [-h] [--restore-time RESTORE_TIME] [--force] [pattern [pattern ...]]
```

- `-h`, `--help`: Show the help message and exit.
- `--restore-time RESTORE_TIME`: Date/time to be restored (e.g., 'now', epoch value, ISO date format, interval).
- `--force`: Force execution of the restore operation without user confirmation.
- `pattern`: Files and folders to be restored.

### `stop`

Stop the backup.

```sh
minarca stop [-h] [--force]
```

- `-h`, `--help`: Show the help message and exit.
- `--force`: Don't fail if the backup is not running.

### `schedule`

Create required schedule tasks.

```sh
minarca schedule [-h] [--hourly] [--daily] [--weekly]
```

- `-h`, `--help`: Show the help message and exit.
- `--hourly`: Schedule backup to run hourly.
- `--daily`: Schedule backup to run daily.
- `--weekly`: Schedule backup to run weekly.

### `status`

Return the current Minarca status.

```sh
minarca status [-h]
```

- `-h`, `--help`: Show the help message and exit.

### `unlink`

Unlink the Minarca agent from the server.

```sh
minarca unlink [-h]
```

- `-h`, `--help`: Show the help message and exit.

### `pause`

Temporarily delay the backup execution.

```sh
minarca pause [-h] [-d DELAY] [-c [DELAY]]
```

- `-h`, `--help`: Show the help message and exit.
- `-d DELAY`, `--delay DELAY`: Number of hours to delay the backup.
- `-c [DELAY]`, `--clear [DELAY]`: Clear a previously set delay.

## Examples

```bash
# Start a background backup
minarca start

# Exclude files with specific patterns
minarca exclude '*.log' '*.tmp'

# Link Minarca backup with a remote server
minarca link -r http://example.com:8080/ -u user -p pass -n myrepo

# Restore specific files from backup
minarca restore --restore-time '3D' file.txt

# Schedule daily backups
minarca schedule --daily

# Check Minarca status
minarca status

# Pause backup for 6 hours
minarca pause -d 6
```

This documentation provides an overview of the Minarca CLI and its available sub-commands. For more detailed information on each sub-command, refer to the respective help documentation using the `--help` option.