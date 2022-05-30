#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from eth_account.messages import encode_defunct

from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.utils import get_ether_balance
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import generate_wallet


@pytest.mark.unit
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


@pytest.mark.unit
def test_generating_wallets(web3, publisher_ocean_instance):
    generated_wallet = generate_wallet()
    assert generated_wallet.address, "Wallet has not an address."
    assert get_ether_balance(web3, generated_wallet.address) == to_wei(3)

    OCEAN_token = publisher_ocean_instance.OCEAN_token
    assert OCEAN_token.balanceOf(generated_wallet.address) == to_wei(50)

    env_key_labels = [
        "TEST_PRIVATE_KEY1",
        "TEST_PRIVATE_KEY2",
        "TEST_PRIVATE_KEY3",
        "TEST_PRIVATE_KEY4",
        "TEST_PRIVATE_KEY5",
        "TEST_PRIVATE_KEY6",
        "TEST_PRIVATE_KEY7",
        "TEST_PRIVATE_KEY8",
        "FACTORY_DEPLOYER_PRIVATE_KEY",
        "PROVIDER_PRIVATE_KEY",
    ]
    env_private_keys = []
    for key_label in env_key_labels:
        key = os.environ.get(key_label)
        env_private_keys.append(key)
    assert generated_wallet.private_key not in env_private_keys
