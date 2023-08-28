#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import copy
import logging
import os
from pathlib import Path

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
    "NETWORK_NAME": "development",
    "METADATA_CACHE_URI": "http://172.15.0.5:5000",
    "PROVIDER_URL": "http://172.15.0.4:8030",
    "DOWNLOADS_PATH": "consume-downloads",
}

PROVIDER_PER_NETWORK = {
    "mainnet": "https://v4.provider.mainnet.oceanprotocol.com",
    "goerli": "https://v4.provider.goerli.oceanprotocol.com",
    "bsc": "https://v4.provider.bsc.oceanprotocol.com",
    "polygon": "https://v4.provider.polygon.oceanprotocol.com",
    "energyweb": "https://v4.provider.energyweb.oceanprotocol.com",
    "moonriver": "https://v4.provider.moonriver.oceanprotocol.com",
    "moonbase": "https://v4.provider.moonbase.oceanprotocol.com",
    "mumbai": "https://v4.provider.mumbai.oceanprotocol.com",
    "development": DEFAULT_PROVIDER_URL,
}


def get_rpc_url(network_name: str) -> str:
    """Return the RPC URL for a given network."""
    if network_name == "development":
        if os.getenv("DEVELOPMENT_RPC_URL"):
            return os.getenv("DEVELOPMENT_RPC_URL")

        return "http://localhost:8545"

    base_url = None

    if os.getenv(f"{network_name.upper()}_RPC_URL"):
        base_url = os.getenv(f"{network_name.upper()}_RPC_URL")

    if os.getenv("WEB3_INFURA_PROJECT_ID"):
        base_url = f"{base_url}{os.getenv('WEB3_INFURA_PROJECT_ID')}"

    if base_url:
        return base_url

    raise Exception(f"Need to set {network_name.upper()}_RPC_URL env variable.")


def get_config_dict(network_name=None) -> dict:
    """Return config dict containing default values for a given network.
    Chain ID is determined by querying the RPC specified by network_url.
    """
    if not network_name or network_name in ["ganache", "development"]:
        network_name = "development"

    if network_name not in PROVIDER_PER_NETWORK:
        raise ValueError("The chain id for the specific RPC could not be fetched!")

    network_url = get_rpc_url(network_name)

    config_dict = copy.deepcopy(config_defaults)
    config_dict["PROVIDER_URL"] = PROVIDER_PER_NETWORK[network_name]
    config_dict["NETWORK_NAME"] = network_name
    config_dict["web3_instance"] = get_web3(network_url)
    config_dict["CHAIN_ID"] = config_dict["web3_instance"].eth.chain_id

    if network_name != "development":
        config_dict["METADATA_CACHE_URI"] = METADATA_CACHE_URI

    if os.getenv("ADDRESS_FILE"):
        base_file = os.getenv("ADDRESS_FILE")
        address_file = os.path.expanduser(base_file)
    elif network_name == "development":
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
