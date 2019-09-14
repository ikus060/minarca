# Minarca Server Documentation

## Installation

On a Debian Linux server:

    wget http://www.patrikdufresne.com/archive/minarca/minarca-server_latest_all.deb
    apt install minarca-server_latest_all.deb

This should install Minarca server and all required dependencies. The server should be running on http://127.0.0.1:8080 listening on all interfaces.

You may stop start the service using systemd:

    sudo service minarca-server stop
    sudo service minarca-server start
    
Once insatalled, read how to configure minarca-server.

## Migrating from rdiffweb to minarca-server

If you already have an installation of rdiffweb, you may migrate relatively
easily to minarca-server. To migrate from rdiffweb to minarca-server, you must
first uninstall rdiffweb.

1. Uninstall rdiffweb

    sudo service rdiffweb stop
    sudo pip remove rdiffweb
    
2. Migrate rdiffweb user database

Rdiffweb is persisting users database in `/etc/rdiffweb` while minarca-server
is persisting the data to `/etc/minarca`. If you want to keep your users
preferences, you must copy the database to minarca folder.

    cp /etc/rdiffweb/rdw.db /etc/minarca/rdw.db

4. Install minarca server

Proceed with the installation of minarca-server.

    wget http://www.patrikdufresne.com/archive/minarca/minarca-server_latest_all.deb
    apt install minarca-server_latest_all.deb
    
5. Review minarca-server configuration

When installing minarca-server, a new configuration file get created in
`/etc/minarca/minarca-server.conf`. You should review the configuration file
according to your previous rdiffweb configuration.

Make sure to set `MinarcaRestrictedToBasedDir` to `false` if your user's home
directory are not located under a single directory.

Restart the service when you are done reviewing the configuration.

    sudo service minarca-server restart

6. Change permissions 

Minarca web server is not running as root and required the data to be readable
and writable by minarca user. If you backups are all located under `/backups/`
as it was recommended by rdiffweb documentation. You may run the following
command to update the permissions.

    sudo chown -R minarca:minarca /backups/

## Setup Storage

Compared to rdiffweb, Minarca intend to take over the management of your storage and for that reason,
need to enforce some rules regarding how your storage should be layout.

You need to define a folder where all your backups will reside. Everything under this folder will then be managed by Minarca. By default, this folder is `/backups`. If you want a different folder update the parameter `MinarcaUserBaseDir` in minarca configuration.

When installing, this folder will be created with the right ownership and permissions. If you have created this folder your self, make sure the ownership is set to `minarca:minarca` and permissions to `-rwxr-x---`.

    chown minarca:minarca /backups/
    chmod 7500 /backups/


## Configuration

Since Minarca Server is built on top of rdiffweb, you may take a look at [rdiffweb configiuration](https://github.com/ikus060/rdiffweb/).

You may also change Minarca's configuration in `/etc/minarca/minarca-server.conf`:

| Parameter | Description | Required | Example |
| --- | --- | --- | --- |
| MinarcaQuotaApiUrl | URL to a minarca-quota-api service to be used to get/set user's quota. | No | http://minarca:secret@localhost:8081/ | 
| MinarcaUserSetupDirMode | Permission to be set on the user's folder created by Minarca. (Default: 0700) | No | 0o0700 |
| MinarcaUserBaseDir | Folder where users repositories should be created. You may need to change this value if you already have your repositories created in a different location or if you are migrating from rdiffweb. Otherwise it's recommended to keep the default value. (Default: /backups/) | No | /backups/ |
| MinarcaRestrictedToBasedDir | Used to enforce security by limiting the user's home directories to inside `UserBaseDir`. It's highly recommended to keep this feature enabled. (Default: True) | No | True |
| MinarcaShell | Location of `minarca-shell` used to limit SSH server access. (Default: /opt/minarca/bin/minarca-shell) | No | /opt/minarca/bin/minarca-shell | 
| MinarcaAuthOptions | Default SSH auth options. This is used to limit the user's permission on the SSH Server, effectively disabling X11 forwarding, port forwarding and PTY. | No | default='no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty' |
| MinarcaRemoteHost | URL defining the remote SSH identity. This value is queried by Minarca Client to link and back up to the server. If not provided, the HTTP URL is used as a base. You may need to change this value if the SSH server is accessible using a different IP address or if not running on port 22. | No | ssh.example.com:2222 |
| MinarcaRemoteHostIdentity | Location of SSH server identity. This value is queried by Minarca Client to authenticate the server. You may need to change this value if SSH service and the Web service are not running on the same server. (Default: /etc/ssh) | No | /etc/ssh | 

    

