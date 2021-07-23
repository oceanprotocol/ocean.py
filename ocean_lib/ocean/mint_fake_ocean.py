#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os

from ocean_lib.config import Config
from ocean_lib.models.data_token import DataToken
from ocean_lib.ocean.util import get_web3_connection_provider, to_base_18
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.utils import from_wei, get_ether_balance
from ocean_lib.web3_internal.wallet import Wallet
from web3.main import Web3


def mint_fake_OCEAN(config: Config) -> None:
    """
    Does the following:
    1. Mints tokens
    2. Distributes tokens to TEST_PRIVATE_KEY1 and TEST_PRIVATE_KEY2
    """
    addresses_file = config.address_file

    with open(addresses_file) as f:
        network_addresses = json.load(f)

    web3 = Web3(provider=get_web3_connection_provider(config.network_url))
    deployer_wallet = Wallet(
        web3, private_key=os.environ.get("FACTORY_DEPLOYER_PRIVATE_KEY")
    )

    OCEAN_token = DataToken(web3, address=network_addresses["development"]["Ocean"])

    amt_distribute = 1000
    amt_distribute_base = to_base_18(float(amt_distribute))

    OCEAN_token.mint(
        deployer_wallet.address, 2 * amt_distribute_base, from_wallet=deployer_wallet
    )

    for key_label in ["TEST_PRIVATE_KEY1", "TEST_PRIVATE_KEY2"]:
        key = os.environ.get(key_label)
        if not key:
            continue

        w = Wallet(web3, private_key=key)

        if OCEAN_token.token_balance(w.address) < 1000:
            OCEAN_token.transfer(
                w.address, amt_distribute_base, from_wallet=deployer_wallet
            )

        if from_wei(get_ether_balance(web3, w.address)) < 2:
            send_ether(deployer_wallet, w.address, 4)
