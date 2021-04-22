#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""
    Used for minting and sending fake OCEAN
    isort:skip_file
"""

import json
import os
import sys

from ocean_lib.config_provider import ConfigProvider

# Setup ocean_lib.enforce_typing_shim before importing anything that uses it
from ocean_lib.enforce_typing_shim import setup_enforce_typing_shim

setup_enforce_typing_shim()

from ocean_lib.example_config import ExampleConfig  # noqa: E402
from ocean_lib.models.data_token import DataToken  # noqa: E402
from ocean_lib.ocean import util  # noqa: E402
from ocean_lib.ocean.util import get_web3_connection_provider  # noqa: E402
from ocean_lib.web3_internal.contract_handler import ContractHandler  # noqa: E402
from ocean_lib.web3_internal.utils import privateKeyToAddress  # noqa: E402
from ocean_lib.web3_internal.wallet import Wallet  # noqa: E402
from ocean_lib.web3_internal.web3_provider import Web3Provider  # noqa: E402
from tests.resources.helper_functions import (  # noqa: E402
    get_ganache_wallet,
    get_publisher_ocean_instance,
)


def mint_fake_OCEAN():
    """
    Does the following:
    1. Mints tokens
    2. Distributes tokens to TEST_PRIVATE_KEY1 and TEST_PRIVATE_KEY2
    """
    network = "ganache"
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    Web3Provider.init_web3(provider=get_web3_connection_provider(config.network_url))
    ContractHandler.set_artifacts_path(config.artifacts_path)

    addresses_file = config.address_file

    ocean = get_publisher_ocean_instance()
    web3 = ocean.web3

    if os.path.exists(addresses_file):
        with open(addresses_file) as f:
            network_addresses = json.load(f)
    else:
        network_addresses = {network: {}}

    if network not in network_addresses:
        network = "development"

    # ****SET ENVT****
    deployer_private_key = get_ganache_wallet().private_key

    if invalidKey(deployer_private_key):
        print("Need valid DEPLOYER_PRIVATE_KEY")
        sys.exit(0)

    deployer_wallet = Wallet(web3, private_key=deployer_private_key)
    OCEAN_cap = 10000
    OCEAN_cap_base = util.to_base_18(float(OCEAN_cap))
    OCEAN_token = DataToken(address=network_addresses["development"]["Ocean"])

    print("****Mint fake OCEAN: begin****")
    OCEAN_token.mint(
        deployer_wallet.address, OCEAN_cap_base, from_wallet=deployer_wallet
    )
    print("****Mint fake OCEAN: done****\n")

    print("****Distribute fake OCEAN: begin****")
    amt_distribute = 1000
    amt_distribute_base = util.to_base_18(float(amt_distribute))
    for key_label in ["TEST_PRIVATE_KEY1", "TEST_PRIVATE_KEY2"]:
        key = os.environ.get(key_label)
        if not key:
            continue

        dst_address = privateKeyToAddress(key)
        OCEAN_token.transfer(
            dst_address, amt_distribute_base, from_wallet=deployer_wallet
        )
        print(f"Distributed {amt_distribute} OCEAN to address {dst_address}")

    print("****Distribute fake OCEAN: done****\n")


def invalidKey(private_key_str):  # super basic check
    return len(private_key_str) < 10


def invalidAddr(addr_str):  # super basic check
    return len(addr_str) < 10
