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
  * Debian Bullseye
  * Debian Bookworm
  * Ubuntu Jammy 22.04 LTS
  * Ubuntu Lunar 23.04
  * Ubuntu Noble 24.04 LTS
  * Ubuntu Oracular 24.10
* Cpu: 64bit x86-64 or amd64, 4 core
* Memory: minimum 4 GiB
* Storage: consider the storage according to your backup needs. A couple of terabytes should be considered for the long term. Ideally, you should consider hardware or ZFS raid for your storage. If you plan to support user quota, make sure that your file system supports it. E.g. ext4 and ZFS. Other file systems might not be well supported.
* Temporary storage: Minarca requires a temporary storage location that is used during the restoration process. This location should be greater than 8gb. This temporary storage will be closer to the web application. Ideally, it should be in ram using tmpfs.

### Compatibility Matrix

Here's a compatibility matrix for Minarca Server and Minarca Agent:

| Agent                      | v6.x | v5.x | v4.5 - v4.3 | v4.2 - v4.0 | v3.x |
| -------------------------- | ---- | ---- | ----------- | ----------- | ---- |
| Minarca Server v6.x        | ✓    | ✓    | ✓           | ✓ *1        | ✓ *1 |
| Minarca Server v5.x        | ✓ *2 | ✓    | ✓           | ✓ *1        | ✓ *1 |
| Minarca Server v4.5 - v4.3 |      |      | ✓           | ✓ *1        | ✓ *1 |
| Minarca Server v4.2 - v4.0 |      |      | ✓ *1        | ✓ *1        | ✓ *1 |
| Minarca Server v3.x        |      |      |             |             | ✓    |

1. Supported only if the agent is already configured because the initialisation
   process was using the web form which is no longer supported for security reason.
2. Some features are not available: updating the backup settings from Minarca Agents,
    retrieving the Disk usage from server.

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

### Configure Storage

As an additional steps to the installation, you may want to change the location used to store the backups. By default, this location is `/backups/` and may be changed to an alternate location.

[Read how to configure Minarca storage](configuration-storage)

### Setup SSH Server

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

### Minarca with LXC

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

#### For LXC

The container need to be started with `security.nesting`:

    lxc launch ubuntu nestc1 -c security.nesting=true

#### For Proxmox VE (lxc)

The container must be configured with feature `nesting=1`.

Edit `/etc/pve/lxc/100.conf` by adding:

    features: nesting=1
