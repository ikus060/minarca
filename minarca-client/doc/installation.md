# Installation

## System requirements

We recommend using high quality server hardware when running Minarca in production, mainly for storage.

### Minimum server requirement for evaluation

These minimum requirements are solely for evaluation and shall not be used in a production environment :

* Cpu 64bit x86-64 or amd64, 2 core
* Memory : 2 GiB RAM
* Hard drive/storage more than 8 GiB

### Recommended server requirement

* Supported Operating System:
  * Debian Buster
  * Debian Bullseye
  * Ubuntu Groovy
  * Ubuntu Hirsute
* Cpu: 64bit x86-64 or amd64, 4 core
* Memory: minimum 4 GiB
* Storage: consider the storage according to your backup needs. A couple of terabytes should be considered for the long term. Ideally, you should consider hardware or ZFS raid for your storage. If you plan to support user quota, make sure that your file system supports it. E.g. ext4 and ZFS. Other file systems might not be well supported.
* Temporary storage: Rdiffweb requires a temporary storage location that is used during the restoration process. This location should be greater than 8gb. This temporary storage will be closer to the web application. Ideally, it should be in ram using tmpfs.

### Minarca agent requirement

* Supported Operating System:
  * Windows (64bit)
  * Mac OS (Intel)
  * Debian Buster (64bit)
  * Debian Bullseye (64bit)
  * Ubuntu Groovy (64bit)
  * Ubuntu Hirsute (64bit)
  * Linux (64bit)

## Minarca Server installation

Two different solutions are available to install Minarca Server. You should pick the right solution for your environment.

### Option 1. Quick automated installation

On a Debian Linux server:

    curl -L https://www.ikus-soft.com/archive/minarca/get-minarca.sh | sh -

This should install Minarca server and all required dependencies.

The server should be running on http://127.0.0.1:8080 listening on all interfaces.

You may stop or start the service using systemd:

    sudo service minarca-server stop
    sudo service minarca-server start

Once installed, continue reading about how to configure minarca-server.

You may access the web interface at http://localhost:8080 using:

    * username: admin
    * password: admin123 

### Option 2. Step-by-Step installation

On a Debian Linux server:

    sudo apt-get update
    sudo apt-get install apt-transport-https ca-certificates gnupg
    curl -L https://www.ikus-soft.com/archive/minarca/public.key | sudo apt-key add -
    echo "deb https://nexus.ikus-soft.com/repository/apt-release-buster/ buster main" | sudo tee /etc/apt/sources.list.d/minarca.list
    apt-get update
    apt-get install minarca-server

## Setup Storage

Compared to Rdiffweb, Minarca intend to take over the management of your storage and for that reason,
need to enforce some rules regarding how your storage should be layout.

You need to define a folder where all your backups will reside. Everything under this folder will then be managed by Minarca. By default, this folder is `/backups`. If you want a different folder update the parameter `MinarcaUserBaseDir` in minarca configuration.

When installing, this folder will be created with the right ownership and permissions. If you have created this folder your self, make sure the ownership is set to `minarca:minarca` and permissions to `-rwxr-x---`.

    chown minarca:minarca /backups/
    chmod 0750 /backups/

## Setup SSH Server

On a fresh Debian installation, Minarca is working fine with the default SSH server
configuration (etc/ssh/sshd_config), but if you have enforce some configuration in your SSH
server, you may need to update it's configuration to allow "minarca" user to authenticate.

Something similar to the following should make it work in most environment:

    Match User minarca
            PubkeyAuthentication yes
            PasswordAuthentication no
            AllowGroups minarca
            X11Forwarding no
            AllowTcpForwarding no
            PermitTTY no

## Migrating from Rdiffweb to Minarca

If you already have an installation of Rdiffweb, you may migrate relatively
easily to Minarca. To migrate from Rdiffweb to Minarca, you must
first uninstall Rdiffweb.

### 1. Uninstall Rdiffweb

    sudo service rdiffweb stop
    sudo pip remove rdiffweb

### 2. Migrate Rdiffweb user database

Rdiffweb is persisting users database in `/etc/rdiffweb` while Minarca
is persisting the data to `/etc/minarca`. If you want to keep your users
preferences, you must copy the database to Minarca folder.

    cp /etc/rdiffweb/rdw.db /etc/minarca/rdw.db

### 4. Install Minarca server

Proceed with the installation of Minarca.

    wget https://www.ikus-soft.com/archive/minarca/minarca-server_latest_amd64.deb
    apt install minarca-server_latest_amd64.deb

### 5. Review Minarca configuration

When installing Minarca, a new configuration file get created in
`/etc/minarca/minarca-server.conf`. You should review the configuration file
according to your previous Rdiffweb configuration.

Make sure to set `MinarcaRestrictedToBasedDir` to `false` if your user's home
directory are not located under a single directory.

Restart the service when you are done reviewing the configuration.

    sudo service minarca-server restart

### 6. Change permissions 

Minarca web server is not running as root and required the data to be readable
and writable by minarca user. If you backups are all located under `/backups/`
as it was recommended by Rdiffweb documentation. You may run the following
command to update the permissions.

    sudo chown -R minarca:minarca /backups/
