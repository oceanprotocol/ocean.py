#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Tuple
import random

from Crypto.Util.number import *
from Crypto.Random import get_random_bytes
from enforce_typing import enforce_types


@enforce_types
class ElGamalEncryptedObject:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return f"ElGamalEncryptedObject({self.a}, {self.b})"

    def __repr__(self):
        return str(self)


@enforce_types
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

    def __add__(self, other: "ElGamalEncryptedObject") -> "ElGamalEncryptedObject":
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

    def __mul__(self, other: int) -> "ElGamalEncryptedObject":
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

    def encrypt(self, v: int) -> "ElGamalEncryptedObject":
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

    def decrypt(self, obj: "ElGamalEncryptedObject") -> int:
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
