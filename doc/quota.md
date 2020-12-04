# Minarca Quota Management

Minarca provide user base quota management. This allow you to define fixed
amount of disk space for each user. If a user backup reach the quota, the
backup will fail.

This feature might be used by service provider to define the maximum disk space
allocated to a user based on the price of the service.

Default implementation of users quota support only ZFS storage. But you may
customize this to fit your file system and deployment by configure the command
line to be executed.

First, install `minarca-quota-api` on the storage server. This might be the
same server as Minarca Web Server or a different one depending on your setup.

In Minarca web server configuration file `/etc/minarca/minarca-server.conf`,
you must define the location of the quota API service to be used to set and
fetch the disk usage.

    MinarcaQuotaApiUrl=http://minarca:secret@localhost:8081/ 


You may also change Minarca's configuration in :

## Troubleshooting

**List project id**

    #     lsattr -p /backups
    1 -----------------P- /backups/admin
    2 -----------------P- /backups/john
