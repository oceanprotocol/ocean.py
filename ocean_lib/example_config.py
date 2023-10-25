#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import copy
import logging
import os
from pathlib import Path
from typing import Optional

import addresses
from enforce_typing import enforce_types
from web3 import Web3
from web3.exceptions import ExtraDataLengthError

from ocean_lib.web3_internal.http_provider import get_web3_connection_provider

logging.basicConfig(level=logging.INFO)

DEFAULT_METADATA_CACHE_URI = "http://172.15.0.5:5000"
METADATA_CACHE_URI = "https://v4.aquarius.oceanprotocol.com"
DEFAULT_PROVIDER_URL = "http://172.15.0.4:8030"

config_defaults = {
    "METADATA_CACHE_URI": "http://172.15.0.5:5000",
    "PROVIDER_URL": "http://172.15.0.4:8030",
    "DOWNLOADS_PATH": "consume-downloads",
}

PROVIDER_PER_NETWORK = {
    1: "https://v4.provider.mainnet.oceanprotocol.com",
    5: "https://v4.provider.goerli.oceanprotocol.com",
    56: "https://v4.provider.bsc.oceanprotocol.com",
    137: "https://v4.provider.polygon.oceanprotocol.com",
    246: "https://v4.provider.energyweb.oceanprotocol.com",
    1285: "https://v4.provider.moonriver.oceanprotocol.com",
    1287: "https://v4.provider.moonbase.oceanprotocol.com",
    80001: "https://v4.provider.mumbai.oceanprotocol.com",
    58008: "https://v4.provider.oceanprotocol.com",
    8996: DEFAULT_PROVIDER_URL,
}

NAME_PER_NETWORK = {
    1: "mainnet",
    5: "goerli",
    56: "bsc",
    137: "polygon",
    246: "energyweb",
    1285: "moonriver",
    1287: "moonbase",
    80001: "mumbai",
    58008: "sepolia",
    8996: "development",
}


def get_config_dict(network_url: Optional[str] = None) -> dict:
    """Return config dict containing default values for a given network.
    Chain ID is determined by querying the RPC specified by network_url.
    """
    if not network_url:
        network_url = "http://localhost:8545"

    config_dict = copy.deepcopy(config_defaults)
    config_dict["web3_instance"] = get_web3(network_url)
    config_dict["CHAIN_ID"] = config_dict["web3_instance"].eth.chain_id

    chain_id = config_dict["CHAIN_ID"]
    if chain_id not in PROVIDER_PER_NETWORK:
        raise ValueError("The chain id for the specific RPC could not be fetched!")

    config_dict["PROVIDER_URL"] = PROVIDER_PER_NETWORK[chain_id]
    config_dict["NETWORK_NAME"] = NAME_PER_NETWORK[chain_id]

    if chain_id != 8996:
        config_dict["METADATA_CACHE_URI"] = METADATA_CACHE_URI

    if os.getenv("ADDRESS_FILE"):
        base_file = os.getenv("ADDRESS_FILE")
        address_file = os.path.expanduser(base_file)
    elif chain_id == 8996:
        # this is auto-created when barge is run
        base_file = "~/.ocean/ocean-contracts/artifacts/address.json"
        address_file = os.path.expanduser(base_file)
    else:
        # `contract_addresses` comes from "ocean-contracts" pypi library,
        # a JSON blob holding addresses of contract deployments, per network
        address_file = (
            Path(os.path.join(addresses.__file__, "..", "address.json"))
            .expanduser()
            .resolve()
        )
    assert os.path.exists(address_file), f"Could not find address_file={address_file}."

    config_dict["ADDRESS_FILE"] = address_file

    return config_dict


@enforce_types
def get_web3(network_url: str) -> Web3:
    """
    Return a web3 instance connected via the given network_url.
    Adds POA middleware when connecting to the Rinkeby Testnet.
    A note about using the `rinkeby` testnet:
    Web3 py has an issue when making some requests to `rinkeby`
    - the issue is described here: https://github.com/ethereum/web3.py/issues/549
    - and the fix is here: https://web3py.readthedocs.io/en/latest/middleware.html#geth-style-proof-of-authority
    """
    provider = get_web3_connection_provider(network_url)
    web3 = Web3(provider)

    try:
        web3.eth.get_block("latest")
    except ExtraDataLengthError:
        from web3.middleware import geth_poa_middleware

        web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    web3.strict_bytes_type_checking = False

    return web3
