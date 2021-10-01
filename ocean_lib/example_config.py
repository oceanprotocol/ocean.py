#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import copy
import logging
import os

from enforce_typing import enforce_types
from ocean_lib.config import (
    DEFAULT_METADATA_CACHE_URI,
    DEFAULT_PROVIDER_URL,
    NAME_BLOCK_CONFIRMATIONS,
    NAME_CHAIN_ID,
    NAME_METADATA_CACHE_URI,
    NAME_NETWORK_URL,
    NAME_PROVIDER_URL,
    NETWORK_NAME,
    SECTION_ETH_NETWORK,
    SECTION_RESOURCES,
    Config,
    config_defaults,
)
from ocean_lib.ocean.util import get_web3

logging.basicConfig(level=logging.INFO)

CONFIG_NETWORK_HELPER = {
    1: {
        NAME_PROVIDER_URL: "https://provider.mainnet.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "mainnet",
        NAME_BLOCK_CONFIRMATIONS: 1,
    },
    3: {
        NAME_PROVIDER_URL: "https://provider.ropsten.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "ropsten",
        NAME_BLOCK_CONFIRMATIONS: 1,
    },
    4: {
        NAME_PROVIDER_URL: "https://provider.rinkeby.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "rinkeby",
        NAME_BLOCK_CONFIRMATIONS: 1,
    },
    56: {
        NAME_PROVIDER_URL: "https://provider.bsc.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "bsc",
        NAME_BLOCK_CONFIRMATIONS: 1,
    },
    137: {
        NAME_PROVIDER_URL: "https://provider.polygon.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "polygon",
        NAME_BLOCK_CONFIRMATIONS: 15,
    },
    246: {
        NAME_PROVIDER_URL: "https://provider.energyweb.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "energyweb",
        NAME_BLOCK_CONFIRMATIONS: 3,
    },
    1285: {
        NAME_PROVIDER_URL: "https://provider.moonriver.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "moonriver",
        NAME_BLOCK_CONFIRMATIONS: 3,
    },
    1287: {
        NAME_PROVIDER_URL: "https://provider.moonbeamalpha.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "moonbeamalpha",
        NAME_BLOCK_CONFIRMATIONS: 3,
    },
    1337: {
        NAME_PROVIDER_URL: DEFAULT_PROVIDER_URL,
        NAME_METADATA_CACHE_URI: DEFAULT_METADATA_CACHE_URI,
        NETWORK_NAME: "ganache",
        NAME_BLOCK_CONFIRMATIONS: 0,
    },
    44787: {
        NAME_PROVIDER_URL: "https://provider.celoalfajores.oceanprotocol.com",
        NAME_METADATA_CACHE_URI: "https://aquarius.oceanprotocol.com",
        NETWORK_NAME: "celoalfajores",
        NAME_BLOCK_CONFIRMATIONS: 3,
    },
}


@enforce_types
def get_config_dict(chain_id: int) -> dict:
    if chain_id not in CONFIG_NETWORK_HELPER:
        raise ValueError("The chain id for the specific RPC could not be fetched!")

    config_helper = copy.deepcopy(config_defaults)
    config_helper[SECTION_ETH_NETWORK].update(
        {
            NAME_CHAIN_ID: chain_id,
            NETWORK_NAME: CONFIG_NETWORK_HELPER[chain_id][NETWORK_NAME],
            NAME_BLOCK_CONFIRMATIONS: CONFIG_NETWORK_HELPER[chain_id][
                NAME_BLOCK_CONFIRMATIONS
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


class ExampleConfig:
    @staticmethod
    @enforce_types
    def get_config() -> Config:
        """Return `Config` containing default values for a given network.
        Chain ID is determined by querying the RPC specified by `OCEAN_NETWORK_URL` envvar.
        """

        network_url = os.getenv("OCEAN_NETWORK_URL")
        assert (
            network_url is not None
        ), "Cannot use ocean-lib without a specified network URL."

        w3 = get_web3(network_url)
        chain_id = w3.eth.chain_id

        config = get_config_dict(chain_id)
        config[SECTION_ETH_NETWORK][NAME_NETWORK_URL] = network_url
        return Config(options_dict=config)
