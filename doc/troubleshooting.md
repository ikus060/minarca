# Troubleshooting

## Minarca Server

For effective troubleshooting, it's crucial to know where to locate the logs and configuration files associated with your Minarca Server.

### Log Files (server)

By default, all Minarca Server log files are stored in the `/var/log/minarca` directory.

- **server.log**: Logs related to the web interface server.
- **shell.log**: Logs from the `minarca-shell` component, which handles SSH connections. This file contains records of agents connecting to the server for data backups.
- **access.log**: An Apache-compatible access log that tracks all HTTP requests made to the web interface.
- **quota-api.log**: Logs from the `minarca-quota-api` component, if installed.

If you're experiencing issues with connecting your Minarca Client to the server, you may also need to review the `/var/log/auth.log` file. This file contains SSH authentication logs, which can help diagnose connectivity problems.


Here's a revised version of your text that makes use of tables to improve readability and clarity.  

---

## Minarca Client

When troubleshooting, it is essential to know where to find the logs, settings, and status files. The locations of these files differ depending on the operating system you are using: Windows, Linux, or macOS.

### Log Files (client)

| **Operating System** | **Log File**                             | 
|----------------------|------------------------------------------|
| **Windows**          | `%LOCALAPPDATA%/minarca/minarca.log`<br>*e.g.: `c:/Users/my-user/AppData/Local/minarca/minarca.log`*     |
| **Linux**            | `$XDG_DATA_HOME/minarca/minarca.log`<br>*e.g.: `/home/my-user/.local/share/minarca/minarca.log`* |
| **Linux (root)**     | `/var/log/minarca.log`                   |
| **macOS**            | `$HOME/Library/Logs/Minarca/minarca.log`<br>*e.g.: `/Users/myuser/Library/Logs/Minarca/minarca.log`*  |

### Troubleshooting: "0x800710E0" Error in Windows Task Scheduler

When using the Minarca Data Backup client, you may encounter the following error in the Windows Task Scheduler:

```
0x800710E0: The operator or administrator has refused the request.
```

* **Cause**: This error occurs when the task is configured to **run only when the user is logged on**, but the required conditions for an interactive logon are not met. This typically happens if:
    - The user is logged off.
    - The task is configured to run interactively but cannot start due to a lack of an active user session.

* **Resolution Steps**: To resolve the "0x800710E0" error, adjust the task's configuration to ensure it can run regardless of whether the user is logged on.
    - Open the **Minarca Client**
    - Select **Backup Configuration**
    - Check the box for **Run whether the user's session is open or not**
    - Enter your **Windows credentials**
