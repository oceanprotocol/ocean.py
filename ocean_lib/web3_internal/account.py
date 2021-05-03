#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Accounts module."""
import logging
import os

from ocean_lib.web3_internal.utils import privateKeyToAddress

logger = logging.getLogger("account")


class Account:

    """Class representing an account."""

    def __init__(
        self,
        address=None,
        password=None,
        key_file=None,
        encrypted_key=None,
        private_key=None,
    ):
        """Hold account address, password and either keyfile path, encrypted key or private key.

        :param address: The address of this account
        :param password: account's password. This is necessary for decrypting the private key
            to be able to sign transactions locally
        :param key_file: str path to the encrypted private key file
        :param encrypted_key:
        :param private_key:
        """
        assert (
            key_file or encrypted_key or private_key
        ), "Account requires one of `key_file`, `encrypted_key`, or `private_key`."
        if key_file or encrypted_key:
            assert (
                password
            ), "`password` is required when using `key_file` or `encrypted_key`."

        if private_key:
            password = None

        self.address = address
        self.password = password
        self._key_file = key_file
        if self._key_file and not encrypted_key:
            with open(self.key_file) as _file:
                encrypted_key = _file.read()
        self._encrypted_key = encrypted_key
        self._private_key = private_key

        if self.address is None and self._private_key is not None:
            self.address = privateKeyToAddress(private_key)

        assert self.address is not None

    @property
    def key_file(self):
        """Holds the key file path"""
        return (
            os.path.expandvars(os.path.expanduser(self._key_file))
            if self._key_file
            else None
        )

    @property
    def private_key(self):
        """Holds the private key"""
        return self._private_key

    @property
    def key(self):
        """Returns the private key (if defined) or the encrypted key."""
        if self._private_key:
            return self._private_key

        return self._encrypted_key
