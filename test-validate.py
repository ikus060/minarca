from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
#from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_ssh_private_key, load_ssh_public_key, serialize_ssh_public_key, _serialize_ssh_private_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64

# $minarcaid$v=1$fingerprint$signature

def _validate_minarcaid(value):
    parts = value.split('$', 4)



def generate_ssh_key_pair():
    # Generate an RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Get the public key in OpenSSH format
    public_key = private_key.public_key()
    ssh_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )

    # Get the private key in PEM format (you can use other formats like PKCS8 as well)
    ssh_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    return ssh_public_key, ssh_private_key

private_key_file = 'id_rsa'
public_key_file = 'id_rsa.pub'

#
# Generate the key pair & Save them.
#
public_key, private_key = generate_ssh_key_pair()
with open(public_key_file, "wb") as file:
    file.write(public_key)

# Load the private key from file
with open(private_key_file, "wb") as file:
    file.write(private_key)

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


#
# Sign public key with our private key - will be used as authentication value for Minarca
#
def sign_data(data, private_key):
    # Sign the data using the private key
    signature = private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    return signature

signature = sign_data(b'123456', ssh_private_key)
base64.b64encode(signature).decode('ascii')

def verify_signature(data, signature, public_key):
    try:
        # Verify the signature using the public key
        public_key.verify(
            signature,
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print(f"Verification failed: {e}")
        return False

verify_signature(b'123456', signature, ssh_public_key)




