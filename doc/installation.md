# Server Installation Guide

## Quick Installation Steps (Debian Linux)

1. Prepare the System:

    ```sh
    apt update
    apt upgrade
    apt install ca-certificates curl lsb-release gpg
    ```

2. Add Minarca Repository Key:

    ```sh
    curl -L -o /etc/apt/keyrings/minarca-keyring.asc https://www.ikus-soft.com/archive/public.asc
    ```

3. Add Minarca Repository:

    ```sh
    cat <<EOF > /etc/apt/sources.list.d/minarca.sources
    Types: deb
    URIs: https://nexus.ikus-soft.com/repository/apt-release-$(lsb_release -sc)/
    Suites: $(lsb_release -sc)
    Components: main
    Architectures: amd64
    Signed-By: /etc/apt/keyrings/minarca-keyring.asc
    EOF
    ```

4. Install Minarca Server:

    ```sh
    apt update
    apt install minarca-server
    ```

5. Access Minarca Web Interface:

    After installation, the server should be running on `http://127.0.0.1:8080`, listening on all interfaces. For production, it is strongly recommended to configure a reverse proxy with SSL termination (e.g., Nginx or Apache).

6. Start/Stop Minarca Server (systemd):

    You may start or stop the Minarca service using:
    ```
    sudo service minarca-server start
    sudo service minarca-server stop
    ```

7. Default Login Credentials:

    After installation, you can log in to the web interface at `http://127.0.0.1:8080` using:
    - **Username:** `admin`
    - **Password:** `admin123`

Continue reading to learn how to install Minarca for production use.

## System Requirements

### Minimum Server Requirements (Evaluation)
These are for evaluation purposes only and should not be used in production:

- CPU: 64bit x86-64 or amd64, 2 cores
- Memory: 2 GiB RAM
- Storage: 8 GiB minimum

### Recommended Server Requirements
- **Operating System**:
  - Debian Bullseye, Debian Bookworm
  - Ubuntu Jammy 22.04 LTS, Ubuntu Lunar 23.04, Ubuntu Noble 24.04 LTS, Ubuntu Oracular 24.10, Ubuntu Plucky 25.04
- **CPU**: 64bit x86-64 or amd64, 4 cores
- **Memory**: Minimum 32 GiB
- **Storage**: Sufficient space based on your backup needs (typically multiple terabytes for long-term storage). For enhanced reliability, it is recommended to use hardware RAID or ZFS.
- **Temporary Storage**: Minarca requires 8 GiB or more of temporary storage, ideally configured as `tmpfs` for better performance during restoration. This should be near the web application.

## Hardware Configuration

**Note:** Configuring storage at the hardware or hypervisor level is outside the scope of this document but is essential for ensuring the system's viability.

### RAID Configuration
For production environments, ensure your storage is configured correctly at the hardware level or in your hypervisor (e.g., RAID). If using ZFS, it is essential to configure your RAID controller in JBOD (Just a Bunch of Disks) mode to maximize ZFS's performance.

- **Recommendation for physical machines**: Use ZFS for backup storage if you have direct access to the hardware.
- **Recommendation for virtual machines**: Use ext4 as the file system for backup storage.
- **Avoid installing the OS on ZFS**: For recovery ease, avoid using ZFS for your operating system. Use a traditional file system such as ext4 for the OS.

### Storage for Backups
It is highly recommended to keep backup storage separate from the system OS to prevent performance bottlenecks and to simplify recovery in case of failure.


## Install Debian

While the installation of Debian is outside the scope of this guide, we strongly recommend using Debian as the operating system for Minarca.

