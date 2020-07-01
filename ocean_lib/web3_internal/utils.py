#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import eth_account
import logging
import os
from collections import namedtuple

from eth_keys import KeyAPI
from eth_utils import big_endian_to_int
from web3 import Web3
from web3.contract import ContractEvent
from web3.exceptions import TimeExhausted

from ocean_lib.ocean import util
from ocean_lib.web3_internal.account import Account
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

def get_account(index: int) -> Account:
    #for testing
    network = 'ganache'
    assert index in [0,1]
    label = 'TEST_PRIVATE_KEY' + str(index+1)
    private_key = util.confFileValue(network, label)
    account = Account(private_key=private_key)
    return account
    
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
    except TimeExhausted:
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
