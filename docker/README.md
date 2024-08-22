# Minarca Server - Docker Image

## Introduction

Minarca is an open-source, easy-to-use backup solution designed to provide secure, reliable, and efficient data protection. Built with simplicity and flexibility in mind, Minarca allows you to set up and manage backups for your data with ease. Whether you're an individual, a small business, or an enterprise, Minarca ensures that your critical data is safe and recoverable.

Minarca Server acts as the central hub for managing your backups. It supports various configurations, including local and remote backups, making it a versatile solution for diverse backup needs.

For more information and resources on Minarca, check out the following links:
- [Minarca Website](https://minarca.org/)
- [Minarca Documentation](https://www.ikus-soft.com/archive/minarca/doc/)
- [Minarca Gitlab Repository](https://gitlab.com/ikus-soft/minarca)

## Using the Docker Image
### Running Minarca Server with Docker Command Line

To start the Minarca Server using Docker, use the following command:

```bash
docker run -d \
  -p 8080:8080 \
  -p 22:22 \
  -v /path/to/backups:/backups \
  -v /path/to/conf:/etc/minarca \
  -v /path/to/logs:/var/log/minarca \
  --restart always \
  --name minarca-server \
  ikus060/minarca-server
```

### Docker Command Breakdown:
- `-p 8080:8080`: Exposes port 8080 on your host machine for the Minarca web interface.
- `-p 22:22`: Exposes port 22 on your host machine for SSH access by Minarca Agents.
- `-v /path/to/backups:/backups`: Maps the backup directory inside the container to a directory on your host machine.
- `-v /path/to/conf:/etc/minarca`: Maps the configuration directory inside the container to a directory on your host machine.
- `-v /path/to/logs:/var/log/minarca`: Maps the log directory inside the container to a directory on your host machine.
- `--restart always`: Ensures the container restarts automatically if it stops.

### Running Minarca Server with Docker Compose

If you prefer using Docker Compose, here's a sample `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  minarca-server:
    image: ikus060/minarca-server
    ports:
      - "8080:8080"
      - "2222:22"
    volumes:
      # Location of the backups
      - ./backups:/backups
      # Configuration file and local database
      - ./conf:/etc/minarca
      # Application logs
      - ./logs:/var/log/minarca
    restart: always
    environment:
      # Define the URL to be used by users to connect to this container port 8080 running the webserver.
      # This is optional and only required if a reverse proxy is used.
      MINARCA_EXTERNAL_URL: https://minarca.mycompany.com
      # Define the hostname and IP address to be used by Minarca Agent to connect to this container on port 2222 running SSH Server.
      # This is optional and only required if the port used for SSH is not 22.
      MINARCA_MINARCA_REMOTE_HOST: minarca.mycompany.com:2222
```

### Notes:

- **MINARCA_EXTERNAL_URL**: This environment variable is optional. It should be set if you are using a reverse proxy to handle connections to the Minarca Server on port 8080.
- **MINARCA_MINARCA_REMOTE_HOST**: This environment variable is also optional. Set it only if the SSH port is not the default port 22, which is commonly used by the host system.

By following these instructions, you can have Minarca Server up and running with minimal configuration, ready to manage your backup needs effectively.

## Accessing the Minarca Server

Once the container is running, you can access the Minarca web interface by navigating to the external URL you defined in the MINARCA_EXTERNAL_URL environment variable (e.g., https://minarca.mycompany.com). From there, you can monitor backups and more.
