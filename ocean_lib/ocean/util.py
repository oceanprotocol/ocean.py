#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from ocean_lib.config import Config
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.ocean.env_constants import (
    ENV_CONFIG_FILE,
    ENV_INFURA_CONNECTION_TYPE,
    ENV_INFURA_PROJECT_ID,
)
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.utils import get_network_name
from ocean_lib.web3_internal.web3_overrides.http_provider import CustomHTTPProvider
from ocean_lib.web3_internal.web3_provider import Web3Provider
from web3 import WebsocketProvider

WEB3_INFURA_PROJECT_ID = "357f2fe737db4304bd2f7285c5602d0d"
GANACHE_URL = "http://127.0.0.1:8545"
POLYGON_URL = "https://rpc.polygon.oceanprotocol.com"

# shortcut names for networks that *Infura* supports, plus ganache and polygon
SUPPORTED_NETWORK_NAMES = {
    "rinkeby",
    "kovan",
    "ganache",
    "mainnet",
    "ropsten",
    "polygon",
}


def get_infura_connection_type():
    _type = os.getenv(ENV_INFURA_CONNECTION_TYPE, "http")
    if _type not in ("http", "websocket"):
        _type = "http"

    return _type


def get_infura_id():
    return os.getenv(ENV_INFURA_PROJECT_ID, WEB3_INFURA_PROJECT_ID)


def get_infura_url(infura_id, network):
    conn_type = get_infura_connection_type()
    if conn_type == "http":
        return f"https://{network}.infura.io/v3/{infura_id}"

    if conn_type == "websocket":
        return f"wss://{network}.infura.io/ws/v3/{infura_id}"

    raise AssertionError(f"Unknown connection type {conn_type}")


def get_web3_connection_provider(network_url):
    """Return the suitable web3 provider based on the network_url.

    When connecting to a public ethereum network (mainnet or a test net) without
    running a local node requires going through some gateway such as `infura`.

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
        provider = CustomHTTPProvider(network_url)
    elif network_url.startswith("ws"):
        provider = WebsocketProvider(network_url)
    elif network_url == "ganache":
        provider = CustomHTTPProvider(GANACHE_URL)
    elif network_url == "polygon":
        provider = CustomHTTPProvider(POLYGON_URL)
    else:
        assert network_url in SUPPORTED_NETWORK_NAMES, (
            f"The given network_url *{network_url}* does not start with either "
            f"`http` or `wss`, in this case a network name is expected and must "
            f"be one of the supported networks {SUPPORTED_NETWORK_NAMES}."
        )
        network_url = get_infura_url(get_infura_id(), network_url)
        if network_url.startswith("http"):
            provider = CustomHTTPProvider(network_url)
        else:
            provider = WebsocketProvider(network_url)

    return provider


def get_contracts_addresses(network, config):
    addresses = {}
    try:
        addresses = ContractHandler.get_contracts_addresses(
            network, config.address_file
        )
    except Exception as e:
        print(
            f"error reading contract addresses: {e}.\n"
            f"artifacts path is {ContractHandler.artifacts_path}, address file is {config.address_file}"
        )

    if not addresses:
        print(
            f"cannot find contract addresses: \n"
            f"artifacts path is {ContractHandler.artifacts_path}, address file is {config.address_file}"
        )
        print(f"address file exists? {os.path.exists(config.address_file)}")
        print(
            f"artifacts path exists? {os.path.exists(ContractHandler.artifacts_path)}"
        )
        print(
            f"contents of artifacts folder: \n"
            f"{os.listdir(ContractHandler.artifacts_path)}"
        )
    return addresses or {}


@enforce_types_shim
def to_base_18(amt: float) -> int:
    return to_base(amt, 18)


@enforce_types_shim
def to_base(amt: float, dec: int) -> int:
    """Returns value in e.g. wei (taking e.g. ETH as input)."""
    return int(amt * 1 * 10 ** dec)


@enforce_types_shim
def from_base_18(num_base: int) -> float:
    return from_base(num_base, 18)


@enforce_types_shim
def from_base(num_base: int, dec: int) -> float:
    """Returns value in e.g. ETH (taking e.g. wei as input)."""
    return float(num_base / (10 ** dec))


def get_dtfactory_address(network=None):
    return DTFactory.configured_address(
        network or get_network_name(), ConfigProvider.get_config().address_file
    )


def get_bfactory_address(network=None):
    return BFactory.configured_address(
        network or get_network_name(), ConfigProvider.get_config().address_file
    )


def get_ocean_token_address(network=None):
    addresses = get_contracts_addresses(
        network or get_network_name(), ConfigProvider.get_config()
    )
    return addresses.get("Ocean") if addresses else None


def init_components(config=None):
    if config is None:
        config = Config(os.getenv(ENV_CONFIG_FILE))

    ConfigProvider.set_config(config)
    Web3Provider.init_web3(provider=get_web3_connection_provider(config.network_url))
    ContractHandler.set_artifacts_path(config.artifacts_path)
