# Server Installation

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
  * Debian Bookworm
  * Ubuntu Jammy 22.04 LTS
  * Ubuntu Kinetic 22.10
  * Ubuntu Lunar 23.04
  * Ubuntu Mantic 23.10
* Cpu: 64bit x86-64 or amd64, 4 core
* Memory: minimum 4 GiB
* Storage: consider the storage according to your backup needs. A couple of terabytes should be considered for the long term. Ideally, you should consider hardware or ZFS raid for your storage. If you plan to support user quota, make sure that your file system supports it. E.g. ext4 and ZFS. Other file systems might not be well supported.
* Temporary storage: Rdiffweb requires a temporary storage location that is used during the restoration process. This location should be greater than 8gb. This temporary storage will be closer to the web application. Ideally, it should be in ram using tmpfs.

### Compatibility Matrix

Here's a compatibility matrix for Minarca Server and Minarca Agent:

| Agent                      | v6.* | v5.x | v4.5 - v4.3 | v4.2 - v4.0 | v3.x |
| -------------------------- | ---- | ---- | ----------- | ----------- | ---- |
| Minarca Server v6.*        | ✓    | ✓    | ✓           | ✓ (1)       | ✓ (1)|
| Minarca Server v5.*        | ✓ (2)| ✓    | ✓           | ✓ (1)       | ✓ (1)|
| Minarca Server v4.5 - v4.3 |      |      | ✓           | ✓ (1)       | ✓ (1)|
| Minarca Server v4.2 - v4.0 |      |      | ✓ (1)       | ✓ (1)       | ✓ (1)|
| Minarca Server v3.*        |      |      |             |             | ✓    |

1. Supported only if the agent is already configured. 
2. Some features are not supported.

## Installation Steps

On a Debian Linux server:

    apt update
    apt upgrade
    apt install apt-transport-https ca-certificates curl lsb-release gpg
    curl -L https://www.ikus-soft.com/archive/minarca/public.key | gpg --dearmor > /usr/share/keyrings/minarca-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/minarca-keyring.gpg] https://nexus.ikus-soft.com/repository/apt-release-$(lsb_release -sc)/ $(lsb_release -sc) main" > /etc/apt/sources.list.d/minarca.list
    apt update
    apt install minarca-server

The server should be running on http://127.0.0.1:8080 listening on all interfaces. For a production deployment, it is strongly recommended to configure a reverse proxy with SSL termination like Nginx or Apache.

You may stop or start the service using systemd:

    sudo service minarca-server stop
    sudo service minarca-server start

Once installed, continue reading about how to configure minarca-server.

You may access the web interface at http://127.0.0.1:8080 using:

    * username: admin
    * password: admin123 

## Configure Storage

As an additional steps to the installation, you may want to change the location used to store the backups. By default, this location is `/backups/` and may be changed to an alternate location.

[Read how to configure Minarca storage](configuration-storage)

## Setup SSH Server

On a fresh Debian installation, Minarca is working fine with the default SSH server
configuration (etc/ssh/sshd_config), but if you have enforce some configuration in your SSH
server, you may need to update its configuration to allow "minarca" user to authenticate.

Something similar to the following should make it work in most environment:

    Match User minarca
            PubkeyAuthentication yes
            PasswordAuthentication no
            AllowGroups minarca
            X11Forwarding no
            AllowTcpForwarding no
            PermitTTY no

## Minarca with Docker or LXC

When installing Minarca into a dedicated server or a virtual machine, the
process is seamless. If you are installing Minarca in a container like
Docker or LXC, you must pay attention to configure the container properly.

Minarca-Shell, the component responsible to handle SSH connection and isolate
each user's connection, is using a Kernel feature
called [user namespaces](https://man7.org/linux/man-pages/man7/user_namespaces.7.html).
This feature is used by Minarca-Shell to create a chroot jail to completely
isolate each user SSH connection. That same feature is used by many applications
for improved hardening. Without this feature, Minarca-Shell will refuse any incoming
SSH connection and throw errors.

When installing Minarca on a dedicated server or a virtual machine, the installation
process take care of enabling this feature if not already enabled. When installing Minarca
in a container, it's not enough because this feature might be disabled by your container
orchestration like Docker or LXC.

### For Docker

The container needs to be started with `privileged`:

    docker run -privileged

### For LXC

The container need to be started with `security.nesting`:

    lxc launch ubuntu nestc1 -c security.nesting=true

### For Proxmox VE (lxc)

The container must be configured with feature `nesting=1`.

Edit `/etc/pve/lxc/100.conf` by adding:

    features: nesting=1

## Migrating from Rdiffweb to Minarca

If you already have an installation of Rdiffweb, you may migrate relatively
easily to Minarca. To migrate from Rdiffweb to Minarca, you must
first uninstall Rdiffweb.

### 1. Uninstall Rdiffweb

    sudo service rdiffweb stop
    sudo pip remove rdiffweb

### 2. Migrate Rdiffweb user database

Rdiffweb saves the user database in `/etc/rdiffweb` while Minarca
saves the data to `/etc/minarca`. If you want to keep your users
preferences, you must copy the database to Minarca folder.

    cp /etc/rdiffweb/rdw.db /etc/minarca/rdw.db

### 4. Install Minarca server

Proceed with the installation of Minarca.

    wget https://www.ikus-soft.com/archive/minarca/minarca-server_latest_amd64.deb
    apt install minarca-server_latest_amd64.deb

### 5. Review Minarca configuration

When installing Minarca, a new configuration file gets created in
`/etc/minarca/minarca-server.conf`. You should review the configuration file
according to your previous Rdiffweb configuration.

Make sure to set `MinarcaRestrictedToBasedDir` to `false` if your user's home
directories are not located under a single directory.

Restart the service when you are done reviewing the configuration.

    sudo service minarca-server restart

### 6. Change permissions

Minarca web server is not running as root and required the data to be readable
and writable by minarca user. If your backups are all located under `/backups/`
as it was recommended by Rdiffweb documentation, you may run the following
command to update the permissions.

    sudo chown -R minarca:minarca /backups/