- For installation instructions, refer to [Debian Installation Guide](https://www.debian.org/releases/bookworm/amd64/).

## Enable "Unprivileged User Namespace" for Containers

### Why It’s Important
Minarca relies on **unprivileged user namespaces** to isolate SSH connections and backups from one another, ensuring security and system integrity.

- For dedicated machines or VMs, Minarca will usually enable this feature automatically.
- For container installations (e.g., LXC), you must enable this feature on the host system.

### Enabling on Proxmox
In **Proxmox**, configure the container with the following:
```
features: nesting=1
```

### Enabling on LXC
For **LXC** containers, enable nesting with:
```
lxc launch ubuntu nestc1 -c security.nesting=true
```

### Verifying the Feature
To verify that the unprivileged user namespaces are enabled, execute the following command:
```
unshare --user --net bash
```
If it works as root but not as a normal user, the issue is likely due to restricted unprivileged user namespaces.


## Prepare Storage

After installing Debian, configure your storage to be mounted at `/backups`, the default location for Minarca's backup data.

::::{tab-set}

:::{tab-item} EXT4

### Configure Storage for ext4

It's recommended to use ext4 only if you are using reliable hardware, such as hardware RAID, to ensure data integrity. If you don't have a reliable hardware setup, consider using ZFS for higher data protection.

1. Partition the Disk

   First, create a partition on the disk (for example, `/dev/sdb1`) using either `fdisk` or `parted`. Below is an example using `fdisk`:

    ```
    fdisk /dev/sdb
    ```

    Follow these steps within `fdisk`:
    - Type `n` to create a new partition.
    - Choose the partition type (default is primary).
    - Select the partition size.
    - Type `w` to write the changes and exit.

2. Format the Partition as ext4

   After partitioning, format the newly created partition (`/dev/sdb1`) with the `ext4` file system:

    ```
    mkfs.ext4 /dev/sdb1
    ```

3. Update `/etc/fstab` to Mount the Partition

   To ensure the partition is mounted automatically after a reboot, add an entry for it in `/etc/fstab`.

    First, get the UUID of the partition using:

    ```
    blkid /dev/sdb1
    ```

    This will output a UUID, which you'll use in the `fstab` entry. For example, if the UUID is `1234-5678`, add the following line to `/etc/fstab`:

    ```
    UUID=1234-5678  /backups  ext4  defaults,relatime  0  0
    ```

    This line will mount the partition `/dev/sdb1` at `/backups` with the `ext4` file system.

4. Mount the Partition

   To mount the partition immediately without rebooting, run:

    ```
    systemctl daemon-reload
    # OR
    mount -a
    ```
Now your ext4 partition is ready at the `/backups` location for use by Minarca.

:::

:::{tab-item} ZFS


### Configure Storage for ZFS

#### Steps to install ZFS:

1. Install ZFS utilities:
   ```
   apt update
   apt install -y zfsutils-linux
   ```
2. Load ZFS kernel module:
   ```
   modprobe zfs
   ```
3. Create a ZFS pool (example with `raidz2` for redundancy):
   ```
   zpool create tank raidz2 /dev/sda /dev/sdb /dev/sdc
   ```
4. Create and mount the backup location:
   ```
   zfs create tank/backups
   zfs set mountpoint=/backups tank/backups
   ```

#### ZFS Compression & Tuning

To optimize storage space and improve performance, customize ZFS settings:
```
zfs set compression=zstd-3 tank/backups
zfs set primarycache=all tank/backups
zfs set sync=disabled tank/backups
zfs set atime=off tank/backups
zfs set xattr=sa tank/backups
zfs set dnodesize=auto tank/backups
```

Ensure the `embedded_data` feature is active for ZFS:
```
zpool get feature@embedded_data rpool
```

:::

::::

## Install Minarca Server

### Installation Steps for Minarca Server

On a Debian Linux server:
1. Update and install necessary dependencies:

   ```sh
   apt update
   apt upgrade
   apt install ca-certificates curl lsb-release gpg
   ```

2. Add Minarca repository and key:

   ```sh
   curl -L -o /etc/apt/keyrings/minarca-keyring.asc https://www.ikus-soft.com/archive/public.asc

   cat <<EOF > /etc/apt/sources.list.d/minarca.sources
   Types: deb
   URIs: https://nexus.ikus-soft.com/repository/apt-release-$(lsb_release -sc)/
   Suites: $(lsb_release -sc)
   Components: main
   Architectures: amd64
   Signed-By: /etc/apt/keyrings/minarca-keyring.asc
   EOF
   ```

3. Install Minarca Server:

   ```sh
   apt update
   apt install minarca-server
   ```

### Start and Access Minarca Server
After installation, the Minarca server will be available at `http://127.0.0.1:8080`. For production, it's recommended to set up a reverse proxy (e.g., Nginx) with SSL.

- **Service commands**:
   ```
   sudo service minarca-server stop
   sudo service minarca-server start
   ```
- Default login credentials:
   - Username: `admin`
   - Password: `admin123`

## Deployment behind Router with Reverse Proxy (Optional)

If you server it deployed in a private network behind a router, after the installation of Minarca, you have some extra steps to complete to accomodate the networking.

```{toctree}
---
titlesonly: true
---
networking
```

## Configure Email Server (Optional)

Configure an email server if necessary for sending notifications and alerts.

[Configure Email Server](configuration.md#configure-email-notifications)

## Hardening and Security Best Practices (Optional)

```{toctree}
---
titlesonly: true
---
hardening
```

## Configure Quota (Optional)

If you want to enforce disk quotas on the backup storage, ensure the file system supports quotas (e.g., ext4 or ZFS). You can configure quotas on the `/backups` directory.

[Configure Storage Quota](configuration.md#configure-user-quota)
