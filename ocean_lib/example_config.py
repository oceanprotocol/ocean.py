#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import copy
import logging
import os
from pathlib import Path

import addresses

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
    "polygon-main": "https://v4.provider.polygon.oceanprotocol.com",
    "energyweb": "https://v4.provider.energyweb.oceanprotocol.com",
    "moonriver": "https://v4.provider.moonriver.oceanprotocol.com",
    "moonbase": "https://v4.provider.moonbase.oceanprotocol.com",
    "development": DEFAULT_PROVIDER_URL,
    "polygon-test": "https://v4.provider.mumbai.oceanprotocol.com",
}


def get_config_dict(network_name=None) -> dict:
    """Return config dict containing default values for a given network.
    Chain ID is determined by querying the RPC specified by network_url.
    """
    if not network_name:
        network_name = "development"

    if network_name not in PROVIDER_PER_NETWORK:
        raise ValueError("The chain id for the specific RPC could not be fetched!")

    config_dict = copy.deepcopy(config_defaults)
    config_dict["PROVIDER_URL"] = PROVIDER_PER_NETWORK[network_name]
    config_dict["NETWORK_NAME"] = network_name

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
