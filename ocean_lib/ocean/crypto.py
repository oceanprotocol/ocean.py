#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from base64 import b64encode
from hashlib import sha256

from cryptography.fernet import Fernet
from ecies import decrypt as asymmetric_decrypt
from ecies import encrypt as asymmetric_encrypt
from enforce_typing import enforce_types
from eth_keys import keys
from eth_utils import decode_hex


@enforce_types
def calc_symkey(base_str: str) -> str:
    """Compute a symmetric private key that's a function of the base_str"""
    base_b = base_str.encode("utf-8")  # bytes
    hash_b = sha256(base_b)
    symkey_b = b64encode(str(hash_b).encode("ascii"))[:43] + b"="  # bytes
    symkey = symkey_b.decode("ascii")
    return symkey


@enforce_types
def sym_encrypt(value: str, symkey: str) -> str:
    """Symmetrically encrypt a value, e.g. ready to store in set_data()"""
    value_b = value.encode("utf-8")  # bytes
    symkey_b = symkey.encode("utf-8")  # bytes
    value_enc_b = Fernet(symkey_b).encrypt(value_b)  # main work. bytes
    value_enc = value_enc_b.decode("ascii")  # ascii str
    return value_enc


@enforce_types
def sym_decrypt(value_enc: str, symkey: str) -> str:
    """Symmetrically decrypt a value, e.g. retrieved from get_data()"""
    value_enc_b = value_enc.encode("utf-8")
    symkey_b = symkey.encode("utf-8")
    value_b = Fernet(symkey_b).decrypt(value_enc_b)  # main work
    value = value_b.decode("ascii")
    return value


@enforce_types
def calc_pubkey(privkey: str) -> str:
    privkey_obj = keys.PrivateKey(decode_hex(privkey))
    pubkey = str(privkey_obj.public_key)  # str
    return pubkey


@enforce_types
def asym_encrypt(value: str, pubkey: str) -> str:
    """Asymmetrically encrypt a value, e.g. ready to store in set_data()"""
    value_b = value.encode("utf-8")  # binary
    value_enc_b = asymmetric_encrypt(pubkey, value_b)  # main work. binary
    value_enc_h = value_enc_b.hex()  # hex str
    return value_enc_h


@enforce_types
def asym_decrypt(value_enc_h: str, privkey: str) -> str:
    """Asymmetrically decrypt a value, e.g. retrieved from get_data()"""
    value_enc_b = decode_hex(value_enc_h)  # bytes
    value_b = asymmetric_decrypt(privkey, value_enc_b)  # main work. bytes
    value = value_b.decode("ascii")
    return value
