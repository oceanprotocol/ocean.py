#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os

from enforce_typing import enforce_types
from web3 import Web3

from ocean_lib.config import Config, config_defaults
from ocean_lib.web3_internal.constants import NETWORK_NAME_MAP

logging.basicConfig(level=logging.INFO)

network_rpc = os.getenv("NETWORK_URL")

CONFIG_HELPER_NETWORKS = {
    1337: config_defaults,
    3: {
        "eth-network": dict(
            list(config_defaults["eth-network"].items())
            + [
                ("network", network_rpc),
                (
                    "chain_id",
                    list(NETWORK_NAME_MAP.keys())[
                        list(NETWORK_NAME_MAP.values()).index("Ropsten")
                    ],
                ),
            ]
        ),
        "resources": dict(
            list(config_defaults["resources"].items())
            + [
                ("metadata_cache_uri", "https://aquarius.oceanprotocol.com"),
                ("provider.url", "https://provider.ropsten.oceanprotocol.com"),
            ]
        ),
    },
    4: {
        "eth-network": dict(
            list(config_defaults["eth-network"].items())
            + [
                ("network", network_rpc),
                (
                    "chain_id",
                    list(NETWORK_NAME_MAP.keys())[
                        list(NETWORK_NAME_MAP.values()).index("Rinkeby")
                    ],
                ),
            ]
        ),
        "resources": dict(
            list(config_defaults["resources"].items())
            + [
                ("metadata_cache_uri", "https://aquarius.oceanprotocol.com"),
                ("provider.url", "https://provider.rinkeby.oceanprotocol.com"),
            ]
        ),
    },
    1: {
        "eth-network": dict(
            list(config_defaults["eth-network"].items())
            + [
                ("network", network_rpc),
                (
                    "chain_id",
                    list(NETWORK_NAME_MAP.keys())[
                        list(NETWORK_NAME_MAP.values()).index("Mainnet")
                    ],
                ),
            ]
        ),
        "resources": dict(
            list(config_defaults["resources"].items())
            + [
                ("metadata_cache_uri", "https://aquarius.oceanprotocol.com"),
                ("provider.url", "https://provider.mainnet.oceanprotocol.com"),
            ]
        ),
    },
    137: {
        "eth-network": dict(
            list(config_defaults["eth-network"].items())
            + [
                ("network", network_rpc),
                (
                    "chain_id",
                    list(NETWORK_NAME_MAP.keys())[
                        list(NETWORK_NAME_MAP.values()).index("Polygon")
                    ],
                ),
            ]
        ),
        "resources": dict(
            list(config_defaults["resources"].items())
            + [
                ("metadata_cache_uri", "https://aquarius.oceanprotocol.com"),
                ("provider.url", "https://provider.polygon.oceanprotocol.com"),
            ]
        ),
    },
    56: {
        "eth-network": dict(
            list(config_defaults["eth-network"].items())
            + [
                ("network", network_rpc),
                (
                    "chain_id",
                    list(NETWORK_NAME_MAP.keys())[
                        list(NETWORK_NAME_MAP.values()).index("Binance Smart Chain")
                    ],
                ),
            ]
        ),
        "resources": dict(
            list(config_defaults["resources"].items())
            + [
                ("metadata_cache_uri", "https://aquarius.oceanprotocol.com"),
                ("provider.url", "https://provider.bsc.oceanprotocol.com"),
            ]
        ),
    },
}


@enforce_types
class ExampleConfig:
    @staticmethod
    def get_config() -> Config:
        """
        :return: `Config` instance
        """
        w3 = Web3(Web3.HTTPProvider(network_rpc))
        chain_id = w3.eth.chain_id
        assert w3.isConnected()
        if chain_id not in CONFIG_HELPER_NETWORKS:
            raise ValueError("The chain id for the specific RPC could not be fetched!")
        else:
            config = CONFIG_HELPER_NETWORKS[chain_id]
            return Config(options_dict=config)
