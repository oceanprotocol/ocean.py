#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from ocean_lib.ocean import util
from ocean_lib.ocean.util import (
    from_base,
    from_base_18,
    get_bfactory_address,
    get_dtfactory_address,
    get_ocean_token_address,
    to_base,
    to_base_18,
)


def test_get_web3_connection_provider(monkeypatch):
    # GANACHE_URL
    provider = util.get_web3_connection_provider(util.GANACHE_URL)
    assert provider.endpoint_uri == util.GANACHE_URL

    # typical http uri "http://foo.com"
    provider = util.get_web3_connection_provider("http://foo.com")
    assert provider.endpoint_uri == "http://foo.com"

    # typical https uri "https://bar.com"
    provider = util.get_web3_connection_provider("https://bar.com")
    assert provider.endpoint_uri == "https://bar.com"

    # non-supported name
    with pytest.raises(AssertionError):
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


def test_to_base_18():
    res = to_base_18(1.0)
    assert res == 1000000000000000000, "Incorrect conversion to wei."


def test_to_base():
    res = to_base(1.0, 10)
    assert res == 10000000000, "Incorrect conversion to wei."
    res = to_base(1.0, 2)
    assert res == 100, "Incorrect conversion to wei."
    res = to_base(1.0, 18)
    assert res == to_base_18(1.0), "Incorrect conversion to wei."


def test_from_base_and_from_base_18():
    res = from_base(10000000000, 10)
    assert res == 1.0, "Incorrect conversion to ETH."
    res = from_base(100, 2)
    assert res == 1.0, "Incorrect conversion to ETH."
    res = from_base(to_base_18(1.0), 18)
    assert res == from_base_18(to_base_18(1.0)), "Incorrect conversion to ETH."


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
