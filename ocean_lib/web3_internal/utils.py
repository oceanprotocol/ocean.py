#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from collections import namedtuple
from typing import Any

from enforce_typing import enforce_types
from eth_account.account import Account
from eth_keys import keys
from eth_utils import decode_hex
from web3.main import Web3

Signature = namedtuple("Signature", ("v", "r", "s"))

logger = logging.getLogger(__name__)


@enforce_types
def to_32byte_hex(val: int) -> str:
    """

    :param val:
    :return:
    """
    return Web3.toHex(Web3.toBytes(val).rjust(32, b"\0"))


@enforce_types
def split_signature(signature: Any) -> Signature:
    """

    :param web3:
    :param signature: signed message hash, hex str
    :return:
    """
    assert len(signature) == 65, (
        f"invalid signature, " f"expecting bytes of length 65, got {len(signature)}"
    )
    v = Web3.toInt(signature[-1])
    r = to_32byte_hex(int.from_bytes(signature[:32], "big"))
    s = to_32byte_hex(int.from_bytes(signature[32:64], "big"))
    if v != 27 and v != 28:
        v = 27 + v % 2

    return Signature(v, r, s)


@enforce_types
def private_key_to_address(private_key: str) -> str:
    return Account.from_key(private_key).address


@enforce_types
def private_key_to_public_key(private_key: str) -> str:
    private_key_bytes = decode_hex(private_key)
    private_key_object = keys.PrivateKey(private_key_bytes)
    return private_key_object.public_key
