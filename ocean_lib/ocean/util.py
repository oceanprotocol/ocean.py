#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.web3_internal.contract_utils import (
    get_contracts_addresses as get_contracts_addresses_web3,
)
from ocean_lib.web3_internal.utils import get_network_name
from ocean_lib.web3_internal.web3_overrides.http_provider import CustomHTTPProvider
from web3 import WebsocketProvider

GANACHE_URL = "http://127.0.0.1:8545"


def get_web3_connection_provider(network_url):
    """Return the suitable web3 provider based on the network_url.

    Requires going through some gateway such as `infura`.

    Using infura has some issues if your code is relying on evm events.
    To use events with an infura connection you have to use the websocket interface.

    Make sure the `infura` url for websocket connection has the following format
    wss://rinkeby.infura.io/ws/v3/357f2fe737db4304bd2f7285c5602d0d
    Note the `/ws/` in the middle and the `wss` protocol in the beginning.

    A note about using the `rinkeby` testnet:
        Web3 py has an issue when making some requests to `rinkeby`
        - the issue is described here: https://github.com/ethereum/web3.py/issues/549
        - and the fix is here: https://web3py.readthedocs.io/en/latest/middleware.html#geth-style-proof-of-authority

    :param network_url: str
    :return: provider : HTTPProvider
    """
    if network_url.startswith("http"):
        return CustomHTTPProvider(network_url)
    elif network_url.startswith("ws"):
        return WebsocketProvider(network_url)
    else:
        msg = (
            f"The given network_url *{network_url}* does not start with either "
            f"`http` or `wss`. A correct network url is required."
        )
        raise AssertionError(msg)


def get_contracts_addresses(address_file, network):
    return get_contracts_addresses_web3(network, address_file)


@enforce_types
def to_base_18(amt: float) -> int:
    return to_base(amt, 18)


@enforce_types
def to_base(amt: float, dec: int) -> int:
    """Returns value in e.g. wei (taking e.g. ETH as input)."""
    return int(amt * 1 * 10 ** dec)


@enforce_types
def from_base_18(num_base: int) -> float:
    return from_base(num_base, 18)


@enforce_types
def from_base(num_base: int, dec: int) -> float:
    """Returns value in e.g. ETH (taking e.g. wei as input)."""
    return float(num_base / (10 ** dec))


def get_dtfactory_address(address_file, network=None, web3=None):
    """Returns the DTFactory address for given network or web3 instance
    Requires either network name or web3 instance.
    """
    return DTFactory.configured_address(
        network or get_network_name(web3=web3), address_file
    )


def get_bfactory_address(address_file, network=None, web3=None):
    """Returns the BFactory address for given network or web3 instance
    Requires either network name or web3 instance.
    """
    return BFactory.configured_address(
        network or get_network_name(web3=web3), address_file
    )


def get_ocean_token_address(address_file, network=None, web3=None):
    """Returns the Ocean token address for given network or web3 instance
    Requires either network name or web3 instance.
    """
    addresses = get_contracts_addresses(
        address_file, network or get_network_name(web3=web3)
    )
    return addresses.get("Ocean") if addresses else None
