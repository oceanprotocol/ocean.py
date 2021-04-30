#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os

from ocean_lib.config_provider import ConfigProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.data_token import DataToken
from ocean_lib.ocean.util import get_web3_connection_provider, to_base_18
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.utils import from_wei, get_ether_balance
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider
from tests.resources.helper_functions import (
    get_ganache_wallet,
    get_publisher_ocean_instance,
)


def mint_fake_OCEAN():
    """
    Does the following:
    1. Mints tokens
    2. Distributes tokens to TEST_PRIVATE_KEY1 and TEST_PRIVATE_KEY2
    """
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    Web3Provider.init_web3(provider=get_web3_connection_provider(config.network_url))
    ContractHandler.set_artifacts_path(config.artifacts_path)

    addresses_file = config.address_file

    ocean = get_publisher_ocean_instance()
    web3 = ocean.web3

    with open(addresses_file) as f:
        network_addresses = json.load(f)

    network = "development"
    deployer_wallet = get_ganache_wallet()

    OCEAN_token = DataToken(address=network_addresses[network]["Ocean"])

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

        if from_wei(get_ether_balance(w.address)) < 2:
            send_ether(deployer_wallet, w.address, 4)
