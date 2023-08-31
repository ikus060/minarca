# Client Installation

## System requirements

Minarca client could be installed on almost any hardware without
restriction. You are limited to the following operating system.

* Supported Operating System:
  * Windows 7 (64bits) - best effort support
  * Windows 10 (64bit)
  * Windows 11 (64 bits)
  * MacOS Catalina (Intel)
  * MacOS BigSur (Intel)
  * Debian Buster (64bit)
  * Debian Bullseye (64bit)
  * Debian Bookworm (64bit)
  * Ubuntu Jammy (64bit)
  * Ubuntu Kinetic (64bit)
  * Ubuntu Lunar (64bit)
  * Ubuntu Mantic (64bit)
  * Linux (64bit)

## Installation Steps

Installation steps mostly depends on your operating system. Follow the step appropriate for your system.

## Installation on Windows

On a Windows workstation, download the appropriate installer.

<a href="https://www.ikus-soft.com/archive/minarca/minarca-client-latest.exe"><img alt="Minarca Client for Windows" src="https://img.shields.io/badge/download-Minarca-blue?&logo=windows&style=for-the-badge"></a>

Then launch the execution of the installer and follow the instructions.

**Windows7**: Your installation must be up-to-date or manually install [VC 2015 Redistributable](https://www.microsoft.com/en-US/download/details.aspx?id=48145).

## Installation on MacOS

On a Windows workstation, download the appropriate installer.

<a href="https://www.ikus-soft.com/archive/minarca/minarca-client-latest.dmg"><img alt="Minarca Client for Windows" src="https://img.shields.io/badge/download-Minarca-blue?&logo=apple&style=for-the-badge"></a>

Open the disk image and drag-n-drop Minarca to your Applications folder.

![Open Minarca Disk image with Finder](minarca-macos-disk-image.png)

Then open Minarca Application !

If you get the following, you might need to right click on Minarca Application and
click "Open" to skip the certificate validation.

![Minarca can't be open because Apple cannot check it for malicious software.](macos-installation-issue.png)

## Installation on Ubuntu or Debian

On a Ubuntu or Debian workstation, download the appropriate installer.

*Ubuntu*

<a href="https://www.ikus-soft.com/archive/minarca/minarca-client-jammy-latest.deb"><img alt="Minarca Client for Ubuntu Jammy" src="https://img.shields.io/badge/Ubuntu-Jammy-blue?&logo=ubuntu&style=for-the-badge"></a>

<a href="https://www.ikus-soft.com/archive/minarca/minarca-client-kinetic-latest.deb"><img alt="Minarca Client for Ubuntu Kinetic" src="https://img.shields.io/badge/Ubuntu-Kinetic-blue?&logo=ubuntu&style=for-the-badge"></a>

<a href="https://www.ikus-soft.com/archive/minarca/minarca-client-lunar-latest.deb"><img alt="Minarca Client for Ubuntu Lunar" src="https://img.shields.io/badge/Ubuntu-Lunar-blue?&logo=ubuntu&style=for-the-badge"></a>

<a href="https://www.ikus-soft.com/archive/minarca/minarca-client-mantic-latest.deb"><img alt="Minarca Client for Ubuntu Mantic" src="https://img.shields.io/badge/Ubuntu-Mantic-blue?&logo=ubuntu&style=for-the-badge"></a>

*Debian*

<a href="https://www.ikus-soft.com/archive/minarca/minarca-client-buster-latest.deb"><img alt="Minarca Client for Debian Buster" src="https://img.shields.io/badge/Debian-Buster-blue?&logo=debian&style=for-the-badge"></a>

<a href="https://www.ikus-soft.com/archive/minarca/minarca-client-bullseye-latest.deb"><img alt="Minarca Client for Debian Bullseye" src="https://img.shields.io/badge/Debian-Bullseye-blue?&logo=debian&style=for-the-badge"></a>

<a href="https://www.ikus-soft.com/archive/minarca/minarca-client-bookworm-latest.deb"><img alt="Minarca Client for Debian Bookworm" src="https://img.shields.io/badge/Debian-Bookworm-blue?&logo=debian&style=for-the-badge"></a>

On Debian workstation, it's preferable to install the packages using Gdebi.

Once installed, a shortcut to Minarca should be available on your desktop or start menu. Use it to start and configure Minarca.

## Installation on Linux

For other Linux distribution, you may download a portable package.

<a href="https://www.ikus-soft.com/archive/minarca/minarca-client-latest.tar.gz"><img alt="Minarca Client for Linux" src="https://img.shields.io/badge/download-Minarca-blue?&logo=linux&style=for-the-badge"></a>

Extract it's content to a folder and launch `minarcaw` executable or `minarca` from command line.

## Link your client with Minarca Server

Pre-requisite: You need to have a functional Mianrca Server deployed. You may use <https://test.minarca.net> which is made available for testing purpose.

**From User Interface:**

1. Simply open `minarcaw`. If you have installed Minarca client you should be able to launch the client from your start menu.
2. If Minarca is not yet linked to a server, a Setup dialog will be shown to allow you to configure Minarca with you server.
3. You must provide the URL to you Minarca server, a username and password.
4. You must also provide a repository name.

**From Command line:**

    minarca link -r REMOTEURL -u USERNAME [-p PASSWORD] -n NAME

## Troubleshooting

### Logs locations

The user interface and the command line interface are generating logs in the same log files. 

*On Windows*

    %LOCALAPPDATA%\minarca\

*On Linux*

    ~/.local/share/minarca/

*On MacOs*

    ~/Library/Logs/Minarca/
