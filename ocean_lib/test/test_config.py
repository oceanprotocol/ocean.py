#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os.path

import pytest
from ocean_lib.config import (
    NAME_ADDRESS_FILE,
    NAME_AQUARIUS_URL,
    NAME_METADATA_CACHE_URI,
    Config,
    deprecated_environ_names,
    environ_names_and_sections,
)
from ocean_lib.ocean.util import GANACHE_URL
from ocean_lib.ocean.env_constants import ENV_CONFIG_FILE
from ocean_lib.ocean.ocean import Ocean
from tests.resources.ddo_helpers import get_resource_path


def test_metadataStoreUri_config_key():
    """Tests that the metadata_cache_uri config property can be set using the
    `metadataStoreUri` config dict key when created via the Ocean __init__"""
    config_dict = {"metadataStoreUri": "http://ItWorked.com", "network": GANACHE_URL}
    ocean_instance = Ocean(config=config_dict)
    assert "http://ItWorked.com" == ocean_instance.config.metadata_cache_uri


def test_metadataCacheUri_config_key():
    """Tests that the metadata_cache_uri config property can be set using the
    `metadataCacheUri` config dict key when created via the Ocean __init__"""
    config_dict = {"metadataCacheUri": "http://ItWorked.com", "network": GANACHE_URL}
    ocean_instance = Ocean(config=config_dict)
    assert "http://ItWorked.com" == ocean_instance.config.metadata_cache_uri


def test_config_filename_given_file_doesnt_exist():
    """Test creating a Config object.
    Setup: filename given, file doesn't exist
    Expect: complain
    """
    config_file_name = "i_dont_exist.ini"
    assert not os.path.exists(config_file_name)

    with pytest.raises(Exception):
        Config(filename=config_file_name)


def test_config_filename_given_file_exists_malformed_content(monkeypatch, tmp_path):
    """Test creating a Config object.
    Setup: filename given, file exists, malformed content
    Expect: complain
    """
    config_file_name = _create_malformed_conffile(tmp_path)

    monkeypatch.setenv(ENV_CONFIG_FILE, config_file_name)
    with pytest.raises(Exception):
        Config()


def test_config_filename_given_file_exists_wellformed_content():
    """Test creating a Config object.
    Setup: filename given, file exists, content is well-formed
    Expect: success
    """
    config_file_name = get_resource_path("config", "test_config.ini")
    config = Config(filename=config_file_name)

    assert config.metadata_cache_uri == "https://custom-aqua.url"
    assert config.provider_address == "0x00bd138abd70e2f00903268f3db08f2d25677c9e"
    assert isinstance(config.gas_limit, int)


def test_config_filename_not_given_envvar_is_empty(monkeypatch):
    """Test creating a Config object.
    Setup: filename not given, envvar is empty
    Expect: complain
    """
    monkeypatch.delenv(ENV_CONFIG_FILE)
    with pytest.raises(ValueError):
        Config()


def test_config_filename_not_given_file_doesnt_exist(monkeypatch):
    """Test creating a Config object.
    Setup: filename not given, default file doesn't exist
    Expect: complain
    """
    config_file_name = "i_dont_exist.ini"
    assert not os.path.exists(config_file_name)

    monkeypatch.setenv(ENV_CONFIG_FILE, config_file_name)
    with pytest.raises(Exception):
        Config()


def test_config_filename_not_given_file_exists_malformed_content(monkeypatch, tmp_path):
    """Test creating a Config object.
    Setup: no filename given, default file exists, content is malformed
    Expect: complain
    """
    config_file_name = _create_malformed_conffile(tmp_path)

    monkeypatch.setenv(ENV_CONFIG_FILE, config_file_name)
    with pytest.raises(Exception):
        Config()


def test_config_filename_not_given_file_exists_wellformed_content(monkeypatch):
    """Test creating a Config object.
    Setup: filename not given, default file exists, content is well-formed
    Expect: success. Uses config file at ENV_CONFIG_FILE.
    """
    config_file_name = get_resource_path("config", "test_config.ini")
    monkeypatch.setenv(ENV_CONFIG_FILE, str(config_file_name))

    config = Config()

    assert config.provider_address == "0x00bd138abd70e2f00903268f3db08f2d25677c9e"


def _create_malformed_conffile(tmp_path):
    """Helper function to some tests above. In: pytest tmp_pth. Out: str"""
    d = tmp_path / "subdir"
    d.mkdir()
    config_file = d / "test_config_bad.ini"
    config_file.write_text("Malformed content inside config file")
    config_file_name = str(config_file)
    return config_file_name


def test_config_from_text_wellformed_content():
    """Tests creating Config object.
    Setup: from raw text, content is well-formed
    Expect: success
    """
    config_text = """
        [resources]
        metadata_cache_uri = https://another-aqua.url
    """
    config = Config(text=config_text)
    assert config.metadata_cache_uri == "https://another-aqua.url"


def test_config_from_text_malformed_content():
    """Tests creating Config object.
    Setup: from raw text, content is malformed
    Expect: complain
    """
    config_text = "Malformed content inside config text"
    with pytest.raises(Exception):
        Config(text=config_text)


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


def test_metadata_cache_uri_set_via_env_vars(monkeypatch, caplog):
    """Tests the metadata_cache_uri property fallback logic when set via an environment variable"""
    ENV_METADATA_CACHE_URI = environ_names_and_sections[NAME_METADATA_CACHE_URI][0]
    ENV_AQUARIUS_URL = deprecated_environ_names[NAME_AQUARIUS_URL][0]

    monkeypatch.delenv(ENV_METADATA_CACHE_URI, raising=False)
    monkeypatch.delenv(ENV_AQUARIUS_URL, raising=False)
    config = Config()
    metadata_cache_uri = config.metadata_cache_uri
    assert metadata_cache_uri == "https://aquarius.marketplace.oceanprotocol.com"

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


def test_address_file(monkeypatch):
    """Tests the Config.address_file property."""

    # Test default value when ADDRESS_FILE envvar and address.file config option not set
    ENV_ADDRESS_FILE = environ_names_and_sections[NAME_ADDRESS_FILE][0]
    monkeypatch.delenv(ENV_ADDRESS_FILE)
    config_text_empty = ""
    config = Config(text=config_text_empty)
    assert config.address_file.endswith("site-packages/artifacts/address.json")

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
