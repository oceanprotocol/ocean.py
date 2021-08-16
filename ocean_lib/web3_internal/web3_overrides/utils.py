#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
from typing import Optional

from enforce_typing import enforce_types
from hexbytes import HexBytes
from web3 import Web3

from ocean_lib.config import DEFAULT_BLOCK_CONFIRMATIONS
from ocean_lib.web3_internal.utils import get_network_timeout
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
def send_dummy_transactions(block_number: int, from_wallet: Wallet) -> None:
    web3 = from_wallet.web3

    while web3.eth.block_number < block_number + DEFAULT_BLOCK_CONFIRMATIONS:
        tx = {
            "from": from_wallet.address,
            "to": "0xF9f2DB837b3db03Be72252fAeD2f6E0b73E428b9",
            "value": Web3.toWei(0.001, "ether"),
            "chainId": web3.eth.chain_id,
        }
        tx["gas"] = web3.eth.estimate_gas(tx)
        raw_tx = from_wallet.sign_tx(tx)
        web3.eth.send_raw_transaction(raw_tx)
        time.sleep(2.5)


@enforce_types
def fetch_transaction(
    web3: Web3,
    tx_hash: HexBytes,
    tx: dict,
    from_wallet: Wallet,
    timeout: Optional[int] = None,
) -> None:
    receipt = (
        web3.eth.wait_for_transaction_receipt(tx_hash, timeout)
        if timeout
        else web3.eth.wait_for_transaction_receipt(tx_hash)
    )
    if tx["chainId"] == 1337:
        send_dummy_transactions(receipt.blockNumber, from_wallet)
    else:
        while web3.eth.block_number < receipt.blockNumber + DEFAULT_BLOCK_CONFIRMATIONS:
            time.sleep(get_network_timeout(tx["chainId"]))
