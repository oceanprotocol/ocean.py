#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from brownie.network import accounts
from enforce_typing import enforce_types
from eth_account.messages import SignableMessage
from web3.datastructures import AttributeDict
from web3.main import Web3

from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
def get_gas_price(web3) -> int:
    return int(web3.eth.gas_price * 1.1)


@enforce_types
def sign_hash(msg_hash: SignableMessage, wallet: Wallet) -> str:
    """
    This method use `personal_sign`for signing a message. This will always prepend the
    `\x19Ethereum Signed Message:\n32` prefix before signing.

    :param msg_hash:
    :param wallet: Wallet instance
    :return: signature
    """
    s = wallet.sign(msg_hash)
    return s.signature.hex()


@enforce_types
def send_ether(from_wallet: Wallet, to_address: str, amount: int) -> AttributeDict:
    if not Web3.isChecksumAddress(to_address):
        to_address = Web3.toChecksumAddress(to_address)

    accounts.at(from_wallet.address).transfer(to_address, "1 ether")
    receipt = from_wallet.transfer(to_address, "{amount} ether")

    return receipt.txid
