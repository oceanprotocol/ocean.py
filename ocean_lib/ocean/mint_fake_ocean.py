#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from brownie.network import accounts

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.util import get_ocean_token_address
from ocean_lib.web3_internal.currency import to_wei


def mint_fake_OCEAN(config: dict) -> None:
    """
    Does the following:
    1. Mints tokens
    2. Distributes tokens to TEST_PRIVATE_KEY1 and TEST_PRIVATE_KEY2
    """
    deployer_wallet = accounts.add(os.environ.get("FACTORY_DEPLOYER_PRIVATE_KEY"))

    OCEAN_token = Datatoken(config, address=get_ocean_token_address(config))
    amt_distribute = to_wei("2000")
    OCEAN_token.mint(
        deployer_wallet.address, to_wei("20000"), {"from": deployer_wallet}
    )
    for key_label in ["TEST_PRIVATE_KEY1", "TEST_PRIVATE_KEY2", "TEST_PRIVATE_KEY3"]:
        key = os.environ.get(key_label)
        if not key:
            continue

        w = accounts.add(key)

        if OCEAN_token.balanceOf(w.address) < amt_distribute:
            OCEAN_token.mint(w.address, amt_distribute, {"from": deployer_wallet})

        if accounts.at(w.address).balance() < to_wei("2"):
            deployer_wallet.transfer(w.address, "4 ether")
