from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
#from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_ssh_private_key, load_ssh_public_key, serialize_ssh_public_key, _serialize_ssh_private_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64
import hashlib
import time 

private_key_file = 'id_rsa'
public_key_file = 'id_rsa.pub'

#
# Read keypair from file.
#
with open(public_key_file, "rb") as file:
    ssh_public_key = serialization.load_ssh_public_key(
        file.read(),
        backend=default_backend()
    )

# Load the private key from file
with open(private_key_file, "rb") as file:
    ssh_private_key = serialization.load_pem_private_key(
        file.read(),
        password=None,  # Provide a password if the private key is encrypted
        backend=default_backend()
    )

def _fingerprint(public_key):
    """
    Keep same implementation as Rdiffweb.
    """
    public_key_base64 = public_key.public_bytes(encoding=serialization.Encoding.OpenSSH,format=serialization.PublicFormat.OpenSSH).split(b' ', 2)[1]
    public_key_bytes = base64.b64decode(public_key_base64)
    fp_plain = hashlib.md5(public_key_bytes).hexdigest()
    return ':'.join(a + b for a, b in zip(fp_plain[::2], fp_plain[1::2]))

def _minarcaid_v1(private_key):
    """
    Generate minarcaid for authentication with RESTful API.
    $minarcaid$v=1$fingerprint$timestamp$signature
    """
    public_key = private_key.public_key()
    # Generate Fingerprint of public key
    fingerprint = _fingerprint(public_key)
    # Get epoch time
    epoch = int(time.time())
    epoch_bytes = epoch.to_bytes(4, 'big')
    # Sign the epoch using private key.
    signature_bytes = private_key.sign(epoch_bytes, padding.PKCS1v15(), hashes.SHA256())
    signature_base64 = base64.b64encode(signature_bytes).decode('ascii')
    return f'$minarcaid$v=1${fingerprint}${epoch}${signature_base64}'

def _verify_minarcaid_v1(value, public_key):
    assert value.startswith('$minarcaid$v=1$')
    parts = value.split('$', 5)
    if len(parts) != 6:
        raise ValueError('wrong number of fields for minarcaid version 1')
    _empty, _id, _version, fingerprint, epoch, signature_base64 = parts
    # FIXME Lookup fingerprint in database
    signature_bytes = base64.b64decode(signature_base64) 
    if not epoch.isdigit():
        raise ValueError('invalid epoch value for minarcaid version 1')
    if abs(epoch - int(time.time())) > 10:
        raise ValueError('expired minarcaid')
    epoch_bytes = int(epoch).to_bytes(4, 'big')
    # Verify signature
    public_key.verify(signature_bytes,
        epoch_bytes,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

def _verify_minarcaid(value, public_key):
    if not value.startswith('$minarcaid$'):
        raise ValueError('expecting minarcaid')
    if value.startswith('$minarcaid$v=1$'):
        return _verify_minarcaid_v1(value, public_key)
    raise ValueError('unsuported version of minarcaid')

minarcaid = _minarcaid_v1(ssh_private_key)


_verify_minarcaid(minarcaid, ssh_public_key)