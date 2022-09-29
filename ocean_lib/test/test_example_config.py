#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.example_config import (
    DEFAULT_METADATA_CACHE_URI,
    DEFAULT_PROVIDER_URL,
    METADATA_CACHE_URI,
    ExampleConfig,
    get_config_dict,
)
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.ocean.util import get_contracts_addresses
from tests.resources.helper_functions import get_address_of_type


@pytest.mark.unit
def test_ganache_example_config():
    """Tests the config structure of ganache network."""

    config = ExampleConfig.get_config()

    assert config["CHAIN_ID"] == 8996
    assert config["RPC_URL"] == "http://127.0.0.1:8545"
    assert config["METADATA_CACHE_URI"] == DEFAULT_METADATA_CACHE_URI
    assert config["PROVIDER_URL"] == DEFAULT_PROVIDER_URL
    assert config["BLOCK_CONFIRMATIONS"] == 0


@pytest.mark.unit
def test_polygon_example_config():
    """Tests the config structure of Polygon network."""

    config = ExampleConfig.get_config("https://polygon-rpc.com")

    assert config["CHAIN_ID"] == 137
    assert config["RPC_URL"] == "https://polygon-rpc.com"
    assert config["METADATA_CACHE_URI"] == METADATA_CACHE_URI
    assert config["PROVIDER_URL"] == "https://v4.provider.polygon.oceanprotocol.com"
    assert config["BLOCK_CONFIRMATIONS"] == 15


@pytest.mark.unit
def test_bsc_example_config():
    """Tests the config structure of BSC network."""

    config = ExampleConfig.get_config("https://bsc-dataseed.binance.org")

    assert config["CHAIN_ID"] == 56
    assert config["RPC_URL"] == "https://bsc-dataseed.binance.org"
    assert config["METADATA_CACHE_URI"] == METADATA_CACHE_URI
    assert config["PROVIDER_URL"] == "https://v4.provider.bsc.oceanprotocol.com"
    assert config["BLOCK_CONFIRMATIONS"] == 1


@pytest.mark.unit
def test_moonbeam_alpha_example_config(monkeypatch):
    """Tests the config structure of Moonbeam Alpha network."""

    config = ExampleConfig.get_config("https://rpc.testnet.moonbeam.network")

    assert config["CHAIN_ID"] == 1287
    assert config["RPC_URL"] == "https://rpc.testnet.moonbeam.network"
    assert config["METADATA_CACHE_URI"] == METADATA_CACHE_URI
    assert config["PROVIDER_URL"] == "https://v4.provider.moonbase.oceanprotocol.com"
    assert config["BLOCK_CONFIRMATIONS"] == 3


@pytest.mark.unit
def test_get_address_of_type(monkeypatch):
    config = ExampleConfig.get_config("https://polygon-rpc.com")

    data_nft_factory = get_address_of_type(config, DataNFTFactoryContract.CONTRACT_NAME)
    addresses = get_contracts_addresses(config)
    assert addresses[DataNFTFactoryContract.CONTRACT_NAME] == data_nft_factory
