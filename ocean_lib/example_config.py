#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
from typing import Optional

from enforce_typing import enforce_types
from ocean_lib.config import Config, config_defaults
from ocean_lib.web3_internal.constants import NETWORK_NAME_MAP

logging.basicConfig(level=logging.INFO)

CONFIG_HELPER_NETWORKS = {
    "ganache": config_defaults,
    "ropsten": {
        "eth-network": list(config_defaults["eth-network"].items())
        + [
            ("network", "https://ropsten.infura.io/v3"),
            (
                "chain_id",
                list(NETWORK_NAME_MAP.keys())[
                    list(NETWORK_NAME_MAP.values()).index("Ropsten")
                ],
            ),
        ],
        "resources": list(config_defaults["resources"].items())
        + [
            ("metadata_cache_uri", "https://aquarius.oceanprotocol.com"),
            ("provider.url", "https://provider.ropsten.oceanprotocol.com"),
        ],
    },
    "rinkeby": {
        "eth-network": list(config_defaults["eth-network"].items())
        + [
            ("network", "https://rinkeby.infura.io/v3"),
            (
                "chain_id",
                list(NETWORK_NAME_MAP.keys())[
                    list(NETWORK_NAME_MAP.values()).index("Rinkeby")
                ],
            ),
        ],
        "resources": list(config_defaults["resources"].items())
        + [
            ("metadata_cache_uri", "https://aquarius.oceanprotocol.com"),
            ("provider.url", "https://provider.rinkeby.oceanprotocol.com"),
        ],
    },
    "mainnet": {
        "eth-network": list(config_defaults["eth-network"].items())
        + [
            ("network", "https://mainnet.infura.io/v3"),
            (
                "chain_id",
                list(NETWORK_NAME_MAP.keys())[
                    list(NETWORK_NAME_MAP.values()).index("Mainnet")
                ],
            ),
        ],
        "resources": list(config_defaults["resources"].items())
        + [
            ("metadata_cache_uri", "https://aquarius.oceanprotocol.com"),
            ("provider.url", "https://provider.mainnet.oceanprotocol.com"),
        ],
    },
    "polygon": {
        "eth-network": list(config_defaults["eth-network"].items())
        + [
            ("network", "https://polygon-mainnet.infura.io/v3"),
            (
                "chain_id",
                list(NETWORK_NAME_MAP.keys())[
                    list(NETWORK_NAME_MAP.values()).index("Polygon")
                ],
            ),
        ],
        "resources": list(config_defaults["resources"].items())
        + [
            ("metadata_cache_uri", "https://aquarius.oceanprotocol.com"),
            ("provider.url", "https://provider.polygon.oceanprotocol.com"),
        ],
    },
    "bsc": {
        "eth-network": list(config_defaults["eth-network"].items())
        + [
            ("network", "https://bsc-dataseed.binance.org"),
            (
                "chain_id",
                list(NETWORK_NAME_MAP.keys())[
                    list(NETWORK_NAME_MAP.values()).index("Binance Smart Chain")
                ],
            ),
        ],
        "resources": list(config_defaults["resources"].items())
        + [
            ("metadata_cache_uri", "https://aquarius.oceanprotocol.com"),
            ("provider.url", "https://provider.bsc.oceanprotocol.com"),
        ],
    },
}


@enforce_types
class ExampleConfig:
    @staticmethod
    def get_config(network_name: Optional[str] = None) -> Config:
        """
        :return: `Config` instance
        """
        config = CONFIG_HELPER_NETWORKS.get(
            network_name, CONFIG_HELPER_NETWORKS["ganache"]
        )
        return Config(options_dict=config)
