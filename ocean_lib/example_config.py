#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os

from enforce_typing import enforce_types
from web3 import Web3

from ocean_lib.config import (
    Config,
    config_defaults,
    SECTION_ETH_NETWORK,
    NAME_CHAIN_ID,
    SECTION_RESOURCES,
    NAME_NETWORK_URL,
    NAME_PROVIDER_URL,
)
from ocean_lib.ocean.util import get_web3_connection_provider

logging.basicConfig(level=logging.INFO)

PROVIDER_URLS = {
    1: "https://provider.mainnet.oceanprotocol.com",
    3: "https://provider.ropsten.oceanprotocol.com",
    4: "https://provider.rinkeby.oceanprotocol.com",
    56: "https://provider.bsc.oceanprotocol.com",
    137: "https://provider.polygon.oceanprotocol.com",
    1337: "http://localhost:8030",
}


def get_config_helper_networks(network_url: str) -> dict:
    w3 = Web3(get_web3_connection_provider(network_url))
    chain_id = w3.eth.chain_id
    if chain_id not in PROVIDER_URLS:
        raise ValueError("The chain id for the specific RPC could not be fetched!")
    config_helper = {
        SECTION_ETH_NETWORK: dict(
            list(config_defaults[SECTION_ETH_NETWORK].items())
            + [(NAME_NETWORK_URL, network_url), (NAME_CHAIN_ID, chain_id)]
        ),
        SECTION_RESOURCES: dict(
            list(config_defaults[SECTION_RESOURCES].items())
            + [
                (NAME_PROVIDER_URL, PROVIDER_URLS[chain_id]),
            ]
        ),
    }
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
        if chain_id not in PROVIDER_URLS:
            raise ValueError("The chain id for the specific RPC could not be fetched!")
        else:
            config = get_config_helper_networks(network_url)
            return Config(options_dict=config)
