# Runtime Settings

This section describes the settings available from the web interface
and that are editable at runtime in opposition to configuration that
are defined at application startup.

## Users' roles & permissions

In the administration view, you may create a new user to give him access to Minarca
user interface. That would allow him to connect to Minarca with a username and a
password that you define. In addition, you must also assign a user’s role to this
newly created user.

The following table lists permissions available for each role:

| Action | User | Maintainer | Admin
| ------ |:----:|:---:|:---:|
| Browse one of his repositories                               | ✓ | ✓ | ✓ |
| View Graphs, logs and status of his repositories             | ✓ | ✓ | ✓ |
| Retrieve a file or a directory from one of his repositories  | ✓ | ✓ | ✓ |
| Modify the encoding of one of his repositories               | ✓ | ✓ | ✓ |
| Modify the encoding of one of his repositories               | ✓ | ✓ | ✓ |
| Modify the notification parameters (email and delay)         | ✓ | ✓ | ✓ |
| Change his password                                          | ✓ | ✓ | ✓ |
| Adding new SSH Key                                           | ✓ | ✓ | ✓ |
| Deleting an SSH Key                                          |   | ✓ | ✓ |
| Delete one of his repositories                               |   | ✓ | ✓ |
| Delete the history of a file or folder from his repositories |   | ✓ | ✓ |
| Modify the retention period of one of his repositories       |   | ✓ | ✓ |
| View system logs                                             |   |   | ✓ |
| View system information (RAM, CPU, version, dependencies)   |   |   | ✓ |
| Create new users                                             |   |   | ✓ |
| Modify other user's email, password and role                 |   |   | ✓ |
| Define other user's quota                                    |   |   | ✓ |
| Delete other user's repository                               |   |   | ✓ |
| Delete the history of a file or folder from other users      |   |   | ✓ |
| Browse other user's repository                               |   |   | ✓ |

