#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from eth_account.messages import encode_defunct
from ocean_lib.web3_internal.wallet import Wallet


def test_wallet_arguments(web3, config):
    """Tests that a wallet's arguments are correctly setup."""
    private_key = os.environ.get("TEST_PRIVATE_KEY1")
    assert private_key, "envvar TEST_PRIVATE_KEY1 is not set."

    # Create wallet with valid private key
    wallet = Wallet(
        web3,
        private_key=private_key,
        block_confirmations=config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )
    assert wallet.private_key == private_key, "Private keys are different."
    assert wallet.address, "The wallet does not have a wallet address."
    signed_message = wallet.sign(encode_defunct(text="msg-to-sign"))
    assert signed_message, "Signed message is None."

    # create wallet with missing arguments
    with pytest.raises(TypeError):
        Wallet(web3)

    # Create wallet with invalid private_key
    invalid_key = "332233444332"
    with pytest.raises(ValueError):
        Wallet(
            web3,
            private_key=invalid_key,
            block_confirmations=config.block_confirmations,
            transaction_timeout=config.transaction_timeout,
        )

    with pytest.raises(TypeError):
        Wallet(
            web3,
            private_key=None,
            block_confirmations=config.block_confirmations,
            transaction_timeout=config.transaction_timeout,
        )
