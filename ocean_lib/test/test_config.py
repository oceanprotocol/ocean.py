#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.config import (
    NAME_ADDRESS_FILE,
    NAME_AQUARIUS_URL,
    NAME_METADATA_CACHE_URI,
    Config,
    deprecated_environ_names,
    environ_names_and_sections,
)
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import GANACHE_URL


@pytest.mark.unit
def test_metadataCacheUri_config_key():
    """Tests that the metadata_cache_uri config property can be set using the
    `metadataCacheUri` config dict key when created via the Ocean __init__"""
    config_dict = {
        "METADATA_CACHE_URI": "http://ItWorked.com",
        "OCEAN_NETWORK_URL": GANACHE_URL,
    }
    ocean_instance = Ocean(config_dict=config_dict)
    assert "http://ItWorked.com" == ocean_instance.config_dict["METADATA_CACHE_URI"]


@pytest.mark.unit
def test_metadata_cache_uri_set_via_config_options(caplog):
    """Tests the metadata_cache_uri property fallback logic when set via a config dict"""
    config_dict = {"resources": {"metadata_cache_uri": "https://custom-aqua.uri"}}
    config = Config(options_dict=config_dict)
    assert config.metadata_cache_uri == "https://custom-aqua.uri"

    config_dict = {
        "resources": {
            "metadata_cache_uri": "https://custom-aqua.uri",
            "aquarius.url": "https://another-aqua.url",
        }
    }
    with pytest.raises(ValueError):
        Config(options_dict=config_dict)

    config_dict = {"resources": {"aquarius.url": "https://another-aqua.url"}}
    config = Config(options_dict=config_dict)
    assert config.metadata_cache_uri == "https://another-aqua.url"
    assert (
        "Config: resources.aquarius.url option is deprecated. "
        "Use resources.metadata_cache_uri instead." in caplog.text
    )


@pytest.mark.unit
def test_metadata_cache_uri_set_via_env_vars(monkeypatch, caplog):
    """Tests the metadata_cache_uri property fallback logic when set via an environment variable"""
    ENV_METADATA_CACHE_URI = environ_names_and_sections[NAME_METADATA_CACHE_URI][0]
    ENV_AQUARIUS_URL = deprecated_environ_names[NAME_AQUARIUS_URL][0]

    monkeypatch.delenv(ENV_METADATA_CACHE_URI, raising=False)
    monkeypatch.delenv(ENV_AQUARIUS_URL, raising=False)
    config = Config()
    metadata_cache_uri = config.metadata_cache_uri
    assert metadata_cache_uri == "http://172.15.0.5:5000"

    monkeypatch.setenv(ENV_METADATA_CACHE_URI, "https://custom-aqua.uri")
    config = Config()
    assert config.metadata_cache_uri == "https://custom-aqua.uri"

    monkeypatch.setenv(ENV_AQUARIUS_URL, "https://another-aqua.url")
    with pytest.raises(ValueError):
        Config()

    monkeypatch.delenv(ENV_METADATA_CACHE_URI)
    config = Config()
    assert config.metadata_cache_uri == "https://another-aqua.url"
    assert (
        "Config: AQUARIUS_URL envvar is deprecated. Use METADATA_CACHE_URI instead."
        in caplog.text
    )


@pytest.mark.unit
def test_address_file(monkeypatch):
    """Tests the Config.address_file property."""
    ENV_ADDRESS_FILE = environ_names_and_sections[NAME_ADDRESS_FILE][0]
    monkeypatch.delenv(ENV_ADDRESS_FILE)

    # Test when address.file config option is set
    config_text = """
        [eth-network]
        address.file = custom/address.json
    """
    config = Config(text=config_text)
    assert config.address_file.endswith("custom/address.json")

    # Test when ADDRESS_FILE envvar is set
    monkeypatch.setenv(ENV_ADDRESS_FILE, "another/custom/address.json")
    config = Config()
    assert config.address_file.endswith("another/custom/address.json")

    # Test when both ADDRESS_FILE envvar and address.file config option are set
    config = Config(text=config_text)
    assert config.address_file.endswith("another/custom/address.json")
