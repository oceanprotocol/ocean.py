#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import sys

from ocean_lib.config_provider import ConfigProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.data_token import DataToken
from ocean_lib.ocean.util import get_web3_connection_provider, to_base_18
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.utils import privateKeyToAddress
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_lib.web3_internal.web3helper import Web3Helper
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

    # ****DEPLOY****
    deployer_wallet = Wallet(web3, private_key=deployer_private_key)

    # For simplicity, hijack DataTokenTemplate.
    deployer_addr = deployer_wallet.address
    OCEAN_token = DataToken(address=network_addresses[network]["Ocean"])
    amt_distribute = 1000
    amt_distribute_base = to_base_18(float(amt_distribute))

    OCEAN_token.mint(
        deployer_addr, 2 * amt_distribute_base, from_wallet=deployer_wallet
    )

    for key_label in ["TEST_PRIVATE_KEY1", "TEST_PRIVATE_KEY2"]:
        key = os.environ.get(key_label)
        w = Wallet(web3, private_key=key)
        if not key:
            continue

        dst_address = privateKeyToAddress(key)
        OCEAN_token.transfer(
            dst_address, amt_distribute_base, from_wallet=deployer_wallet
        )

        if Web3Helper.from_wei(Web3Helper.get_ether_balance(w.address)) < 2:
            Web3Helper.send_ether(deployer_wallet, w.address, 4)


def invalidKey(private_key_str):  # super basic check
    return len(private_key_str) < 10
