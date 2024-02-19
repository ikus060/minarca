# -*- coding: utf-8 -*-
#
# Minarca
#
# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Jan 30, 2024

Reusable module to generate and validate minarcaid

@author: Patrik Dufresne <patrik@ikus-soft.com>
"""

import base64
import hashlib
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def _fingerprint(public_key):
    """
    Generate a fingerprint from ssh key.
    """
    # Format public key into ssh-rsa, etc.
    ssh_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH, format=serialization.PublicFormat.OpenSSH
    )
    # Pick the key part after ssh-rsa
    key = ssh_public_key.split(b' ', 1)[1]
    # Define the data from base64
    key_bytes = base64.b64decode(key)
    # Create a hash of the bytes
    fp_plain = hashlib.md5(key_bytes).hexdigest()
    # Reformat the hash.
    return ':'.join(a + b for a, b in zip(fp_plain[::2], fp_plain[1::2]))


def _read_private_key(value):
    """
    Try to read the private key.
    """
    assert isinstance(value, bytes)
    #
    # Try custom OPEN SSH Format
    #
    try:
        return serialization.load_ssh_private_key(value, password=None)
    except Exception:
        # Silently ignore error
        pass
    #
    # Try defaul PEM format
    #
    return serialization.load_pem_private_key(value, password=None)


def gen_minarcaid_v1(private_key_data, epoch=None):
    """
    Generate minarcaid for authentication with RESTful API.
    v=1$fingerprint$timestamp$signature
    """
    #
    # Read the private key.
    #
    private_key = _read_private_key(private_key_data)

    #
    # Generate finger print of ssh key identical to rdiffweb.
    #
    fingerprint = _fingerprint(private_key.public_key())
    #
    # Get epoch time
    #
    epoch = epoch or int(time.time())
    epoch_bytes = epoch.to_bytes(4, 'big')
    #
    # Sign the epoch using private key.
    #
    signature_bytes = private_key.sign(epoch_bytes, padding.PKCS1v15(), hashes.SHA256())
    signature_base64 = base64.b64encode(signature_bytes).decode('ascii')
    return f'v=1${fingerprint}${epoch}${signature_base64}'


def _verify_minarcaid_v1(value, public_key_callback):
    assert value.startswith('v=1$')
    parts = value.split('$', 4)
    if len(parts) != 4:
        raise ValueError('wrong number of fields for minarcaid version 1')
    fingerprint, epoch, signature_base64 = parts[1:]
    signature_bytes = base64.b64decode(signature_base64)
    #
    # Validate epoch
    #
    if not epoch.isdigit():
        raise ValueError('invalid epoch value for minarcaid version 1')
    if abs(int(epoch) - int(time.time())) > 10:
        raise ValueError('expired minarcaid')
    epoch_bytes = int(epoch).to_bytes(4, 'big')
    #
    # Lockup public key
    #
    return_value = public_key_callback(fingerprint)
    if return_value is None:
        raise ValueError('no key matching fingerprint')
    if isinstance(return_value, (tuple, list)):
        data = return_value[0]
    public_key = serialization.load_ssh_public_key(data.encode('ascii'), backend=default_backend())
    #
    # Verify epoch signature
    #
    try:
        public_key.verify(signature_bytes, epoch_bytes, padding.PKCS1v15(), hashes.SHA256())
        return return_value
    except InvalidSignature:
        raise ValueError('invalid signature')


def verify_minarcaid(value, public_key_callback):
    if value.startswith('v=1$'):
        return _verify_minarcaid_v1(value, public_key_callback)
    raise ValueError('unsuported version of minarcaid')
