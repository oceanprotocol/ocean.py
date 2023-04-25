#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Tuple
import random

from base64 import b64encode
from hashlib import sha256

from Crypto.Util.number import *
from Crypto.Random import get_random_bytes
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


class ElGamalEncryptedObject:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return f"ElGamalEncryptedObject({self.a}, {self.b})"

    def __repr__(self):
        return str(self)


class ElGamal:
    """
    Implementation of the ElGamal cryptosystem for encrypting and decrypting integers.
    """

    def __init__(self, bits: int) -> None:
        """
        Initializes an ElGamal object with a key pair.

        Args:
            bits: The number of bits to use for the prime modulus p.
        """
        p, g, x, Y = self._get_keys(bits)
        self.p = p
        self.g = g
        self.x = x
        self.Y = Y

    def __add__(self, other: 'ElGamalEncryptedObject') -> 'ElGamalEncryptedObject':
        """
        Adds two ElGamal encrypted objects using homomorphic addition.

        Args:
            other: The other ElGamal encrypted object to add.

        Returns:
            An ElGamal encrypted object representing the sum of the two encrypted values.
        """
        an = (self.a * other.a) % self.p
        bn = (self.a * other.b) % self.p
        return ElGamalEncryptedObject(an, bn)

    def __mul__(self, other: int) -> 'ElGamalEncryptedObject':
        """
        Multiplies an ElGamal encrypted object by an integer using homomorphic multiplication.

        Args:
            other: The integer to multiply the encrypted value by.

        Returns:
            An ElGamal encrypted object representing the product of the encrypted value and the integer.
        """
        an = pow(self.a, other, self.p)
        bn = pow(self.b, other, self.p)
        return ElGamalEncryptedObject(an, bn)

    def _get_generator(self, p: int) -> int:
        """
        Finds a generator for the group (Z/pZ)*.

        Args:
            p: The prime modulus.

        Returns:
            A generator for the group (Z/pZ)*.
        """
        while True:
            # Find generator which doesn't share factor with p
            generator = random.randrange(3, p)
            if pow(generator, 2, p) == 1:
                continue
            if pow(generator, p, p) == 1:
                continue
            return generator

    def _get_keys(self, bits: int) -> Tuple[int, int, int, int]:
        """
        Generates an ElGamal key pair.

        Args:
            bits: The number of bits to use for the prime modulus p.

        Returns:
            A tuple containing the prime modulus p, the generator g, the private key x, and the public key Y.
        """
        p = getPrime(bits, randfunc=get_random_bytes)
        g = self._get_generator(p)
        x = random.randrange(3, p)
        Y = pow(g, x, p)
        return p, g, x, Y

    def encrypt(self, v: int) -> 'ElGamalEncryptedObject':
        """
        Encrypts an integer using the ElGamal cryptosystem.

        Args:
            v: The integer to encrypt.

        Returns:
            An ElGamal encrypted object representing the encrypted value.
        """
        k = random.randrange(3, self.p)
        a = pow(self.g, k, self.p)
        b = (pow(self.Y, k, self.p) * pow(self.g, v, self.p)) % self.p
        return ElGamalEncryptedObject(a, b)

    def decrypt(self, obj: 'ElGamalEncryptedObject') -> int:
        """
        Decrypts an ElGamal encrypted object and returns the plaintext integer.

        Args:
            obj: The ElGamal encrypted object to decrypt.

        Returns:
            The decrypted integer.
        """
        a = obj.a
        b = obj.b
        return (b * pow(a, self.p - 1 - self.x, self.p)) % self.p
