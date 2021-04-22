#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import os

import pytest

from ocean_lib.config import Config
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.ocean import util
from ocean_lib.ocean.env_constants import (
    ENV_INFURA_CONNECTION_TYPE,
    ENV_INFURA_PROJECT_ID,
    ENV_CONFIG_FILE,
)


def test_get_infura_connection_type(monkeypatch):
    # no envvar
    if ENV_INFURA_CONNECTION_TYPE in os.environ:
        monkeypatch.delenv(ENV_INFURA_CONNECTION_TYPE)
    assert util.get_infura_connection_type() == "http"

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

    # all infura-supported network names
    for network in util.SUPPORTED_NETWORK_NAMES:
        if network == "ganache":
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


def test_get_contracts_addresses():
    config = Config(os.getenv(ENV_CONFIG_FILE))
    ConfigProvider.set_config(config)
    addresses = util.get_contracts_addresses("ganache", config)
    assert addresses
    assert isinstance(addresses, dict)
    assert (
        "DTFactory"
        and "BFactory"
        and "FixedRateExchange"
        and "Metadata"
        and "Ocean" in addresses
    )
    assert len(addresses) == 5
    for _, value in addresses.items():
        assert value.startswith("0x")


# FIXME: add tests for:
# to_base_18
# to_base
# from_base_18
# from_base
# get_dtfactory_address
# get_bfactory_address
# get_ocean_token_address
# init_components
