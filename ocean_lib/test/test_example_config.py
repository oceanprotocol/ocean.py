#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from ocean_lib.config import (
    DEFAULT_METADATA_CACHE_URI,
    DEFAULT_PROVIDER_URL,
    SECTION_ETH_NETWORK,
)
from ocean_lib.example_config import (
    ExampleConfig,
    NETWORK_NAME,
    NAME_BLOCK_CONFIRMATION_POLL_INTERVAL,
)


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
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL
    ] == str(2.5)


def test_polygon_example_config(monkeypatch):
    """Tests the config structure of Polygon network."""

    monkeypatch.setenv("OCEAN_NETWORK_URL", "https://rpc-mainnet.maticvigil.com")
    config = ExampleConfig.get_config()

    assert config.chain_id == 137
    assert config.network_url == "https://rpc-mainnet.maticvigil.com"
    assert config.metadata_cache_uri == "https://aquarius.oceanprotocol.com"
    assert config.provider_url == "https://provider.polygon.oceanprotocol.com"

    assert config.__dict__["_sections"][SECTION_ETH_NETWORK][NETWORK_NAME] == "polygon"
    assert config.__dict__["_sections"][SECTION_ETH_NETWORK][
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL
    ] == str(1)


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
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL
    ] == str(1.5)


def test_moonbeam_alpha_example_config(monkeypatch):
    """Tests the config structure of Moonbeam Alpha network."""

    monkeypatch.setenv("OCEAN_NETWORK_URL", "https://rpc.testnet.moonbeam.network")
    config = ExampleConfig.get_config()

    assert config.chain_id == 1287
    assert config.network_url == "https://rpc.testnet.moonbeam.network"
    assert config.metadata_cache_uri == "https://aquarius.oceanprotocol.com"
    assert config.provider_url == "https://provider.moonbeamalpha.oceanprotocol.com"

    assert (
        config.__dict__["_sections"][SECTION_ETH_NETWORK][NETWORK_NAME]
        == "moonbeamalpha"
    )
    assert config.__dict__["_sections"][SECTION_ETH_NETWORK][
        NAME_BLOCK_CONFIRMATION_POLL_INTERVAL
    ] == str(6)
