#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import os.path

import pytest
from ocean_lib.config import Config
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.env_constants import ENV_CONFIG_FILE
from ocean_lib.ocean.ocean import Ocean
from tests.resources.ddo_helpers import get_resource_path


def test_set_config():
    """Tests that a custom config can be set on the ConfigProvider."""
    config = "foo config"
    ConfigProvider.set_config(config)

    assert ConfigProvider.get_config() == "foo config"


def test_metadataStoreUri_version():
    """Tests that the Aquarius URL can use the custom metadataStoreUri key."""
    config_dict = {"metadataStoreUri": "http://ItWorked.com", "network": "ganache"}
    ocean_instance = Ocean(config=config_dict)
    assert "http://ItWorked.com" == ocean_instance.config.metadata_cache_uri


def test_metadataCacheUri_version():
    """Tests that the Aquarius URL can use the custom metadataCacheUri key."""
    config_dict = {"metadataCacheUri": "http://ItWorked.com", "network": "ganache"}
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
    assert config.artifacts_path is not None
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
        metadata_cache.uri = https://another-aqua.url
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


def test_network_config():
    assert (
        "ganache.infura.io"
        in ExampleConfig.get_network_config("ganache")["eth-network"]["network"]
    )
