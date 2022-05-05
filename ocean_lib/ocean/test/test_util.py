#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from web3 import Web3

from ocean_lib.ocean import util
from ocean_lib.ocean.util import get_address_of_type, get_ocean_token_address


@pytest.mark.unit
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


@pytest.mark.unit
def test_get_ocean_token_address(config):
    addresses = util.get_contracts_addresses(config.address_file, "ganache")
    assert addresses
    assert isinstance(addresses, dict)
    assert "Ocean" in addresses

    address = get_ocean_token_address(config.address_file, "ganache")
    assert Web3.isChecksumAddress(address), "It is not a checksum token address."
    assert address == Web3.toChecksumAddress(addresses["Ocean"])


@pytest.mark.unit
def test_get_address_by_type(config):
    addresses = util.get_contracts_addresses(config.address_file, "ganache")

    address = get_address_of_type(config, "Ocean")
    assert Web3.isChecksumAddress(address), "It is not a checksum token address."
    assert address == Web3.toChecksumAddress(addresses["Ocean"])


@pytest.mark.unit
def test_get_address_of_type_failure(config):
    with pytest.raises(KeyError):
        get_address_of_type(config, "", "non-existent-key")
