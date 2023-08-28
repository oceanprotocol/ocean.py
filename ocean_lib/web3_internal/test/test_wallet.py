#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest

from ocean_lib.ocean.util import to_wei
from tests.resources.helper_functions import generate_wallet


@pytest.mark.unit
def test_generating_wallets(ocean_token, config):
    generated_wallet = generate_wallet()
    assert generated_wallet.address, "Wallet has not an address."

    assert config["web3_instance"].eth.get_balance(generated_wallet.address) == to_wei(
        3
    )

    assert ocean_token.balanceOf(generated_wallet.address) == to_wei(50)

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
    assert generated_wallet._private_key.hex() not in env_private_keys
