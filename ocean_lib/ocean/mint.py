#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""
    Used for minting fake OCEAN
    isort:skip_file
"""

import json
import os

from ocean_lib.config_provider import ConfigProvider

# Setup ocean_lib.enforce_typing_shim before importing anything that uses it
from ocean_lib.enforce_typing_shim import setup_enforce_typing_shim

setup_enforce_typing_shim()

from ocean_lib.example_config import ExampleConfig  # noqa: E402
from ocean_lib.models.data_token import DataToken  # noqa: E402
from ocean_lib.ocean.util import to_base_18  # noqa: E402
from tests.resources.helper_functions import (
    get_ganache_wallet,
    get_publisher_wallet,
    get_consumer_wallet,
)  # noqa: E402


def mint_OCEAN():
    """
    Mints OCEAN tokens
    """
    network = "ganache"
    config = ExampleConfig.get_config()
    wallet = get_ganache_wallet()
    ConfigProvider.set_config(config)

    addresses_file = config.address_file

    if os.path.exists(addresses_file):
        with open(addresses_file) as f:
            network_addresses = json.load(f)
    else:
        network_addresses = {network: {}}

    if network not in network_addresses:
        network = "development"

    amt_distribute = 1000
    amt_distribute_base = to_base_18(float(amt_distribute))

    OCEAN_token = DataToken(address=network_addresses[network]["Ocean"])

    for w in (get_publisher_wallet(), get_consumer_wallet()):
        # if Web3Helper.from_wei(Web3Helper.get_ether_balance(w.address)) < 2:
        #    Web3Helper.send_ether(wallet, w.address, 4)

        OCEAN_token.mint(wallet.address, amt_distribute_base, from_wallet=wallet)
        OCEAN_token.transfer(w.address, amt_distribute_base, from_wallet=wallet)
