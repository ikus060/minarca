# FAQ

## Is Minarca compatible with…?

The Minarca client application works with Windows and Linux
operating systems. We recommend the following configuration:

* Windows 10 and 11
* Debian Linux (recommended)
* Ubuntu Linux
* Other Linux

To access your data on the Minarca Web interface, we recommend the following browsers:

* Google Chrome  (recommended)
* Internet Explorer 9+
* Safari 8+
* Firefox 3+
* Android devices

## What is Minarca.net SaaS ?

[Minarca.net SaaS](https://www.minarca.net) (Software as a service) allows you to backup your data using Minarca without the trouble of installing Minarca Server. This solution is perfect to Small Business or non-technical customer. You will benefits from Minarca without the burden of maintaining the hardware architecture.

## How do I sign up for Minarca.net SaaS ?

You may subscribe to our [Minarca.net SaaS](https://www.minarca.net) (Software as a service) which allow you to benefit from Minarca without installing a server. To subscribe, you may fill the [subscription form](https://minarca.org/en_CA/contactus) or send an email to [support@ikus-soft.com](mailto:support@ikus-soft.com). We will contact you to finalize your subscription, either by email or phone, depending on your preference.

## How do I install Minarca Client?

### 1. Download

You can download the Minarca application and follow the [**installation procedures**](https://ikus-soft.com/en/minarca/download/).

![Minarca installation - Accept license agreement.](4terms.png)

![Minarca installation - Select installation directory.](fenetre-installation.png)

### 2. Subscribe

Enter the username and temporary password assigned to you, and then create a name to link your computer to Minarca.

![Minarca Setup - Sign in with your username and password.](5connect.png)

### 3. Enjoy Minarca

 Once the application is installed, you can access the Minarca web interface by clicking on the **View my account online** in the application itself. You will have to sign in again.

## How do I change the automatic backup frequency?

To change the automatic backup frequency in Minarca Data Backup software, you can follow these steps:

1. Open the Minarca application on your computer.
2. Look for the "Schedule backup" option within the application's interface and click on it. It is located in the top menu or toolbar.
3. Click on the backup frequency option to modify it. You may have the choice to select from predefined options such as hourly, daily or bi-daily backups.

Your data will be backed up accordingly at the specified intervals.

## How do I perform a manual backup?

Minarca automatically backs up data according to frequency settings. However, it is possible to manually backup data. To do this, open your Minarca application, and click **Start backup**.

## How do I access my data backups?

To access your data backups, you can open your Minarca application and click the icon in the **View my account online** section.

## How do I select the folders I would like to back up?

The Minarca application lets you select which folders or files you do or do not want to back up. Open your Minarca application and, in the **Select files** section. You can then choose the folders or files you want to back up.

## There is a folder I would like to back up, but it is not on the list

When you access **Select files**, there is a predefined list of files. However, it is possible to customize your choice by adding folders. Click **Add Folder**, and select one of your existing folders. Follow the same steps to add only one file by clicking **Add File**.

## How do I restore one or more file(s)?

You can restore a complete backup or specific files only by accessing your data using the web interface. In the **Repository** section, choose the device you would like to back up.

![Minarca Web Interface - Repository list.](10acceuil.png)

**For a complete backup:** select the **Restore Directory** tab, and download the desired version of the backup.

**To restore a directory:** stay in the **Browse Directory** tab, and select the file you want to restore. Once the file has been selected, go to the **Restore Directory** tab, and download. Only the selected file will be downloaded.

![Minarca Web Interface - Restore a folder.](12repositories.png)

## How do I link a second device to my account?

With Minarca, you can link several devices to the same account. Simply install the application on your selected devices, and give each device its own name. When you connect to the web interface, you will have access to all your devices in the **Repository** section.

## How do I delete a backup from one of my devices?

It is possible to completely delete one of your device backups. In the **Repository** section, select the desired device, and then click the **Settings** tab.

**Warning! The deletion of a device backup is permanent!**

## There is a new version of the Minarca application online. How do I get the update?

Simply reinstall the application to get the new version online.

## How do I change my password?

Change your password in the *User Profile* Top-Right corner in the web application. For security reasons, we recommend that you choose a secure password. You may also enabled multi-factor authentication for better security.

![Minarca Web Interfaces - User profile to change your password.](15usersettings.png)

## I forgot my password. What should I do?

It's not possible for you to recover you password. You must contact your system administrator to recover the password.

## How do I change my email address?

You can change your email address in the *User Profile* Top-Right corner in web application.

## Can I change my username?

Your username cannot be changed.

## Can I change the names of my repository?

The names of your repository cannot be changed by the user. You must ask a system administrator to rename a repository. To do so, the system administrator could manually rename the folder directly on the server. Any configuration settings such as notification preference defined on the repository will be lost.

## How much space do my backups use?

As soon as you connect to the Minarca web interface, you can see the space used and the space available in the **Repository** section.

## Why are rdiff-backup packages downloaded from custom repository when rdiff-backup is in Debian?

The reason why the rdiff-backup packages are downloaded from our repository instead of using the ones provided by Debian is due to several factors. Firstly, Minarca server is designed to support multiple versions of rdiff-backup for backward compatibility. These versions include 1.2.8, 2.0.x, and soon 2.2.x. However, the packages distributed by Debian cannot be installed side-by-side, which is a requirement for Minarca's functionality.

Moreover, the packages distributed within Minarca are pre-compiled with a specific version of Python that is guaranteed to work in any Debian or Ubuntu distribution, regardless of the Python version provided by the operating system. This ensures compatibility across different environments.

Additionally, there are occasions when we need to apply additional patches to the original source code for compatibility reasons. While most of these patches are eventually merged upstream within a few months, we apply them directly to the packages distributed by Minarca to avoid any disruption for our end-users.

In summary, the rdiff-backup packages distributed by Minarca are specifically tailored and known to work seamlessly with Minarca, whereas the packages provided by Debian may not fulfill these requirements.
