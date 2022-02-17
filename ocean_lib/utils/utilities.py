#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""Utilities class"""
import hashlib
from typing import Tuple

from enforce_typing import enforce_types
from eth_account.datastructures import SignedMessage
from eth_typing import HexStr
from eth_typing.encoding import Primitives
from web3.main import Web3


@enforce_types
def to_lpad_32byte(val: Primitives) -> bytes:
    """
    ecrecover in Solidity expects v as a native uint8, but r and s as left-padded bytes32
    This convenience method will add the padding

    Adapted from https://web3py.readthedocs.io/en/stable/web3.eth.account.html#prepare-message-for-ecrecover-in-solidity
    """
    return Web3.toBytes(val).rjust(32, b"\0")


@enforce_types
def to_lpad_32byte_hex(val: Primitives) -> HexStr:
    """
    ecrecover in Solidity expects v as a native uint8, but r and s as left-padded bytes32
    Remix / web3.js expect r and s to be encoded to hex
    This convenience method will add the padding and encode to hex

    Copied from https://web3py.readthedocs.io/en/stable/web3.eth.account.html#prepare-message-for-ecrecover-in-solidity
    """
    return Web3.toHex(to_lpad_32byte(val))


@enforce_types
def prepare_message_for_ecrecover_in_solidity(
    signed_message: SignedMessage,
) -> Tuple[HexStr, int, str, str]:
    """
    Copied from https://web3py.readthedocs.io/en/stable/web3.eth.account.html#prepare-message-for-ecrecover-in-solidity
    """
    return (
        Web3.toHex(signed_message.messageHash),
        signed_message.v,
        to_lpad_32byte_hex(signed_message.r),
        to_lpad_32byte_hex(signed_message.s),
    )


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
def create_checksum(text: str) -> str:
    """
    :return: str
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
