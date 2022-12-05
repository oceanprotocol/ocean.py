#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.example_config import (
    DEFAULT_METADATA_CACHE_URI,
    DEFAULT_PROVIDER_URL,
    METADATA_CACHE_URI,
    get_config_dict,
)
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.contract_utils import get_contracts_addresses


@pytest.mark.unit
def test_ganache_example_config():
    """Tests the config structure of ganache network."""

    config = get_config_dict()

    assert config["METADATA_CACHE_URI"] == DEFAULT_METADATA_CACHE_URI
    assert config["PROVIDER_URL"] == DEFAULT_PROVIDER_URL


@pytest.mark.unit
def test_polygon_example_config():
    """Tests the config structure of Polygon network."""

    config = get_config_dict("polygon")

    assert config["METADATA_CACHE_URI"] == METADATA_CACHE_URI
    assert config["PROVIDER_URL"] == "https://v4.provider.polygon.oceanprotocol.com"


@pytest.mark.unit
def test_bsc_example_config():
    """Tests the config structure of BSC network."""

    config = get_config_dict("bsc")

    assert config["METADATA_CACHE_URI"] == METADATA_CACHE_URI
    assert config["PROVIDER_URL"] == "https://v4.provider.bsc.oceanprotocol.com"


@pytest.mark.unit
def test_moonbeam_alpha_example_config(monkeypatch):
    """Tests the config structure of Moonbeam Alpha network."""

    config = get_config_dict("moonbase")

    assert config["METADATA_CACHE_URI"] == METADATA_CACHE_URI
    assert config["PROVIDER_URL"] == "https://v4.provider.moonbase.oceanprotocol.com"


@pytest.mark.unit
def test_get_address_of_type(monkeypatch):
    config = get_config_dict("polygon")

    data_nft_factory = get_address_of_type(config, DataNFTFactoryContract.CONTRACT_NAME)
    addresses = get_contracts_addresses(config)
    assert addresses[DataNFTFactoryContract.CONTRACT_NAME] == data_nft_factory
