#!/bin/bash
set -e
KEY_DIR="/etc/minarca"
export MINARCA_MINARCA_REMOTE_HOST_IDENTITY="$KEY_DIR"

# RSA key
if [ ! -f "$KEY_DIR/ssh_host_rsa_key" ]; then
    echo "Generating RSA key..."
    ssh-keygen -t rsa -b 4096 -f "$KEY_DIR/ssh_host_rsa_key" -N ""
fi

# ECDSA key
if [ ! -f "$KEY_DIR/ssh_host_ecdsa_key" ]; then
    echo "Generating ECDSA key..."
    ssh-keygen -t ecdsa -b 521 -f "$KEY_DIR/ssh_host_ecdsa_key" -N ""
fi

# ED25519 key
if [ ! -f "$KEY_DIR/ssh_host_ed25519_key" ]; then
    echo "Generating ED25519 key..."
    ssh-keygen -t ed25519 -f "$KEY_DIR/ssh_host_ed25519_key" -N ""
fi

# Start the OpenSSH server
echo "Starting OpenSSH service..."
/usr/sbin/sshd \
    -E /var/log/minarca/sshd.log \
    -o HostKey=$KEY_DIR/ssh_host_rsa_key \
    -o HostKey=$KEY_DIR/ssh_host_ecdsa_key \
    -o HostKey=$KEY_DIR/ssh_host_ed25519_key \
    -o AcceptEnv=TERM \
    -o AllowAgentForwarding=no \
    -o DebianBanner=no \
    -o LoginGraceTime=1m \
    -o MaxAuthTries=3 \
    -o PermitRootLogin=no \
    -o PasswordAuthentication=no \
    -o AllowUsers=minarca

# Start the Minarca service
echo "Starting Minarca service..."
/opt/minarca-server/bin/minarca-server &

# Get the PID of the Python service
PYTHON_PID=$!

# Function to stop both services
stop_services() {
    echo "Stopping services..."
    kill $PYTHON_PID
    pkill sshd
    exit 0
}

# Trap SIGTERM and SIGINT to gracefully stop services
trap 'stop_services' SIGTERM SIGINT

# Wait for the Python service to exit
wait $PYTHON_PID

# Stop SSHD if Python service exits
stop_services
