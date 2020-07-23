#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0
import json
import logging
import os
from collections import namedtuple

import eth_account
import eth_keys
import eth_utils
from eth_keys import KeyAPI
from eth_utils import big_endian_to_int
from web3 import Web3
from web3.contract import ContractEvent
from ocean_lib.web3_internal.web3_provider import Web3Provider

Signature = namedtuple('Signature', ('v', 'r', 's'))

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
    return Web3.soliditySha3(
        types,
        values
    )


def prepare_prefixed_hash(msg_hash):
    """

    :param msg_hash:
    :return:
    """
    return generate_multi_value_hash(
        ['string', 'bytes32'],
        ["\x19Ethereum Signed Message:\n32", msg_hash]
    )


def add_ethereum_prefix_and_hash_msg(text):
    """
    This method of adding the ethereum prefix seems to be used in web3.personal.sign/ecRecover.

    :param text: str any str to be signed / used in recovering address from a signature
    :return: hash of prefixed text according to the recommended ethereum prefix
    """
    prefixed_msg = f"\x19Ethereum Signed Message:\n{len(text)}{text}"
    return Web3.sha3(text=prefixed_msg)


def get_public_key_from_address(web3, account):
    """

    :param web3:
    :param account:
    :return:
    """
    _hash = web3.sha3(text='verify signature.')
    signature = web3.personal.sign(_hash, account.address, account.password)
    signature = split_signature(web3, web3.toBytes(hexstr=signature))
    signature_vrs = Signature(signature.v % 27,
                              big_endian_to_int(signature.r),
                              big_endian_to_int(signature.s))
    prefixed_hash = prepare_prefixed_hash(_hash)
    pub_key = KeyAPI.PublicKey.recover_from_msg_hash(prefixed_hash,
                                                     KeyAPI.Signature(vrs=signature_vrs))
    assert pub_key.to_checksum_address() == account.address, \
        'recovered address does not match signing address.'
    return pub_key


def to_32byte_hex(web3, val):
    """

    :param web3:
    :param val:
    :return:
    """
    return web3.toBytes(val).rjust(32, b'\0')


def split_signature(web3, signature):
    """

    :param web3:
    :param signature: signed agreement hash, hex str
    :return:
    """
    assert len(signature) == 65, f'invalid signature, ' \
                                 f'expecting bytes of length 65, got {len(signature)}'
    v = web3.toInt(signature[-1])
    r = to_32byte_hex(web3, int.from_bytes(signature[:32], 'big'))
    s = to_32byte_hex(web3, int.from_bytes(signature[32:64], 'big'))
    if v != 27 and v != 28:
        v = 27 + v % 2

    return Signature(v, r, s)


def get_wallet(index):
    name = 'PARITY_ADDRESS' if not index else f'PARITY_ADDRESS{index}'
    pswrd_name = 'PARITY_PASSWORD' if not index else f'PARITY_PASSWORD{index}'
    key_name = 'PARITY_KEY' if not index else f'PARITY_KEY{index}'
    encrypted_key_name = 'PARITY_ENCRYPTED_KEY' if not index else f'PARITY_ENCRYPTED_KEY{index}'
    keyfile_name = 'PARITY_KEYFILE' if not index else f'PARITY_KEYFILE{index}'

    address = os.getenv(name)
    if not address:
        return None

    pswrd = os.getenv(pswrd_name)
    key = os.getenv(key_name)
    encr_key = os.getenv(encrypted_key_name)
    key_file = os.getenv(keyfile_name)
    if key_file and not encr_key:
        with open(key_file) as _file:
            encr_key = json.loads(_file.read())

    from ocean_lib.web3_internal.wallet import Wallet
    return Wallet(
        Web3Provider.get_web3(),
        private_key=key,
        encrypted_key=encr_key,
        address=Web3.toChecksumAddress(address),
        password=pswrd
    )


def process_tx_receipt(tx_hash, event_instance, event_name, agreement_id=None):
    """
    Wait until the tx receipt is processed.

    :param tx_hash: hash of the transaction
    :param event_instance: instance of ContractEvent
    :param event_name: name of the event to subscribe, str
    :param agreement_id: hex str
    :return:
    """
    if not isinstance(tx_hash, bytes):
        raise TypeError(f'first argument should be bytes type, '
                        f'got type {type(tx_hash)} and value {tx_hash}')
    if not isinstance(event_instance, ContractEvent):
        raise TypeError(f'second argument should be a ContractEvent, '
                        f'got {event_instance} of type {type(event_instance)}')
    web3 = Web3Provider.get_web3()
    try:
        web3.eth.waitForTransactionReceipt(tx_hash, timeout=20)
    except Exception:
        logger.info(f'Waiting for {event_name} transaction receipt timed out. '
                    f'Cannot verify receipt and event.')
        return False

    receipt = web3.eth.getTransactionReceipt(tx_hash)
    event_logs = event_instance.processReceipt(receipt) if receipt else None
    if event_logs:
        logger.info(f'Success: got {event_name} event after fulfilling condition.')
        logger.debug(
            f'Success: got {event_name} event after fulfilling condition. {receipt}, '
            f'::: {event_logs}')
    else:
        logger.debug(f'Something is not right, cannot find the {event_name} event after calling the'
                     f' fulfillment condition. This is the transaction receipt {receipt}')

    if receipt and receipt.status == 0:
        logger.warning(
            f'Transaction failed: tx_hash {tx_hash.hex()}, tx event {event_name}, receipt '
            f'{receipt}, id {agreement_id}')
        return False

    return True


def privateKeyToAddress(private_key: str) -> str:
    return eth_account.Account().privateKeyToAccount(private_key).address


def privateKeyToPublicKey(private_key: str):
    private_key_bytes = eth_utils.decode_hex(private_key)
    private_key_object = eth_keys.keys.PrivateKey(private_key_bytes)
    return private_key_object.public_key
