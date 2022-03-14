#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os

from ocean_lib.config import Config
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.ocean.util import get_web3
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.utils import get_ether_balance
from ocean_lib.web3_internal.wallet import Wallet


def mint_fake_OCEAN(config: Config) -> None:
    """
    Does the following:
    1. Mints tokens
    2. Distributes tokens to TEST_PRIVATE_KEY1 and TEST_PRIVATE_KEY2
    """
    addresses_file = config.address_file

    with open(addresses_file) as f:
        network_addresses = json.load(f)

    web3 = get_web3(config.network_url)
    deployer_wallet = Wallet(
        web3,
        private_key=os.environ.get("FACTORY_DEPLOYER_PRIVATE_KEY"),
        block_confirmations=config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )

    OCEAN_token = ERC20Token(web3, address=network_addresses["development"]["Ocean"])
    amt_distribute = to_wei("2000")

    for key_label in ["TEST_PRIVATE_KEY1", "TEST_PRIVATE_KEY2", "TEST_PRIVATE_KEY3"]:
        key = os.environ.get(key_label)
        if not key:
            continue

        w = Wallet(
            web3,
            private_key=key,
            block_confirmations=config.block_confirmations,
            transaction_timeout=config.transaction_timeout,
        )

        if OCEAN_token.balanceOf(w.address) < amt_distribute:
            OCEAN_token.transfer(w.address, amt_distribute, from_wallet=deployer_wallet)

        if get_ether_balance(web3, w.address) < to_wei("2"):
            send_ether(deployer_wallet, w.address, to_wei("4"))
