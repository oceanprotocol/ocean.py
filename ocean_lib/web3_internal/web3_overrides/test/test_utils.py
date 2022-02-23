#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from threading import Event, Thread, current_thread

import pytest

from ocean_lib.web3_internal.constants import BLOCK_NUMBER_POLL_INTERVAL
from ocean_lib.web3_internal.transactions import get_gas_price
from ocean_lib.web3_internal.web3_overrides.utils import (
    wait_for_transaction_receipt_and_block_confirmations,
)


@pytest.mark.unit
def test_block_confirmations(publisher_wallet, consumer_wallet):
    alice_wallet = publisher_wallet
    bob_address = consumer_wallet.address

    # Send transaction first, start dummy tx thread second
    # else risk race condition: out of order nonce

    web3 = alice_wallet.web3
    tx = {
        "from": alice_wallet.address,
        "to": bob_address,
        "value": 1,
        "chainId": web3.eth.chain_id,
        "gasPrice": get_gas_price(web3),
    }
    tx["gas"] = web3.eth.estimate_gas(tx)
    raw_tx = alice_wallet.sign_tx(tx)
    tx_hash = web3.eth.send_raw_transaction(raw_tx)

    # Start thread that sends dummy transactions
    dummy_tx_thread = StoppableThread(
        target=send_dummy_transactions, args=(alice_wallet, bob_address)
    )
    dummy_tx_thread.start()

    poll_interval = BLOCK_NUMBER_POLL_INTERVAL[8996]
    wait_for_transaction_receipt_and_block_confirmations(
        web3, tx_hash, block_confirmations=0, block_number_poll_interval=poll_interval
    )

    wait_for_transaction_receipt_and_block_confirmations(
        web3, tx_hash, block_confirmations=1, block_number_poll_interval=poll_interval
    )

    wait_for_transaction_receipt_and_block_confirmations(
        web3, tx_hash, block_confirmations=6, block_number_poll_interval=poll_interval
    )

    wait_for_transaction_receipt_and_block_confirmations(
        web3, tx_hash, block_confirmations=27, block_number_poll_interval=poll_interval
    )

    dummy_tx_thread.stop()
    dummy_tx_thread.join()


def send_dummy_transactions(from_wallet, to_address):
    web3 = from_wallet.web3
    while not current_thread().stopped():
        tx = {
            "from": from_wallet.address,
            "to": to_address,
            "value": 1,
            "chainId": web3.eth.chain_id,
            "gasPrice": get_gas_price(web3),
        }
        tx["gas"] = web3.eth.estimate_gas(tx)
        raw_tx = from_wallet.sign_tx(tx)
        web3.eth.send_raw_transaction(raw_tx)


class StoppableThread(Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the current_thread().stopped() condition."""

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
