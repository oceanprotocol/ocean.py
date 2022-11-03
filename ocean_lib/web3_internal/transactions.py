#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from brownie.network import accounts
from enforce_typing import enforce_types
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend
from web3.datastructures import AttributeDict
from web3.main import Web3

keys = KeyAPI(NativeECCBackend)


@enforce_types
def send_ether(
    config: dict, from_wallet, to_address: str, amount: str
) -> AttributeDict:
    if not Web3.isChecksumAddress(to_address):
        to_address = Web3.toChecksumAddress(to_address)

    return accounts.at(from_wallet.address).transfer(to_address, amount)


def sign_with_key(message_hash, key):
    pk = keys.PrivateKey(Web3.toBytes(hexstr=key))
    prefix = "\x19Ethereum Signed Message:\n32"
    signable_hash = Web3.solidityKeccak(
        ["bytes", "bytes"], [Web3.toBytes(text=prefix), Web3.toBytes(message_hash)]
    )
    return keys.ecdsa_sign(message_hash=signable_hash, private_key=pk)
