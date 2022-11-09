#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from brownie.network import accounts
from web3.main import Web3

from tests.resources.helper_functions import generate_wallet


@pytest.mark.unit
def test_generating_wallets(publisher_ocean_instance):
    generated_wallet = generate_wallet()
    assert generated_wallet.address, "Wallet has not an address."
    assert accounts.at(generated_wallet.address).balance() == Web3.toWei(3, "ether")

    OCEAN_token = publisher_ocean_instance.OCEAN_token
    assert OCEAN_token.balanceOf(generated_wallet.address) == Web3.toWei(50, "ether")

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
