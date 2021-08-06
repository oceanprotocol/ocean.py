#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os
import copy

from enforce_typing import enforce_types
from web3 import Web3

from ocean_lib.config import (
    Config,
    SECTION_ETH_NETWORK,
    NAME_CHAIN_ID,
    SECTION_RESOURCES,
    NAME_NETWORK_URL,
    NAME_PROVIDER_URL,
    config_defaults,
)
from ocean_lib.ocean.util import get_web3_connection_provider

logging.basicConfig(level=logging.INFO)
NETWORK_NAME = "network_name"

CONFIG_NETWORK_HELPER = {
    1: {
        NAME_PROVIDER_URL: "https://provider.mainnet.oceanprotocol.com",
        NETWORK_NAME: "mainnet",
    },
    3: {
        NAME_PROVIDER_URL: "https://provider.ropsten.oceanprotocol.com",
        NETWORK_NAME: "ropsten",
    },
    4: {
        NAME_PROVIDER_URL: "https://provider.rinkeby.oceanprotocol.com",
        NETWORK_NAME: "rinkeby",
    },
    56: {
        NAME_PROVIDER_URL: "https://provider.bsc.oceanprotocol.com",
        NETWORK_NAME: "bsc",
    },
    137: {
        NAME_PROVIDER_URL: "https://provider.polygon.oceanprotocol.com",
        NETWORK_NAME: "polygon",
    },
    1337: {NAME_PROVIDER_URL: "http://localhost:8030", NETWORK_NAME: "ganache"},
}


def get_config_helper_network(network_url: str) -> dict:
    w3 = Web3(get_web3_connection_provider(network_url))
    chain_id = w3.eth.chain_id
    if chain_id not in CONFIG_NETWORK_HELPER:
        raise ValueError("The chain id for the specific RPC could not be fetched!")
    config_helper = copy.deepcopy(config_defaults)
    config_helper[SECTION_ETH_NETWORK].update(
        {
            NAME_NETWORK_URL: network_url,
            NAME_CHAIN_ID: chain_id,
            NETWORK_NAME: CONFIG_NETWORK_HELPER[chain_id][NETWORK_NAME],
        }
    ),
    config_helper[SECTION_RESOURCES].update(
        {NAME_PROVIDER_URL: CONFIG_NETWORK_HELPER[chain_id][NAME_PROVIDER_URL]}
    )
    return config_helper


@enforce_types
class ExampleConfig:
    @staticmethod
    def get_config() -> Config:
        """Return `Config` containing default values for a given network.
        Chain ID is determined by querying the RPC specified by `OCEAN_NETWORK_URL` envvar.
        """
        network_url = os.getenv("OCEAN_NETWORK_URL")
        assert (
            network_url is not None
        ), "Cannot use ocean-lib without a specified network URL."
        w3 = Web3(get_web3_connection_provider(network_url))
        chain_id = w3.eth.chain_id
        if chain_id not in CONFIG_NETWORK_HELPER:
            raise ValueError("The chain id for the specific RPC could not be fetched!")
        else:
            config = get_config_helper_network(network_url)
            return Config(options_dict=config)
