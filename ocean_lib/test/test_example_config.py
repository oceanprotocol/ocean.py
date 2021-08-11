#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.config import (
    DEFAULT_METADATA_CACHE_URI,
    DEFAULT_PROVIDER_URL,
    SECTION_ETH_NETWORK,
)
from ocean_lib.example_config import ExampleConfig, NETWORK_NAME, NAME_STORE_INTERVAL


def test_invalid_schema_url(monkeypatch):
    """Tests a bad URL schema."""

    monkeypatch.setenv("OCEAN_NETWORK_URL", "bad_url")
    with pytest.raises(AssertionError):
        ExampleConfig.get_config()


def test_ganache_example_config(monkeypatch):
    """Tests the config structure of ganache network."""

    monkeypatch.setenv("OCEAN_NETWORK_URL", "http://127.0.0.1:8545")
    config = ExampleConfig.get_config()

    assert config.chain_id == 1337
    assert config.network_url == "http://127.0.0.1:8545"
    assert config.metadata_cache_uri == DEFAULT_METADATA_CACHE_URI
    assert config.provider_url == DEFAULT_PROVIDER_URL

    assert config.__dict__["_sections"][SECTION_ETH_NETWORK][NETWORK_NAME] == "ganache"
    assert config.__dict__["_sections"][SECTION_ETH_NETWORK][
        NAME_STORE_INTERVAL
    ] == str(2.5)


def test_bsc_example_config(monkeypatch):
    """Tests the config structure of BSC network."""

    monkeypatch.setenv("OCEAN_NETWORK_URL", "https://bsc-dataseed.binance.org")
    config = ExampleConfig.get_config()

    assert config.chain_id == 56
    assert config.network_url == "https://bsc-dataseed.binance.org"
    assert config.metadata_cache_uri == "https://aquarius.oceanprotocol.com"
    assert config.provider_url == "https://provider.bsc.oceanprotocol.com"

    assert config.__dict__["_sections"][SECTION_ETH_NETWORK][NETWORK_NAME] == "bsc"
    assert config.__dict__["_sections"][SECTION_ETH_NETWORK][
        NAME_STORE_INTERVAL
    ] == str(1.5)
