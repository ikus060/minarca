# Migrating from rdiffweb to minarca-server

If you already have an installation of rdiffweb, you may migrate relatively
easily to minarca-server. To migrate from rdiffweb to minarca-server, you must
first uninstall rdiffweb.

## 1. Uninstall rdiffweb

    sudo service rdiffweb stop
    sudo pip remove rdiffweb
    
## 2. Migrate rdiffweb user database

Rdiffweb is persisting users database in `/etc/rdiffweb` while minarca-server
is persisting the data to `/etc/minarca`. If you want to keep your users
preferences, you must copy the database to minarca folder.

    cp /etc/rdiffweb/rdw.db /etc/minarca/rdw.db

## 4. Install minarca server

Proceed with the installation of minarca-server.

    wget http://www.patrikdufresne.com/archive/minarca/minarca-server_latest_all.deb
    apt install minarca-server_latest_all.deb
    
## 5. Review minarca-server configuration

When installing minarca-server, a new configuration file get created in
`/etc/minarca/minarca-server.conf`. You should review the configuration file
according to your previous rdiffweb configuration.

Make sure to set `MinarcaRestrictedToBasedDir` to `false` if your user's home
directory are not located under a single directory.

Restart the service when you are done reviewing the configuration.

    sudo service minarca-server restart

## 6. Change permissions 

Minarca web server is not running as root and required the data to be readable
and writable by minarca user. If you backups are all located under `/backups/`
as it was recommended by rdiffweb documentation. You may run the following
command to update the permissions.

    sudo chown -R minarca:minarca /backups/