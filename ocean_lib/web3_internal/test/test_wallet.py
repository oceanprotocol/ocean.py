#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from ocean_lib.web3_internal.utils import add_ethereum_prefix_and_hash_msg
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider


def test_wallet_arguments():
    """Tests that a wallet's arguments are correctly setup."""
    web3 = Web3Provider.get_web3()

    private_key = os.environ.get("TEST_PRIVATE_KEY1")
    assert private_key, "envvar TEST_PRIVATE_KEY1 is not set."

    # Create wallet with valid private key
    wallet = Wallet(web3, private_key=private_key)
    assert wallet.private_key == private_key
    assert wallet.address
    signed_message = wallet.sign(add_ethereum_prefix_and_hash_msg("msg-to-sign"))
    assert signed_message

    # Create wallet with encrypted key and password
    password = "darksecret"
    encrypted_key = web3.eth.account.encrypt(private_key, password)
    w2 = Wallet(web3, encrypted_key=encrypted_key, password=password)
    assert w2.address == wallet.address
    assert w2.private_key == wallet.private_key
    assert w2.sign(add_ethereum_prefix_and_hash_msg("msg-to-sign")) == signed_message

    # create wallet with missing arguments
    with pytest.raises(AssertionError):
        Wallet(web3)
    with pytest.raises(AssertionError):
        Wallet(web3, encrypted_key=encrypted_key)
    with pytest.raises(AssertionError):
        Wallet(web3, password=password)

    # Create wallet with invalid private_key
    invalid_key = "332233444332"
    with pytest.raises(ValueError):
        Wallet(web3, private_key=invalid_key)

    with pytest.raises(AssertionError):
        Wallet(web3, private_key=None)
