#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
    Public key base

    Currently this class stores the public keys in the same form as in the JSON
    text data.

"""

#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import json
import re
from base64 import b64decode, b64encode, b85decode, b85encode

PUBLIC_KEY_STORE_TYPE_PEM = "publicKeyPem"
PUBLIC_KEY_STORE_TYPE_JWK = "publicKeyJwk"
PUBLIC_KEY_STORE_TYPE_HEX = "publicKeyHex"
PUBLIC_KEY_STORE_TYPE_BASE64 = "publicKeyBase64"
PUBLIC_KEY_STORE_TYPE_BASE85 = "publicKeyBase85"


class PublicKeyBase:
    """Base Public Key class, to allow to perfom basic key storage and validation using DDO keys."""

    def __init__(self, key_id, **kwargs):
        self._id = key_id
        self._owner = kwargs.get("owner", None)
        self._type = kwargs.get("type", None)

    def get_id(self):
        """Get the key id."""
        return self._id

    def assign_did(self, did):
        """
        assign the DID as the key id, if the DID does not have a '#value'
        at the end, then automatically add a new key value
        """
        if re.match("^#.*", self._id):
            self._id = did + self._id
        if re.match("^#.*", self._owner):
            self._owner = did + self._owner

    def get_owner(self):
        """Get the owner of this key."""
        return self._owner

    # def set_owner(self, value):
    # self._owner = value

    def get_type(self):
        """Get the type of key."""
        return self._type

    def get_store_type(self):
        """Get the type of key storage."""
        return self._store_type

    def set_key_value(self, value, store_type=PUBLIC_KEY_STORE_TYPE_BASE64):
        """Set the key value based on it's storage type."""
        if isinstance(value, dict):
            if PUBLIC_KEY_STORE_TYPE_HEX in value:
                self.set_key_value(
                    value[PUBLIC_KEY_STORE_TYPE_HEX], PUBLIC_KEY_STORE_TYPE_HEX
                )
            elif PUBLIC_KEY_STORE_TYPE_BASE64 in value:
                self.set_key_value(
                    value[PUBLIC_KEY_STORE_TYPE_BASE64], PUBLIC_KEY_STORE_TYPE_BASE64
                )
            elif PUBLIC_KEY_STORE_TYPE_BASE85 in value:
                self.set_key_value(
                    value[PUBLIC_KEY_STORE_TYPE_BASE85], PUBLIC_KEY_STORE_TYPE_BASE85
                )
            elif PUBLIC_KEY_STORE_TYPE_JWK in value:
                self.set_key_value(
                    value[PUBLIC_KEY_STORE_TYPE_JWK], PUBLIC_KEY_STORE_TYPE_JWK
                )
            elif PUBLIC_KEY_STORE_TYPE_PEM in value:
                self.set_key_value(
                    value[PUBLIC_KEY_STORE_TYPE_PEM], PUBLIC_KEY_STORE_TYPE_PEM
                )
        else:
            self._value = value
            self._store_type = store_type

    def set_encode_key_value(self, value, store_type):
        """Save the key value base on it's storage type."""
        self._store_type = store_type
        if store_type == PUBLIC_KEY_STORE_TYPE_HEX:
            self._value = value.hex()
        elif store_type == PUBLIC_KEY_STORE_TYPE_BASE64:
            self._value = b64encode(value).decode()
        elif store_type == PUBLIC_KEY_STORE_TYPE_BASE85:
            self._value = b85encode(value).decode()
        elif store_type == PUBLIC_KEY_STORE_TYPE_JWK:
            # TODO: need to decide on which jwk library to import?
            raise NotImplementedError
        else:
            self._value = value
        return value

    def get_decode_value(self):
        """Return the key value based on it's storage type."""
        if self._store_type == PUBLIC_KEY_STORE_TYPE_HEX:
            value = bytes.fromhex(self._value)
        elif self._store_type == PUBLIC_KEY_STORE_TYPE_BASE64:
            value = b64decode(self._value)
        elif self._store_type == PUBLIC_KEY_STORE_TYPE_BASE85:
            value = b85decode(self._value)
        elif self._store_type == PUBLIC_KEY_STORE_TYPE_JWK:
            # TODO: need to decide on which jwk library to import?
            raise NotImplementedError
        else:
            value = self._value
        return value

    def get_value(self):
        """Get the key value."""
        return self._value

    def as_text(self, is_pretty=False):
        """Return the key as JSON text."""
        values = {"id": self._id, "type": self._type}
        if self._owner:
            values["owner"] = self._owner

        if is_pretty:
            return json.dumps(values, indent=4, separators=(",", ": "))

        return json.dumps(values)

    def as_dictionary(self):
        """Return the key as a python dictionary."""
        values = {"id": self._id, "type": self._type}

        if self._owner:
            values["owner"] = self._owner
        return values

    def is_valid(self):
        """Return True if the key structure is valid."""
        return self._id and self._type

    def get_authentication_type(self):
        """Base overloaded method to return the authentication type to use for this key."""
        raise NotImplementedError
