#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time

from brownie.network import accounts
from brownie.network.transaction import TransactionReceipt
from enforce_typing import enforce_types
from eth_account.messages import SignableMessage
from web3.datastructures import AttributeDict
from web3.main import Web3


# TODO: look into signing, should we keep anything?
@enforce_types
def sign_hash(msg_hash: SignableMessage, wallet) -> str:
    """
    This method use `personal_sign`for signing a message. This will always prepend the
    `\x19Ethereum Signed Message:\n32` prefix before signing.

    :param msg_hash:
    :param wallet: Wallet instance
    :return: signature
    """
    s = wallet.sign_message(msg_hash)
    return s.signature.hex()


@enforce_types
def send_ether(
    config: dict, from_wallet, to_address: str, amount: str
) -> AttributeDict:
    if not Web3.isChecksumAddress(to_address):
        to_address = Web3.toChecksumAddress(to_address)

    receipt = accounts.at(from_wallet.address).transfer(to_address, amount)

    return wait_for_transaction_status(receipt.txid, config["TRANSACTION_TIMEOUT"])


def wait_for_transaction_status(txid: str, timeout: int):
    receipt = TransactionReceipt(txid)

    if timeout == 0:
        return txid

    start = time.time()
    receipt = TransactionReceipt(txid)

    if receipt.status.value == 1:
        return txid

    while time.time() - start > timeout:
        receipt = TransactionReceipt(txid)
        if receipt.status.value == 1:
            return txid

        time.sleep(0.2)

    raise Exception("Transaction Timeout reached without successful status.")
