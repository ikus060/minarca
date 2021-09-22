# Minarca-Client (Desktop Agent)

## Installation

## Minarca-Client installation

On a Windows or Debian workstation, download the appropriate installer.

<a href="https://www.ikus-soft.com/archive/minarca/minarca-client_latest_all.deb"><img alt="Minarca Client for Linux/Debian" src="https://img.shields.io/badge/download-Minaca--client--for--Debian-green?&logo=debian&style=for-the-badge"></a>
<a href="https://www.ikus-soft.com/archive/minarca/minarca-client_latest.exe"><img alt="Minarca Client for Windows" src="https://img.shields.io/badge/download-Minaca--client--for--Windows-green?&logo=windows&style=for-the-badge"></a>

Then launch the execution of the installer and follow the instructions. On Debian workstation, it's preferable to install the packages using Gdebi.

Once installed, a shortcut to Minarca should be available on your desktop or start menu. Use it to start Minarca.

### On Linux

**With Command Line:**

    wget https://www.ikus-soft.com/archive/minarca/minarca-client_latest_all.deb
    apt install ./minarca-client_latest_all.deb

**With a User interface:**

 1. Download the latest Debian package from [here](https://www.ikus-soft.com/archive/minarca/minarca-client_latest_all.deb).
 2. Double click on the package to install it using your favourite tool.

*Notice: To improve the user experience we are working to make a PPA available.*

### On Windows

 1. Download the latest Windows installer from [here](https://www.ikus-soft.com/archive/minarca/minarca-client_latest.exe).
 2. Double click on the package to install it.

### Link your client with Minarca Server

Pre-requisite: You need to have a functional Mianrca Server deployed. You may use https://test.minarca.net which is made available for testing purpose.

**From Command line:**

    minarca link --force --remoteurl {{minarca_client_remote_url}} --username {{minarca_client_user}} --password {{minarca_client_pass}} --name {{ansible_hostname}}

**From User Interface:**

1. Simply open `minarcaui`. If you have installed Minarca client you should be able to launch the client from your start menu.
2. If Minarca is not yet linked to a server, a Setup dialog will be shown to allow you to configure Minarca with you server.
3. You must provide the URL to you Minarca server, a username and password.
4. You must also provide a repository name.

## Troubleshooting

### Logs locations

The user interface and the command line interface are generating logs in the same log files. 

*On Windows*

    %TEMP%\minarca.log
    or
    C:\Users\vmtest\AppData\Local\Temp\minarca.log

*On Linux*

    ~/.local/share/minarca/
