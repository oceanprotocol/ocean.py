#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from collections import namedtuple
from typing import Any, Union

import requests
from enforce_typing import enforce_types
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend
from hexbytes.main import HexBytes
from web3.main import Web3

Signature = namedtuple("Signature", ("v", "r", "s"))

logger = logging.getLogger(__name__)
keys = KeyAPI(NativeECCBackend)


@enforce_types
def to_32byte_hex(val: int) -> str:
    """

    :param val:
    :return:
    """
    return Web3.to_hex(Web3.to_bytes(val).rjust(32, b"\0"))


# reinstate as part of #1461
# @enforce_types
# def sign_with_clef(message_hash: str, wallet: ClefAccount) -> str:
#     message_hash = Web3.solidity_keccak(
#        ["bytes"],
#        [Web3.to_bytes(text=message_hash)],
#    )
#
#    orig_sig = wallet._provider.make_request(
#        "account_signData", ["data/plain", wallet.address, message_hash.hex()]
#    )["result"]
#    return orig_sig


@enforce_types
def sign_with_key(message_hash: Union[HexBytes, str], key: str) -> str:
    if isinstance(message_hash, str):
        message_hash = Web3.solidity_keccak(
            ["bytes"],
            [Web3.to_bytes(text=message_hash)],
        )

    pk = keys.PrivateKey(Web3.to_bytes(hexstr=key))

    prefix = "\x19Ethereum Signed Message:\n32"
    signable_hash = Web3.solidity_keccak(
        ["bytes", "bytes"], [Web3.to_bytes(text=prefix), Web3.to_bytes(message_hash)]
    )

    return keys.ecdsa_sign(message_hash=signable_hash, private_key=pk)


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
    v = Web3.to_int(signature[-1])
    r = to_32byte_hex(int.from_bytes(signature[:32], "big"))
    s = to_32byte_hex(int.from_bytes(signature[32:64], "big"))
    if v != 27 and v != 28:
        v = 27 + v % 2

    return Signature(v, r, s)


@enforce_types
def get_gas_fees() -> tuple:
    # Polygon & Mumbai uses EIP-1559. So, dynamically determine priority fee
    gas_resp = requests.get("https://gasstation.polygon.technology/v2")

    return (
        Web3.to_wei(gas_resp.json()["fast"]["maxPriorityFee"], "gwei"),
        Web3.to_wei(gas_resp.json()["fast"]["maxFee"], "gwei"),
    )
