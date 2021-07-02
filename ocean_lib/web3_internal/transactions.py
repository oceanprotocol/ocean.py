#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.web3_internal.wallet import Wallet
from web3.main import Web3


@enforce_types
def sign_hash(msg_hash, wallet: Wallet) -> str:
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
def send_ether(from_wallet: Wallet, to_address: str, ether_amount: int):
    if not Web3.isChecksumAddress(to_address):
        to_address = Web3.toChecksumAddress(to_address)

    web3 = from_wallet.web3

    tx = {
        "from": from_wallet.address,
        "to": to_address,
        "value": Web3.toWei(ether_amount, "ether"),
        "chainId": web3.eth.chain_id,
    }
    tx["gas"] = web3.eth.estimate_gas(tx)
    raw_tx = from_wallet.sign_tx(tx)
    tx_hash = web3.eth.send_raw_transaction(raw_tx)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
    return receipt


@enforce_types
def cancel_or_replace_transaction(
    from_wallet: Wallet, nonce_value, gas_price=None, gas_limit=None
):
    web3 = from_wallet.web3
    tx = {
        "from": from_wallet.address,
        "to": from_wallet.address,
        "value": 0,
        "chainId": web3.eth.chain_id,
    }
    gas = gas_limit if gas_limit is not None else web3.eth.estimate_gas(tx)
    tx["gas"] = gas + 1
    raw_tx = from_wallet.sign_tx(tx, fixed_nonce=nonce_value, gas_price=gas_price)
    tx_hash = web3.eth.send_raw_transaction(raw_tx)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
    return receipt
