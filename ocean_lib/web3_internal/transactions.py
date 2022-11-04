#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend
from web3.main import Web3

keys = KeyAPI(NativeECCBackend)


def sign_with_key(message_hash, key):
    pk = keys.PrivateKey(Web3.toBytes(hexstr=key))
    prefix = "\x19Ethereum Signed Message:\n32"
    signable_hash = Web3.solidityKeccak(
        ["bytes", "bytes"], [Web3.toBytes(text=prefix), Web3.toBytes(message_hash)]
    )
    return keys.ecdsa_sign(message_hash=signable_hash, private_key=pk)
