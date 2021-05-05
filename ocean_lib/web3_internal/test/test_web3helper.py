#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.web3_internal.web3helper import Web3Helper


def test_send_ether(alice_wallet, bob_address):
    assert Web3Helper.send_ether(
        alice_wallet, bob_address, 1
    ), "Cannot send ETH from Alice to Bob."


def test_cancel_or_replace_transaction(alice_wallet):
    assert Web3Helper.cancel_or_replace_transaction(alice_wallet, None)
