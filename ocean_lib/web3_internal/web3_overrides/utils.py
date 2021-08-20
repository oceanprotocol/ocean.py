#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
from typing import Optional

from enforce_typing import enforce_types
from hexbytes import HexBytes
from web3 import Web3

from ocean_lib.config import Config
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
def send_dummy_transactions(block_number: int, from_wallet: Wallet) -> None:
    web3 = from_wallet.web3
    config = Config()
    while web3.eth.block_number < block_number + config.block_confirmations:
        tx = {
            "from": from_wallet.address,
            "to": "0xF9f2DB837b3db03Be72252fAeD2f6E0b73E428b9",
            "value": Web3.toWei(0.001, "ether"),
            "chainId": web3.eth.chain_id,
        }
        tx["gas"] = web3.eth.estimate_gas(tx)
        raw_tx = from_wallet.sign_tx(tx)
        web3.eth.send_raw_transaction(raw_tx)
        from ocean_lib.example_config import (
            CONFIG_NETWORK_HELPER,
            NAME_BLOCK_CONFIRMATION_POLL_INTERVAL,
        )

        time.sleep(CONFIG_NETWORK_HELPER[1337][NAME_BLOCK_CONFIRMATION_POLL_INTERVAL])


@enforce_types
def fetch_transaction(
    tx_hash: HexBytes,
    tx: dict,
    from_wallet: Wallet,
    timeout: Optional[int] = None,
) -> None:
    web3 = from_wallet.web3
    config = Config()
    receipt = (
        web3.eth.wait_for_transaction_receipt(tx_hash, timeout)
        if timeout
        else web3.eth.wait_for_transaction_receipt(tx_hash)
    )
    from ocean_lib.example_config import (
        CONFIG_NETWORK_HELPER,
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL,
    )

    if tx["chainId"] == 1337:
        send_dummy_transactions(receipt.blockNumber, from_wallet)
    else:
        while web3.eth.block_number < receipt.blockNumber + config.block_confirmations:
            time.sleep(
                CONFIG_NETWORK_HELPER[tx["chainId"]][
                    NAME_BLOCK_CONFIRMATION_POLL_INTERVAL
                ]
            )
