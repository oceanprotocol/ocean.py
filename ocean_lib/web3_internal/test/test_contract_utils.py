#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.ocean import util
from ocean_lib.web3_internal.contract_utils import (
    _checksum_contract_addresses,
    get_web3_connection_provider,
)


def test_checksum_contract_addresses(web3, monkeypatch):
    addresses = {
        "chainId": 7,
        "test": "0x20802d1a9581b94e51db358c09e0818d6bd071b4",
        "dict": {"address": "0xe2dd09d719da89e5a3d0f2549c7e24566e947260"},
    }
    assert web3.isChecksumAddress(addresses["test"]) is False
    assert web3.isChecksumAddress(addresses["dict"]["address"]) is False
    checksum_addresses = _checksum_contract_addresses(addresses)
    assert web3.isChecksumAddress(checksum_addresses["test"]) is True
    assert web3.isChecksumAddress(addresses["dict"]["address"]) is True


@pytest.mark.unit
def test_get_web3_connection_provider(monkeypatch):
    # GANACHE_URL
    provider = get_web3_connection_provider(util.GANACHE_URL)
    assert provider.endpoint_uri == util.GANACHE_URL

    # typical http uri "http://foo.com"
    provider = get_web3_connection_provider("http://foo.com")
    assert provider.endpoint_uri == "http://foo.com"

    # typical https uri "https://bar.com"
    provider = get_web3_connection_provider("https://bar.com")
    assert provider.endpoint_uri == "https://bar.com"

    # non-supported name
    with pytest.raises(AssertionError):
        get_web3_connection_provider("not_network_name")

    # typical websockets uri "wss://foo.com"
    provider = get_web3_connection_provider("wss://bah.com")
    assert provider.endpoint_uri == "wss://bah.com"
