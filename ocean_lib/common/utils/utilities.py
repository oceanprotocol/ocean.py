#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""Utilities class"""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import hashlib
import json
import uuid
from datetime import datetime

from ocean_lib.common.agreements.consumable import MalformedCredential


def generate_new_id():
    """
    Generate a new id without prefix.

    :return: Id, str
    """
    return uuid.uuid4().hex + uuid.uuid4().hex


def to_32byte_hex(web3, val):
    """

    :param web3:
    :param val:
    :return:
    """
    return web3.toBytes(val).rjust(32, b"\0")


def convert_to_bytes(web3, data):
    """

    :param web3:
    :param data:
    :return:
    """
    return web3.toBytes(text=data)


def convert_to_string(web3, data):
    """

    :param web3:
    :param data:
    :return:
    """
    return web3.toHex(data)


def convert_to_text(web3, data):
    """

    :param web3:
    :param data:
    :return:
    """
    return web3.toText(data)


def checksum(seed):
    """Calculate the hash3_256."""
    return hashlib.sha3_256(
        (json.dumps(dict(sorted(seed.items(), reverse=False))).replace(" ", "")).encode(
            "utf-8"
        )
    ).hexdigest()


def get_timestamp():
    """Return the current system timestamp."""
    return f"{datetime.utcnow().replace(microsecond=0).isoformat()}Z"


def simplify_credential_to_address(credential):
    if not credential:
        return None

    if not credential.get("value"):
        raise MalformedCredential("Received empty address.")

    return credential["value"]


def get_list_entry_with_type_address(types_list):
    return [entry for entry in types_list if entry["type"] == "address"]
