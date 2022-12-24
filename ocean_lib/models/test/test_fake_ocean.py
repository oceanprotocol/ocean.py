#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from brownie.network import accounts


from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.util import get_ocean_token_address, to_wei
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN


@pytest.mark.unit
def test_direct_call(config, consumer_wallet, factory_deployer_wallet, ocean_token):
    bal_before = ocean_token.balanceOf(consumer_wallet.address)
    amt_distribute = to_wei(1000)
    ocean_token.mint(
        consumer_wallet.address, amt_distribute, {"from": factory_deployer_wallet}
    )
    bal_after = ocean_token.balanceOf(consumer_wallet.address)
    assert bal_after == (bal_before + amt_distribute)


@pytest.mark.unit
def test_use_mint_fake_ocean(config, factory_deployer_wallet, ocean_token):
    expected_amt_distribute = to_wei(2000)

    mint_fake_OCEAN(config)

    for key_label in ["TEST_PRIVATE_KEY1", "TEST_PRIVATE_KEY2", "TEST_PRIVATE_KEY3"]:
        key = os.environ.get(key_label)
        if not key:
            continue

        w = accounts.add(key)
        assert ocean_token.balanceOf(w.address) >= expected_amt_distribute
