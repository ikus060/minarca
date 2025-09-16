# Server Hardening

Server hardening involves implementing various security measures to protect your server from unauthorized access, attacks, and vulnerabilities. By following these steps, you can enhance the security posture of your Minarca server.

## Configure a Reverse Proxy with Encrypt Network Traffic (SSL)

Setting up a reverse proxy can provide an additional layer of security and improve the performance and scalability of your web applications.

[Deploy Minarca Behind a Router with a Reverse Proxy](networking.md)

## Configure Firewall

1. Set up a firewall to control incoming and outgoing network traffic. Only allow necessary ports and protocols.
2. You should consider exposing only ports 80 (http), 433 (https) and 22 (ssh). It's also recommended, as explain in next section, to expose an alternate SSH port like 6022.
3. Make sure you are not exposing default port 8080 used by default by Minarca Server for unsecure communication.
4. Close all unused ports and services to minimize potential attack vectors.
5. Implement a default deny policy, only permitting essential services.

## Secure remote SSH access

The SSH (Secure Shell) server is a critical component of remote server access. Implementing proper security measures for SSH helps protect against unauthorized access and potential attacks.
Minarca Server has already taken some of the best practice regarding the configuration of the SSH server by disabling TCP tunnel, creating a Chroot Jail and using password-less authentication.

Here are additional element an administrator could configure to make the SSH server more secure.

1. Disable SSH protocol versions 1 and use only SSH protocol version 2, which offers stronger security.
2. Disable password authentication:  
  `PasswordAuthentication no`
3. Disable root login:  
  `PermitRootLogin no`
4. Change the default SSH port (typically 22) to a non-standard port to reduce visibility to potential attackers. Choose a port outside the well-known port range.
    * If your server is deployed in a private network behind a proxy, you may create a port forward rule from port 6022 to port 22 pointing to your server.
    * If your server is deployed in a public network on Internet, update your `/etc/ssh/sshd_config`:
    `Port 6022`
    * In both case, don't forget to update Minarca configuration to let the clients know how to connect to your SSH server by updating `/etc/minarca/minarca-server.conf`:  
      `minarca-remote-host=backups.example.com:6022`
    * Reload the SSH service:  
      `service sshd reload`
3. Configure SSH to only allow specific users or groups to connect, limiting access to authorized individuals.
4. Implement SSH brute-force attack protection mechanisms, such as [fail2ban](http://www.fail2ban.org), to automatically block IP addresses that exhibit suspicious behavior.

### Change Default Admin Password
It is strongly recommended to change the default admin password or create an alternate admin user and delete the default **admin** user.

1. Update the configuration `/etc/minarca/minarca-server.conf`  
   ```
   admin-user=youradmin
   ```
2. Login to the web interface with username **youradmin** and default password **admin123**.
3. Using the Admin area, change the password of user **youradmin**.
4. Finally, delete the default **admin** user.

## Update and Patch Management

Regularly update and patch your server's operating system, software, and applications to ensure you have the latest security fixes and bug patches.

```
sudo apt update
sudo apt upgrade
```

Enable automatic updates or establish a systematic update process.

Minarca is continuously updated with secutiry enhancements.

