# Installation

# Install Minarca-Server

On a Debian Linux server:

    wget http://www.patrikdufresne.com/archive/minarca/minarca-server_latest_amd64.deb
    sudo apt install ./minarca-server_latest_amd64.deb

This should install Minarca server and all required dependencies. The server should be running on http://127.0.0.1:8080 listening on all interfaces.

You may stop start the service using systemd:

    sudo service minarca-server stop
    sudo service minarca-server start
    
Once installed, continue reading about how to configure minarca-server.

You may access the web interface at http://localhost:8080 using:

    * username: admin
    * password: admin123 

## Setup Storage

Compared to rdiffweb, Minarca intend to take over the management of your storage and for that reason,
need to enforce some rules regarding how your storage should be layout.

You need to define a folder where all your backups will reside. Everything under this folder will then be managed by Minarca. By default, this folder is `/backups`. If you want a different folder update the parameter `MinarcaUserBaseDir` in minarca configuration.

When installing, this folder will be created with the right ownership and permissions. If you have created this folder your self, make sure the ownership is set to `minarca:minarca` and permissions to `-rwxr-x---`.

    chown minarca:minarca /backups/
    chmod 0750 /backups/
    
## Setup SSH

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


# Install Minarca-Client

On a Windows or Debian workstation, download the appropriate installer.

<a href="http://www.patrikdufresne.com/archive/minarca/minarca-client_latest_all.deb"><img alt="Minarca Client for Linux/Debian" src="https://img.shields.io/badge/download-Minaca--client--for--Debian-green?&logo=debian&style=for-the-badge"></a>
<a href="http://www.patrikdufresne.com/archive/minarca/minarca-latest-install.exe"><img alt="Minarca Client for Windows" src="https://img.shields.io/badge/download-Minaca--client--for--Windows-green?&logo=windows&style=for-the-badge"></a>

Then launch the execution of the installer and follow the instructions. On Debian workstation, it's preferable to install the packages using Gdebi.

Once installed, a shortcut to Minarca should be available on your desktop or start menu. Use it to start Minarca.
