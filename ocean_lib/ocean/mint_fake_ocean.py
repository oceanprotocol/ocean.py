#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from enforce_typing import enforce_types
from eth_account import Account

from ocean_lib.models.datatoken_base import DatatokenBase
from ocean_lib.ocean.util import get_ocean_token_address, send_ether, to_wei


@enforce_types
def mint_fake_OCEAN(config: dict) -> None:
    """
    Does the following:
    1. Mints tokens
    2. Distributes tokens to TEST_PRIVATE_KEY1 and TEST_PRIVATE_KEY2
    """
    deployer_wallet = Account.from_key(
        private_key=os.getenv("FACTORY_DEPLOYER_PRIVATE_KEY")
    )

    OCEAN_token = DatatokenBase.get_typed(
        config, address=get_ocean_token_address(config)
    )
    amt_distribute = to_wei(2000)
    OCEAN_token.mint(deployer_wallet.address, to_wei(20000), {"from": deployer_wallet})
    for key_label in ["TEST_PRIVATE_KEY1", "TEST_PRIVATE_KEY2", "TEST_PRIVATE_KEY3"]:
        key = os.environ.get(key_label)
        if not key:
            continue

        w = Account.from_key(private_key=key)

        if OCEAN_token.balanceOf(w.address) < amt_distribute:
            OCEAN_token.mint(w.address, amt_distribute, {"from": deployer_wallet})

        if config["web3_instance"].eth.get_balance(w.address) < to_wei(2):
            send_ether(config, deployer_wallet, w.address, to_wei(4))
