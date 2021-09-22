# Support backupninja with Minarca-server

When installing minarca server in your environment, you may already have an
existing system to automate the backup of your computers. A common tool used
to backup Linux server is [backupninja](https://github.com/lelutin/backupninja).
If you already have backupninja in your enviroment, or if you want to use
backupninja instead of minarca client, you may configure minarca-server to
support it.

## Update minarca-shell configuration

To accept incomming connection from backupninja, you must enable rdiff-backup
compability layer.

Edit the configuration file `/etc/minarca/minarca-shell.conf`, change the
value of `RDIFFBACKUP_COMPATIBILITY` to `1` and uncomment the line.

    RDIFFBACKUP_COMPATIBILITY=1

## Add you ssh public key to minarca server

Using the web interface, you need to add all your public keys to a specific user.

If you are using the "admin" user, browse to
https://www.minarca.net/prefs/sshkeys/ and add your SSH Key.

By adding them to the user "admin", all your backups repositories are
located under `/backups/admin` folder, unless you have changed the
value of `MinarcaUserBaseDir`.

## Configure backupninja

Finnaly, you must update the the backupninja configuration file under
`/etc/backup.d/`. Verify the values under `[dest]` section:

    [dest]

	# remote or local? If local, you dont need to specify a host below
	type = remote
	
	# the machine which will receive the backups
	host = minarca.example.com
	
	# put the backups under this directory
	directory = .
	
	# make the files owned by this user
	# note: you must be able to ssh backupuser@backhost
	# without specifying a password 
	user = minarca
