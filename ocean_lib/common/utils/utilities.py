#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""Utilities class"""
import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Dict

from enforce_typing import enforce_types
from eth_typing import HexStr
from web3.main import Web3


@enforce_types
def generate_new_id() -> str:
    """
    Generate a new id without prefix.

    :return: Id, str
    """
    return uuid.uuid4().hex + uuid.uuid4().hex


@enforce_types
def to_32byte_hex(val: Any) -> str:
    """

    :param val:
    :return:
    """
    return Web3.toBytes(val).rjust(32, b"\0")


@enforce_types
def convert_to_bytes(data: str) -> bytes:
    """

    :param data:
    :return:
    """
    return Web3.toBytes(text=data)


@enforce_types
def convert_to_string(data: bytes) -> HexStr:
    """

    :param data:
    :return:
    """
    return Web3.toHex(data)


@enforce_types
def convert_to_text(data: bytes) -> str:
    """

    :param data:
    :return:
    """
    return Web3.toText(data)


@enforce_types
def checksum(seed: Dict[str, Any]) -> str:
    """Calculate the hash3_256."""
    return hashlib.sha3_256(
        (json.dumps(dict(sorted(seed.items(), reverse=False))).replace(" ", "")).encode(
            "utf-8"
        )
    ).hexdigest()


@enforce_types
def get_timestamp() -> str:
    """Return the current system timestamp."""
    return f"{datetime.utcnow().replace(microsecond=0).isoformat()}Z"
