#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.transactions import (
    cancel_or_replace_transaction,
    send_ether,
)


def test_chain_id_send_ether(alice_wallet, bob_address):
    """Tests if the chainId has the right value for send ether transactions."""
    receipt = send_ether(alice_wallet, bob_address, to_wei(1))
    assert receipt, "Send ether was unsuccessful."
    tx = alice_wallet.web3.eth.get_transaction(receipt["transactionHash"])
    # Formula: v = CHAIN_ID * 2 + 35 or v = CHAIN_ID * 2 + 36
    chain_ids = [(tx["v"] - 35) / 2, (tx["v"] - 36) / 2]
    result = True if alice_wallet.web3.eth.chain_id in chain_ids else False
    assert result, "The chain ID is not the right one."


def test_chain_id_cancel_or_replace_transaction(alice_wallet, bob_address):
    """Tests if the chainId has the right value for cancelled tx."""
    receipt_cancelled = cancel_or_replace_transaction(alice_wallet, None)
    assert receipt_cancelled, "Cancel or replace transaction failed."
    tx_cancelled = alice_wallet.web3.eth.get_transaction(
        receipt_cancelled["transactionHash"]
    )
    chain_ids = [(tx_cancelled["v"] - 35) / 2, (tx_cancelled["v"] - 36) / 2]
    result_cancelled = True if alice_wallet.web3.eth.chain_id in chain_ids else False
    assert result_cancelled, "The chain ID is not the right one."


def test_send_ether(alice_wallet, bob_address):
    assert send_ether(
        alice_wallet, bob_address, to_wei(1)
    ), "Send ether was unsuccessful."


def test_cancel_or_replace_transaction(alice_wallet):
    assert cancel_or_replace_transaction(
        alice_wallet, None
    ), "Cancel or replace transaction failed."
