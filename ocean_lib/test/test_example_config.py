#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.config import (
    DEFAULT_METADATA_CACHE_URI,
    DEFAULT_PROVIDER_URL,
    METADATA_CACHE_URI,
    SECTION_ETH_NETWORK,
)
from ocean_lib.example_config import NETWORK_NAME, ExampleConfig, get_config_dict


@pytest.mark.unit
def test_ganache_example_config(monkeypatch):
    """Tests the config structure of ganache network."""

    monkeypatch.setenv("OCEAN_NETWORK_URL", "http://127.0.0.1:8545")
    config = ExampleConfig.get_config()

    assert config.chain_id == 8996
    assert config.network_url == "http://127.0.0.1:8545"
    assert config.metadata_cache_uri == DEFAULT_METADATA_CACHE_URI
    assert config.provider_url == DEFAULT_PROVIDER_URL
    assert config.block_confirmations.value == 0

    assert config.__dict__["_sections"][SECTION_ETH_NETWORK][NETWORK_NAME] == "ganache"


@pytest.mark.unit
def test_polygon_example_config(monkeypatch):
    """Tests the config structure of Polygon network."""

    monkeypatch.setenv("OCEAN_NETWORK_URL", "https://rpc.polygon.oceanprotocol.com")
    config = ExampleConfig.get_config()

    assert config.chain_id == 137
    assert config.network_url == "https://rpc.polygon.oceanprotocol.com"
    assert config.metadata_cache_uri == METADATA_CACHE_URI
    assert config.provider_url == "https://v4.provider.polygon.oceanprotocol.com"
    assert config.block_confirmations.value == 15

    assert config.__dict__["_sections"][SECTION_ETH_NETWORK][NETWORK_NAME] == "polygon"


@pytest.mark.unit
def test_bsc_example_config(monkeypatch):
    """Tests the config structure of BSC network."""

    monkeypatch.setenv("OCEAN_NETWORK_URL", "https://bsc-dataseed.binance.org")
    config = ExampleConfig.get_config()

    assert config.chain_id == 56
    assert config.network_url == "https://bsc-dataseed.binance.org"
    assert config.metadata_cache_uri == METADATA_CACHE_URI
    assert config.provider_url == "https://v4.provider.bsc.oceanprotocol.com"
    assert config.block_confirmations.value == 1

    assert config.__dict__["_sections"][SECTION_ETH_NETWORK][NETWORK_NAME] == "bsc"


@pytest.mark.unit
def test_moonbeam_alpha_example_config(monkeypatch):
    """Tests the config structure of Moonbeam Alpha network."""

    monkeypatch.setenv("OCEAN_NETWORK_URL", "https://rpc.testnet.moonbeam.network")
    config = ExampleConfig.get_config()

    assert config.chain_id == 1287
    assert config.network_url == "https://rpc.testnet.moonbeam.network"
    assert config.metadata_cache_uri == METADATA_CACHE_URI
    assert config.provider_url == "https://v4.provider.moonbase.oceanprotocol.com"
    assert config.block_confirmations.value == 3

    assert (
        config.__dict__["_sections"][SECTION_ETH_NETWORK][NETWORK_NAME]
        == "moonbeamalpha"
    )


@pytest.mark.unit
def test_noconfig(monkeypatch):
    """Tests the config fails with wrong chain id."""
    monkeypatch.setenv("OCEAN_NETWORK_URL", "https://bad.network")
    with pytest.raises(ValueError, match="could not be fetched!"):
        get_config_dict(0)
