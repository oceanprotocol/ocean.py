from base64 import b64encode
from hashlib import sha256
from cryptography.fernet import Fernet
from ecies import decrypt as asymmetric_decrypt, encrypt as asymmetric_encrypt
from enforce_typing import enforce_types
from eth_keys import keys
from eth_utils import decode_hex

@enforce_types
def calc_symkey(base_str: str) -> str:
    return (b64encode(sha256(base_str.encode("utf-8")).digest())[:43] + b"=").decode("ascii")

@enforce_types
def sym_encrypt(value: str, symkey: str) -> str:
    return Fernet(symkey.encode("utf-8")).encrypt(value.encode("utf-8")).decode("ascii")

@enforce_types
def sym_decrypt(value_enc: str, symkey: str) -> str:
    return Fernet(symkey.encode("utf-8")).decrypt(value_enc.encode("utf-8")).decode("ascii")

@enforce_types
def calc_pubkey(privkey: str) -> str:
    return str(keys.PrivateKey(decode_hex(privkey)).public_key)

@enforce_types
def asym_encrypt(value: str, pubkey: str) -> str:
    return asymmetric_encrypt(pubkey, value.encode("utf-8")).hex()

@enforce_types
def asym_decrypt(value_enc_h: str, privkey: str) -> str:
    return asymmetric_decrypt(privkey, decode_hex(value_enc_h)).decode("ascii")
