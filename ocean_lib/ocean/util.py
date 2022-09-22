#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
from typing import Dict, Optional, Union

from enforce_typing import enforce_types
from web3 import WebsocketProvider
from web3.main import Web3
from web3.middleware import geth_poa_middleware

from ocean_lib.ocean.networkutil import chainIdToNetwork
from ocean_lib.web3_internal.contract_utils import (
    get_contracts_addresses as get_contracts_addresses_web3,
)
from ocean_lib.web3_internal.utils import get_network_name
from ocean_lib.web3_internal.web3_overrides.http_provider import CustomHTTPProvider

GANACHE_URL = "http://127.0.0.1:8545"


@enforce_types
def get_web3(network_url: Optional[str] = None) -> Web3:
    """
    Return a web3 instance connected via the given network_url.
    Adds POA middleware if needed.
    """
    if not network_url:
        network_url = GANACHE_URL

    provider = get_web3_connection_provider(network_url)
    web3 = Web3(provider)

    # Some chains get an ExtraDataLengthError. To fix, inject some POA middleware
    # - Issue: https://github.com/ethereum/web3.py/issues/549
    # - Fix: https://web3py.readthedocs.io/en/latest/middleware.html#geth-style-proof-of-authority
    problem_networks = [
        "rinkeby",
        "mumbai",
    ]  # add to this if we find issues in other networks
    if chainIdToNetwork(web3.eth.chain_id).lower() in problem_networks:
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    return web3


@enforce_types
def get_web3_connection_provider(
    network_url: str,
) -> Union[CustomHTTPProvider, WebsocketProvider]:
    """Return the suitable web3 provider based on the network_url.

    Requires going through some gateway such as `infura`.

    Using infura has some issues if your code is relying on evm events.
    To use events with an infura connection you have to use the websocket interface.

    Make sure the `infura` url for websocket connection has the following format
    wss://rinkeby.infura.io/ws/v3/357f2fe737db4304bd2f7285c5602d0d
    Note the `/ws/` in the middle and the `wss` protocol in the beginning.

    :param network_url: str
    :return: provider : Union[CustomHTTPProvider, WebsocketProvider]
    """
    if network_url.startswith("http"):
        return CustomHTTPProvider(network_url)
    elif network_url.startswith("ws"):
        return WebsocketProvider(network_url)
    else:
        msg = (
            f"The given network_url *{network_url}* does not start with either"
            f"`http` or `wss`. A correct network url is required."
        )
        raise AssertionError(msg)


def get_contracts_addresses(address_file: str, network: str) -> Dict[str, str]:
    return get_contracts_addresses_web3(network, address_file)


@enforce_types
def get_address_of_type(
    config_dict: dict, address_type: str, key: Optional[str] = None
) -> str:
    address_file = config_dict.get("ADDRESS_FILE")
    network_name = config_dict.get("NETWORK_NAME")

    addresses = get_contracts_addresses(address_file, network_name)
    if address_type not in addresses.keys():
        raise KeyError(f"{address_type} address is not set in the config file")
    address = (
        addresses[address_type]
        if not isinstance(addresses[address_type], dict)
        else addresses[address_type].get(key, addresses[address_type]["1"])
    )
    return Web3.toChecksumAddress(address.lower())


@enforce_types
def get_ocean_token_address(
    config_dict: dict, network: Optional[str] = None, web3: Optional[Web3] = None
) -> str:
    """Returns the Ocean token address for given network or web3 instance
    Requires either network name or web3 instance.
    """
    address_file = config_dict.get("ADDRESS_FILE", os.getenv("ADDRESS_FILE"))

    addresses = get_contracts_addresses(
        address_file, network or get_network_name(web3=web3)
    )
    return Web3.toChecksumAddress(addresses.get("Ocean").lower()) if addresses else None
