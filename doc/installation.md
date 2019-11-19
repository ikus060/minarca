# Minarca-Server Installation

# Install on new server

On a Debian Linux server:

    wget http://www.patrikdufresne.com/archive/minarca/minarca-server_latest_amd64.deb
    apt install minarca-server_latest_amd64.deb

This should install Minarca server and all required dependencies. The server should be running on http://127.0.0.1:8080 listening on all interfaces.

You may stop start the service using systemd:

    sudo service minarca-server stop
    sudo service minarca-server start
    
Once installed, continue reading about how to configure minarca-server.

## Setup Storage

Compared to rdiffweb, Minarca intend to take over the management of your storage and for that reason,
need to enforce some rules regarding how your storage should be layout.

You need to define a folder where all your backups will reside. Everything under this folder will then be managed by Minarca. By default, this folder is `/backups`. If you want a different folder update the parameter `MinarcaUserBaseDir` in minarca configuration.

When installing, this folder will be created with the right ownership and permissions. If you have created this folder your self, make sure the ownership is set to `minarca:minarca` and permissions to `-rwxr-x---`.

    chown minarca:minarca /backups/
    chmod 0750 /backups/
