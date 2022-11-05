#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from collections import namedtuple
from typing import Any

from brownie import network
from enforce_typing import enforce_types
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend
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
    return Web3.toHex(Web3.toBytes(val).rjust(32, b"\0"))


def sign_with_key(message_hash, key):
    pk = keys.PrivateKey(Web3.toBytes(hexstr=key))
    prefix = "\x19Ethereum Signed Message:\n32"
    signable_hash = Web3.solidityKeccak(
        ["bytes", "bytes"], [Web3.toBytes(text=prefix), Web3.toBytes(message_hash)]
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
    v = Web3.toInt(signature[-1])
    r = to_32byte_hex(int.from_bytes(signature[:32], "big"))
    s = to_32byte_hex(int.from_bytes(signature[32:64], "big"))
    if v != 27 and v != 28:
        v = 27 + v % 2

    return Signature(v, r, s)


def connect_to_network(network_name):
    if network.is_connected():
        if network.show_active() != network_name:
            network.disconnect()
            network.connect(network_name)
    else:
        network.connect(network_name)


def check_network(network_name):
    if not network.is_connected():
        raise Exception(
            'Brownie network is not connected. Please call network.connect("{network_name}")'
        )

    active_network = network.show_active()

    if active_network != network_name:
        raise Exception(
            'Brownie network is connected to {active_network}. Please call network.connect("{network_name}")'
        )
