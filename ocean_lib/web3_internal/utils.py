#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import os
from collections import namedtuple
from typing import Any

import web3.gas_strategies.rpc
from enforce_typing import enforce_types
from eth_account.account import Account
from eth_keys import keys
from eth_utils import decode_hex
from web3.main import Web3

from ocean_lib.web3_internal.constants import (
    ENV_GAS_PRICE,
    ENV_MAX_GAS_PRICE,
    GAS_LIMIT_DEFAULT,
)

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


@enforce_types
def get_ether_balance(web3: Web3, address: str) -> int:
    """
    Get balance of an ethereum address.

    :param address: address, bytes32
    :return: balance, int
    """
    return web3.eth.get_balance(address, block_identifier="latest")


@enforce_types
def get_gas_price(web3_object: Web3, tx: dict) -> dict:
    try:
        history = web3_object.eth.fee_history(block_count=1, newest_block="latest")
    except ValueError:
        # environment variable gas price evaluation
        if os.getenv("GAS_SCALING_FACTOR"):
            gas_price = int(
                web3_object.eth.gas_price * float(os.getenv("GAS_SCALING_FACTOR"))
            )
        elif os.getenv(ENV_GAS_PRICE):
            gas_price = int(os.getenv(ENV_GAS_PRICE))
        else:
            gas_price = web3.gas_strategies.rpc.rpc_gas_price_strategy(web3_object)

        max_gas_price = os.getenv(ENV_MAX_GAS_PRICE, None)
        if gas_price and max_gas_price:
            gas_price = min(gas_price, int(max_gas_price))
        tx["gasPrice"] = gas_price

        return tx

    # EIP 1559 gas fees calculation
    tx["maxPriorityFeePerGas"] = web3_object.eth.max_priority_fee
    tx["maxFeePerGas"] = (
        web3_object.eth.max_priority_fee + 2 * history["baseFeePerGas"][0]
    )
    tx["type"] = "0x2"
    tx["gas"] = GAS_LIMIT_DEFAULT

    return tx
