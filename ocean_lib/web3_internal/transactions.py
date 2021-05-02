#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider


@enforce_types_shim
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


def send_ether(from_wallet: Wallet, to_address: str, ether_amount: int):
    w3 = Web3Provider.get_web3()
    if not w3.isChecksumAddress(to_address):
        to_address = w3.toChecksumAddress(to_address)

    tx = {
        "from": from_wallet.address,
        "to": to_address,
        "value": w3.toWei(ether_amount, "ether"),
    }
    _ = w3.eth.estimateGas(tx)
    tx = {
        "from": from_wallet.address,
        "to": to_address,
        "value": w3.toWei(ether_amount, "ether"),
        "gas": 500000,
    }
    wallet = Wallet(w3, private_key=from_wallet.key, address=from_wallet.address)
    raw_tx = wallet.sign_tx(tx)
    tx_hash = w3.eth.sendRawTransaction(raw_tx)
    receipt = w3.eth.waitForTransactionReceipt(tx_hash, timeout=30)
    return receipt


def cancel_or_replace_transaction(
    from_wallet, nonce_value, gas_price=None, gas_limit=None
):
    w3 = Web3Provider.get_web3()
    tx = {"from": from_wallet.address, "to": from_wallet.address, "value": 0}
    gas = gas_limit if gas_limit is not None else w3.eth.estimateGas(tx)
    tx = {
        "from": from_wallet.address,
        "to": from_wallet.address,
        "value": 0,
        "gas": gas + 1,
    }

    wallet = Wallet(w3, private_key=from_wallet.key, address=from_wallet.address)
    raw_tx = wallet.sign_tx(tx, fixed_nonce=nonce_value, gas_price=gas_price)
    tx_hash = w3.eth.sendRawTransaction(raw_tx)
    receipt = w3.eth.waitForTransactionReceipt(tx_hash, timeout=30)
    return receipt
