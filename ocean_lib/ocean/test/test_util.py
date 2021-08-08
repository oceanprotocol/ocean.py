#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import os

import pytest
from ocean_lib.ocean import util
from ocean_lib.ocean.env_constants import (
    ENV_INFURA_CONNECTION_TYPE,
    ENV_INFURA_PROJECT_ID,
)
from ocean_lib.ocean.util import (
    from_base,
    get_bfactory_address,
    get_dtfactory_address,
    get_ocean_token_address,
)


def test_get_infura_connection_type(monkeypatch):
    # no envvar
    if ENV_INFURA_CONNECTION_TYPE in os.environ:
        monkeypatch.delenv(ENV_INFURA_CONNECTION_TYPE)
    assert (
        util.get_infura_connection_type() == "http"
    ), "The default connection type for infura is not http."

    # envvar is "http"
    monkeypatch.setenv(ENV_INFURA_CONNECTION_TYPE, "http")
    assert util.get_infura_connection_type() == "http"

    # envvar is "websocket"
    monkeypatch.setenv(ENV_INFURA_CONNECTION_TYPE, "websocket")
    assert util.get_infura_connection_type() == "websocket"

    # envvar is other val
    monkeypatch.setenv(ENV_INFURA_CONNECTION_TYPE, "foo_type")
    assert util.get_infura_connection_type() == "http"


def test_get_infura_id(monkeypatch):
    # no envvar
    if ENV_INFURA_PROJECT_ID in os.environ:
        monkeypatch.delenv(ENV_INFURA_PROJECT_ID)
    assert util.get_infura_id() == util.WEB3_INFURA_PROJECT_ID

    # envvar is other val
    monkeypatch.setenv(ENV_INFURA_PROJECT_ID, "foo_id")
    assert util.get_infura_id() == "foo_id"


def test_get_infura_url(monkeypatch):
    # envvar is "http"
    monkeypatch.setenv(ENV_INFURA_CONNECTION_TYPE, "http")
    assert util.get_infura_url("id1", "net1") == "https://net1.infura.io/v3/id1"

    # envvar is "websocket"
    monkeypatch.setenv(ENV_INFURA_CONNECTION_TYPE, "websocket")
    assert util.get_infura_url("id2", "net2") == "wss://net2.infura.io/ws/v3/id2"

    # envvar is other val - it will resort to "http"
    monkeypatch.setenv(ENV_INFURA_CONNECTION_TYPE, "foo_type")
    assert util.get_infura_url("id3", "net3") == "https://net3.infura.io/v3/id3"


def test_get_web3_connection_provider(monkeypatch):
    # "ganache"
    provider = util.get_web3_connection_provider("ganache")
    assert provider.endpoint_uri == util.GANACHE_URL  # e.g. http://127.0.0.1:8545

    # GANACHE_URL
    provider = util.get_web3_connection_provider(util.GANACHE_URL)
    assert provider.endpoint_uri == util.GANACHE_URL

    # typical http uri "http://foo.com"
    provider = util.get_web3_connection_provider("http://foo.com")
    assert provider.endpoint_uri == "http://foo.com"

    # typical https uri "https://bar.com"
    provider = util.get_web3_connection_provider("https://bar.com")
    assert provider.endpoint_uri == "https://bar.com"

    # "rinkeby"
    assert "rinkeby" in util.SUPPORTED_NETWORK_NAMES
    monkeypatch.setenv(ENV_INFURA_PROJECT_ID, "id1")
    provider = util.get_web3_connection_provider("rinkeby")
    assert provider.endpoint_uri == "https://rinkeby.infura.io/v3/id1"

    # polygon network name
    assert (
        "polygon" in util.SUPPORTED_NETWORK_NAMES
    ), "polygon is missing from SUPPORTED_NETWORK_NAMES"
    assert util.POLYGON_URL == "https://rpc.polygon.oceanprotocol.com"
    provider = util.get_web3_connection_provider("polygon")
    assert provider.endpoint_uri == "https://rpc.polygon.oceanprotocol.com"

    # bsc network name
    assert (
        "bsc" in util.SUPPORTED_NETWORK_NAMES
    ), "bsc is missing from SUPPORTED_NETWORK_NAMES"
    assert util.BSC_URL == "https://bsc-dataseed.binance.org"
    provider = util.get_web3_connection_provider("bsc")
    assert provider.endpoint_uri == "https://bsc-dataseed.binance.org"

    # all infura-supported network names
    for network in util.SUPPORTED_NETWORK_NAMES:
        if network == "ganache" or "polygon":
            continue  # tested above
        monkeypatch.setenv(ENV_INFURA_PROJECT_ID, f"id_{network}")
        provider = util.get_web3_connection_provider(network)
        assert provider.endpoint_uri == f"https://{network}.infura.io/v3/id_{network}"

    # non-supported name
    monkeypatch.setenv(ENV_INFURA_PROJECT_ID, "idx")
    with pytest.raises(Exception):
        util.get_web3_connection_provider("not_network_name")

    # typical websockets uri "wss://foo.com"
    provider = util.get_web3_connection_provider("wss://bah.com")
    assert provider.endpoint_uri == "wss://bah.com"


def test_get_contracts_addresses(config):
    addresses = util.get_contracts_addresses(config.address_file, "ganache")
    assert addresses
    assert isinstance(addresses, dict)
    assert (
        "DTFactory"
        and "BFactory"
        and "FixedRateExchange"
        and "Metadata"
        and "Ocean" in addresses
    )
    assert len(addresses) == 6
    for value in addresses.values():
        assert value.startswith("0x"), "It is not a token address."


def test_from_base():
    res = from_base(10000000000, 10)
    assert res == 1.0, "Incorrect conversion to ether."
    res = from_base(100, 2)
    assert res == 1.0, "Incorrect conversion to ether."


def test_get_dtfactory_address(config):
    addresses = util.get_contracts_addresses(config.address_file, "ganache")
    assert addresses
    assert isinstance(addresses, dict)
    assert "DTFactory" in addresses

    address = get_dtfactory_address(config.address_file, "ganache")
    assert address[:2] == "0x", "It is not a token address."
    assert address == addresses["DTFactory"]


def test_get_bfactory_address(config):
    addresses = util.get_contracts_addresses(config.address_file, "ganache")
    assert addresses
    assert isinstance(addresses, dict)
    assert "BFactory" in addresses

    address = get_bfactory_address(config.address_file, "ganache")
    assert address[:2] == "0x", "It is not a token address."
    assert address == addresses["BFactory"]


def test_get_ocean_token_address(config):
    addresses = util.get_contracts_addresses(config.address_file, "ganache")
    assert addresses
    assert isinstance(addresses, dict)
    assert "Ocean" in addresses

    address = get_ocean_token_address(config.address_file, "ganache")
    assert address[:2] == "0x", "It is not a token address."
    assert address == addresses["Ocean"]
