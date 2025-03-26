:::{sphinx_argparse_cli}
   :module: minarca_client.main
   :func: _parse_args
   :prog: minarca
   :group_title_prefix:
   :title: Usage

# Minarca CLI interface

## Quick reference

```bash
# Link Minarca client with a remote server
minarca configure -r http://example.com:8080/ -u user -p pass -n myrepo

# Schedule daily backups
minarca schedule --daily

# Include files in backup
minarca include '/etc' '/home/'

# Exclude files with specific patterns
minarca exclude '*.log' '*.tmp'

# Start backup in background
minarca start

# Restore specific files from backup
minarca restore --restore-time '3D' file.txt

# Check Minarca status
minarca status

# Pause backup for 6 hours
minarca pause -d 6
```