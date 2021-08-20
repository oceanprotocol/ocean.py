#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from web3 import Web3

from ocean_lib.web3_internal.web3_overrides.utils import fetch_transaction
from tests.resources.helper_functions import get_publisher_wallet, get_consumer_wallet


def test_fetching_transaction_after_multiple_blocks(monkeypatch):
    monkeypatch.setenv("BLOCK_CONFIRMATIONS", "6")

    publisher_wallet = get_publisher_wallet()
    consumer_address = get_consumer_wallet().address

    if not Web3.isChecksumAddress(consumer_address):
        consumer_address = Web3.toChecksumAddress(consumer_address)

    web3 = publisher_wallet.web3
    tx = {
        "from": publisher_wallet.address,
        "to": consumer_address,
        "value": Web3.toWei(1.0, "ether"),
        "chainId": web3.eth.chain_id,
    }
    tx["gas"] = web3.eth.estimate_gas(tx)
    raw_tx = publisher_wallet.sign_tx(tx)
    tx_hash = web3.eth.send_raw_transaction(raw_tx)
    fetch_transaction(tx_hash, tx, publisher_wallet)
    receipt = web3.eth.get_transaction_receipt(tx_hash)
    assert receipt
    assert web3.eth.block_number >= receipt.blockNumber + 6
