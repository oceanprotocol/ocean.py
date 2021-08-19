#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os
import copy

from web3 import Web3

from ocean_lib.config import (
    Config,
    config_defaults,
    SECTION_ETH_NETWORK,
    NAME_CHAIN_ID,
    SECTION_RESOURCES,
    NAME_NETWORK_URL,
    NAME_PROVIDER_URL,
    NAME_METADATA_CACHE_URI,
    DEFAULT_METADATA_CACHE_URI,
    DEFAULT_PROVIDER_URL,
)
from ocean_lib.ocean.util import get_web3_connection_provider

from enforce_typing import enforce_types

logging.basicConfig(level=logging.INFO)

NETWORK_NAME = "network_name"
"""The interval in seconds between calls for the latest block number."""
NAME_BLOCK_CONFIRMATION_POLL_INTERVAL = "block_confirmation_poll_interval"


CONFIG_NETWORK_HELPER = {
    1: {
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL: 6.5,
        NAME_PROVIDER_URL: "https://provider.mainnet.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "mainnet",
    },
    3: {
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL: 6,
        NAME_PROVIDER_URL: "https://provider.ropsten.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "ropsten",
    },
    4: {
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL: 7.5,
        NAME_PROVIDER_URL: "https://provider.rinkeby.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "rinkeby",
    },
    56: {
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL: 1.5,
        NAME_PROVIDER_URL: "https://provider.bsc.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "bsc",
    },
    137: {
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL: 1,
        NAME_PROVIDER_URL: "https://provider.polygon.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "polygon",
    },
    1287: {
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL: 6,
        NAME_PROVIDER_URL: "https://provider.moonbeamalpha.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "moonbeamalpha",
    },
    1337: {
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL: 2.5,
        NAME_PROVIDER_URL: DEFAULT_PROVIDER_URL,
        NAME_METADATA_CACHE_URI: DEFAULT_METADATA_CACHE_URI,
        NETWORK_NAME: "ganache",
    },
}


def get_config_dict(chain_id: int) -> dict:
    if chain_id not in CONFIG_NETWORK_HELPER:
        raise ValueError("The chain id for the specific RPC could not be fetched!")

    config_helper = copy.deepcopy(config_defaults)
    config_helper[SECTION_ETH_NETWORK].update(
        {
            NAME_CHAIN_ID: chain_id,
            NETWORK_NAME: CONFIG_NETWORK_HELPER[chain_id][NETWORK_NAME],
            NAME_BLOCK_CONFIRMATION_POLL_INTERVAL: CONFIG_NETWORK_HELPER[chain_id][
                NAME_BLOCK_CONFIRMATION_POLL_INTERVAL
            ],
        }
    )
    config_helper[SECTION_RESOURCES].update(
        {
            NAME_PROVIDER_URL: CONFIG_NETWORK_HELPER[chain_id][NAME_PROVIDER_URL],
            NAME_METADATA_CACHE_URI: CONFIG_NETWORK_HELPER[chain_id][
                NAME_METADATA_CACHE_URI
            ],
        }
    )
    return config_helper


@enforce_types
class ExampleConfig:
    @staticmethod
    def get_config() -> Config:
        """Return `Config` containing default values for a given network.
        Chain ID is determined by querying the RPC specified by `NETWORK_URL` envvar.
        """

        network_url = os.getenv("NETWORK_URL")
        assert (
            network_url is not None
        ), "Cannot use ocean-lib without a specified network URL."

        w3 = Web3(get_web3_connection_provider(network_url))
        chain_id = w3.eth.chain_id

        config = get_config_dict(chain_id)
        config[SECTION_ETH_NETWORK][NAME_NETWORK_URL] = network_url
        return Config(options_dict=config)
