# Minarca Storage

This documentation provides details on how to configure the storage settings for Minarca, a backup solution. Properly configuring the storage location and directory structure is essential to ensure efficient and reliable backup operations.

## Setup Storage Location

By default, Minarca stores backups in the `/backups/` directory. This location must be on a reliable storage media with a POSIX filesystem to ensure data integrity and consistency.

It's possible to define an alternate location by updating the value of `minarca-user-base-dir` in the `minarca-server.conf` file on the Minarca server.

To configure an alternate storage location:

1. Open the "minarca-server.conf" file on the Minarca server using a text editor.

2. Locate the or add `minarca-user-base-dir` parameter and update it to the desired path for your storage location. For example, if you want to use "/home/minarca/", the configuration should be:

        minarca-user-base-dir = /home/minarca/

3. After updating the location, ensure that the ownership of this new location is set to "minarca:minarca" with the permissions "-rwxr-x---" using the following command:

        sudo mkdir /home/minarca/
        sudo chown minarca:minarca /home/minarca/
        sudo chmod 750 /home/minarca/

4. In addition, you must also change the home folder of the minarca user to the new location to allow SSH connection.

        sudo usermod -d /home/minarca/ minarca

Remember that changing the storage location might require you to manually copy the data from old location to new location.

You must also manually update the user's root directoryfor each user using the web interface.

## Storage Directory Structure

Minarca follows a specific directory hierarchy for organizing backups, as shown below:

    /<minarca-user-base-dir>/<username>/<repository>

For example, if the Minarca user is "john_doe", the backups will be stored in the following directory by default:

    /backups/john_doe/<repository>

The `<repository>` is the name of the repository where backups for specific data are stored.

## User's Root Directory

The user's root directory defines the specific location used to store a user's backups, as defined by the Storage directory structure explained above. This location is automatically set when creating a new user in Minarca. However, administrators have the option to manually update this root directory if needed.

To manually update the user's root directory:

1. Login to Minarca web interface
2. Click on "Admin Area" then on "Users"
3. Locate the user you want to update and click on "Edit"
4. Update the path to the desired location for the user's root directory.

Please note that when updating the user's root directory, you will need to manually move the existing data from the old location to the new one using the command line. Ensure that the data transfer is performed securely and without any data loss.

## User's identity

In Minarca, the user's identity is managed through the use of SSH key pairs. SSH keys provide a secure and convenient way to authenticate computers and allow them to access the backup server without the need for a password. The user's public SSH key is stored in the `/<minarca-user-base-dir>/.ssh/authorized_keys` file.

SSH key authentication works based on a pair of cryptographic keys: a private key and a public key. The private key should be kept confidential and securely stored on the user's local machine. On the other hand, the public key can be freely shared with the server.

When a computer attempts to access the Minarca server, the server checks the computer's public key against the list of authorized keys stored in the `authorized_keys` file. If the public key matches any of the authorized keys, the computer is granted access without the need to enter a password.

Minarca is automatically creating and updating this `authorized_keys` as needed when a new computer is linked to a user account.

The system administrator's responsibility is to ensure that the SSHD server recognizes the required file. This can be achieved by setting the minarca-user-base-dir value to match the Minarca user's home directory in Linux.

To accomplish this, the administrator can use the following command:

    sudo usermod -d /home/minarca/ minarca

By executing this command, the home directory for the linux user named "minarca" will be set to "/home/minarca/". Additionally, the -m option will ensure that any existing files associated with the user are moved to the new home directory, ensuring a seamless transition.
