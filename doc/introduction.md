# Introduction

## What is Minarca ?

Minarca est une solution de sauvegarde de données permettant de centraliser la gestion de vos sauvegardes. Cette solution a pour avantage d'être facile à installer sur un serveur dédié et permet aussi d'installer facilement un agent appeler minarca-client sur les ordinateurs a sauvegarder. 

Minarca ce veux une solution de sauvegarde sans tracas, incluant toutes les fonctionnalités dont vous avez besoin afin de mieux servir vos usagers. L'agent minarca est disponible pour les plateformes majeurs tel Windows Mac OS et Linux. Vous permettant ainsi d'utiliser une seule solution afin de sauvegarder l'ensemble de votre parc informatique.

## Architecture

La solution de sauvegarde Minarca se décompose en plusieurs composants.

D'abord du côté serveur, une application web vous permet de gérer les sauvegardes de vos usages et et dans configurer l'accès. Cette interface web permet aussi de parcourir la sauvegarde et de restaurer des données à partir de votre navigateur Web. Ce composant est une version modifiée de Riffweb.

En plus de cette application web, on installe aussi un autre composant appeler Minarca-shell qui s'occupe de recevoir les connexions entrantes via le protocole SSH, de valider l'authentification et l'autorisation de l'usager pour faire une sauvegarde et aussi isolé chaque usager et leur dépôt.

 le dernier composant,nommer Minarca client, doit être installé sur les ordinateurs devant être sauvegardées. Ce composant agit comme un agent sur l'ordinateur et s'occupe de coordonner la sauvegarde de données vers le serveur Minarca. En utilisant cet argent il est possible de sélectionner les fichiers et répertoires de vente être sauvegardé et la fréquence de la sauvegarde. 'l'agent Minarca peut être utiliser via une interface utilisateur ou en ligne de commande.

![Minarca Architecture overview](architecture-overview.png)

## Main features

* Web interface: browse and restore backup without command lines.
* User management: provides user access control list for repositories.
* User authentication: username and password validation are done using a database or your LDAP server.
* User permission: allows you to control which users can run deletion operations.
* Email notification: emails can be sent to keep you informed when backup fails
* Statistics visualization: web interface to view backup statistics provided by Rdiff-backup.
* Disk Quota: manage disk space allocated to each user.
* Integrated Agent: maybe used to quickly backup your data without ny technical knowledge
* Compatibility support: allow usability with legacy rdiff-backup v1.2.8 and v2.0.5 agent
* User repository isolation: incomming request are completly isolated from each other
* Automated SSH management: no requirement to manually generate SSH identity, SSH authentication is completly automated and doesn't required intervention
* Open source: no secrets. Rdiffweb is a free open-source software. The source code is licensed under GPL v3.
* Support: business support will be available through [Ikus Software](https://ikus-soft.com).
* Rdiff-backup: used as the main backup software you benefit from its stability, cross-platform. And you can still use it the way you are used to with the command line.

## Software stack

Minarca software consists of a 3 components: minarca-server, minarca-shell, minarca-client.

Aside from the web interface, which uses HTML and JavaScript everything else is written in Python programming language.

## Getting help

### Mailing list

Minarca is open-source, and contributions are welcome. Here is the main communication channel to get help from other users.

[Rdiffweb Google Group](https://groups.google.com/forum/#!forum/rdiffweb)

### Bug tracker

If you encounter a problem, you should start by asking to be added to the mailing list. Next, you may open a ticket in our issue tracking system.

[Gitlab Issues](https://gitlab.com/ikus-soft/minarca/-/issues)

### Professional support

If you need professional support or custom development, you should contact Ikus Software directly.

[IKUS Soft Support Form](https://www.ikus-soft.com/en/support/#form)
