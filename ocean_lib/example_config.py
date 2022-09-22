#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import copy
import logging

from enforce_typing import enforce_types

from ocean_lib.ocean.util import get_web3
from ocean_lib.web3_internal.constants import GAS_LIMIT_DEFAULT

logging.basicConfig(level=logging.INFO)

DEFAULT_METADATA_CACHE_URI = "http://172.15.0.5:5000"
METADATA_CACHE_URI = "https://v4.aquarius.oceanprotocol.com"
DEFAULT_PROVIDER_URL = "http://172.15.0.4:8030"

config_defaults = {
    "OCEAN_NETWORK_URL": "http://127.0.0.1:8545",
    "NETWORK_NAME": "ganache",
    "CHAIN_ID": 8996,
    "GAS_LIMIT": GAS_LIMIT_DEFAULT,
    "BLOCK_CONFIRMATIONS": 0,
    "TRANSACTION_TIMEOUT": 10 * 60,  # 10 minutes
    "METADATA_CACHE_URI": "http://172.15.0.5:5000",
    "PROVIDER_URL": "http://172.15.0.4:8030",
    "DOWNLOADS_PATH": "consume-downloads",
    "ADDRESS_FILE": "~/.ocean/ocean-contracts/artifacts/address.json",
}

CONFIG_NETWORK_HELPER = {
    1: {
        "PROVIDER_URL": "https://v4.provider.mainnet.oceanprotocol.com",
        "NETWORK_NAME": "mainnet",
        "BLOCK_CONFIRMATIONS": 1,
    },
    3: {
        "PROVIDER_URL": "https://v4.provider.ropsten.oceanprotocol.com",
        "NETWORK_NAME": "ropsten",
        "BLOCK_CONFIRMATIONS": 1,
    },
    4: {
        "PROVIDER_URL": "https://v4.provider.rinkeby.oceanprotocol.com",
        "NETWORK_NAME": "rinkeby",
        "BLOCK_CONFIRMATIONS": 1,
    },
    56: {
        "PROVIDER_URL": "https://v4.provider.bsc.oceanprotocol.com",
        "NETWORK_NAME": "bsc",
        "BLOCK_CONFIRMATIONS": 1,
    },
    137: {
        "PROVIDER_URL": "https://v4.provider.polygon.oceanprotocol.com",
        "NETWORK_NAME": "polygon",
        "BLOCK_CONFIRMATIONS": 15,
    },
    246: {
        "PROVIDER_URL": "https://v4.provider.energyweb.oceanprotocol.com",
        "NETWORK_NAME": "energyweb",
        "BLOCK_CONFIRMATIONS": 3,
        "TRANSACTION_TIMEOUT": 60,
    },
    1285: {
        "PROVIDER_URL": "https://v4.provider.moonriver.oceanprotocol.com",
        "NETWORK_NAME": "moonriver",
        "BLOCK_CONFIRMATIONS": 3,
        "TRANSACTION_TIMEOUT": 60,
    },
    1287: {
        "PROVIDER_URL": "https://v4.provider.moonbase.oceanprotocol.com",
        "NETWORK_NAME": "moonbeamalpha",
        "BLOCK_CONFIRMATIONS": 3,
        "TRANSACTION_TIMEOUT": 60,
    },
    8996: {
        "PROVIDER_URL": DEFAULT_PROVIDER_URL,
        "NETWORK_NAME": "ganache",
        "BLOCK_CONFIRMATIONS": 0,
        "TRANSACTION_TIMEOUT": 2,
    },
    44787: {
        "PROVIDER_URL": "https://provider.celoalfajores.oceanprotocol.com",
        "NETWORK_NAME": "celoalfajores",
        "BLOCK_CONFIRMATIONS": 3,
        "TRANSACTION_TIMEOUT": 60,
    },
    80001: {
        "PROVIDER_URL": "https://v4.provider.mumbai.oceanprotocol.com",
        "NETWORK_NAME": "mumbai",
        "BLOCK_CONFIRMATIONS": 1,
        "TRANSACTION_TIMEOUT": 60,
    },
}


@enforce_types
def get_config_dict(chain_id: int, network_url: str) -> dict:
    if chain_id not in CONFIG_NETWORK_HELPER:
        raise ValueError("The chain id for the specific RPC could not be fetched!")

    config_helper = copy.deepcopy(config_defaults)
    config_helper.update(CONFIG_NETWORK_HELPER[chain_id])
    config_helper["CHAIN_ID"] = chain_id
    config_helper["OCEAN_NETWORK_URL"] = network_url

    if chain_id != 8996:
        config_helper["METADATA_CACHE_URI"] = METADATA_CACHE_URI

    return config_helper


class ExampleConfig:
    @staticmethod
    @enforce_types
    def get_config(network_url=None) -> dict:
        """Return config dict containing default values for a given network.
        Chain ID is determined by querying the RPC specified by network_url.
        """

        if not network_url:
            network_url = "http://127.0.0.1:8545"
            chain_id = 8996
        else:
            w3 = get_web3(network_url)
            chain_id = w3.eth.chain_id

        config_dict = get_config_dict(chain_id, network_url)
        config_dict["OCEAN_NETWORK_URL"] = network_url

        return config_dict
