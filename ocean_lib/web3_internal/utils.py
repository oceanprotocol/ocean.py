#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from collections import namedtuple
from decimal import Decimal

from eth_keys import keys
from eth_utils import big_endian_to_int, decode_hex
from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.web3_internal.constants import DEFAULT_NETWORK_NAME, NETWORK_NAME_MAP
from ocean_lib.web3_internal.web3_overrides.signature import SignatureFix
from ocean_lib.web3_internal.web3_provider import Web3Provider

Signature = namedtuple("Signature", ("v", "r", "s"))

logger = logging.getLogger(__name__)


def generate_multi_value_hash(types, values):
    """
    Return the hash of the given list of values.
    This is equivalent to packing and hashing values in a solidity smart contract
    hence the use of `soliditySha3`.

    :param types: list of solidity types expressed as strings
    :param values: list of values matching the `types` list
    :return: bytes
    """
    assert len(types) == len(values)
    return Web3Provider.get_web3().soliditySha3(types, values)


def prepare_prefixed_hash(msg_hash):
    """

    :param msg_hash:
    :return:
    """
    return generate_multi_value_hash(
        ["string", "bytes32"], ["\x19Ethereum Signed Message:\n32", msg_hash]
    )


def add_ethereum_prefix_and_hash_msg(text):
    """
    This method of adding the ethereum prefix seems to be used in web3.personal.sign/ecRecover.

    :param text: str any str to be signed / used in recovering address from a signature
    :return: hash of prefixed text according to the recommended ethereum prefix
    """
    prefixed_msg = f"\x19Ethereum Signed Message:\n{len(text)}{text}"
    return Web3Provider.get_web3().sha3(text=prefixed_msg)


def to_32byte_hex(web3, val):
    """

    :param web3:
    :param val:
    :return:
    """
    return web3.toBytes(val).rjust(32, b"\0")


def split_signature(web3, signature):
    """

    :param web3:
    :param signature: signed message hash, hex str
    :return:
    """
    assert len(signature) == 65, (
        f"invalid signature, " f"expecting bytes of length 65, got {len(signature)}"
    )
    v = web3.toInt(signature[-1])
    r = to_32byte_hex(web3, int.from_bytes(signature[:32], "big"))
    s = to_32byte_hex(web3, int.from_bytes(signature[32:64], "big"))
    if v != 27 and v != 28:
        v = 27 + v % 2

    return Signature(v, r, s)


@enforce_types_shim
def privateKeyToAddress(private_key: str) -> str:
    return Web3Provider.get_web3().eth.account.privateKeyToAccount(private_key).address


@enforce_types_shim
def privateKeyToPublicKey(private_key: str) -> str:
    private_key_bytes = decode_hex(private_key)
    private_key_object = keys.PrivateKey(private_key_bytes)
    return private_key_object.public_key


@enforce_types_shim
def get_network_name(network_id: int = None) -> str:
    """
    Return the network name based on the current ethereum network id.

    Return `ganache` for every network id that is not mapped.

    :param network_id: Network id, int
    :return: Network name, str
    """
    if not network_id:
        network_id = get_network_id()
    return NETWORK_NAME_MAP.get(network_id, DEFAULT_NETWORK_NAME).lower()


@enforce_types_shim
def get_network_id() -> int:
    """
    Return the ethereum network id calling the `web3.version.network` method.

    :return: Network id, int
    """
    return int(Web3Provider.get_web3().version.network)


@enforce_types_shim
def ec_recover(message, signed_message):
    """
    This method does not prepend the message with the prefix `\x19Ethereum Signed Message:\n32`.
    The caller should add the prefix to the msg/hash before calling this if the signature was
    produced for an ethereum-prefixed message.

    :param message:
    :param signed_message:
    :return:
    """
    w3 = Web3Provider.get_web3()
    v, r, s = split_signature(w3, w3.toBytes(hexstr=signed_message))
    signature_object = SignatureFix(vrs=(v, big_endian_to_int(r), big_endian_to_int(s)))
    return w3.eth.account.recoverHash(
        message, signature=signature_object.to_hex_v_hacked()
    )


@enforce_types_shim
def personal_ec_recover(message, signed_message):
    prefixed_hash = add_ethereum_prefix_and_hash_msg(message)
    return ec_recover(prefixed_hash, signed_message)


@enforce_types_shim
def get_ether_balance(address: str) -> int:
    """
    Get balance of an ethereum address.

    :param address: address, bytes32
    :return: balance, int
    """
    return Web3Provider.get_web3().eth.getBalance(address, block_identifier="latest")


def from_wei(wei_value: int) -> Decimal:
    return Web3Provider.get_web3().fromWei(wei_value, "ether")
