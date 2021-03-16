#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from ocean_lib.config import Config
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
from tests.resources.ddo_helpers import get_resource_path


def test_set_config():
    """Tests that a custom config can be set on the ConfigProvider."""
    config = "foo config"
    ConfigProvider.set_config(config)

    assert ConfigProvider.get_config() == "foo config"


def test_metadataCacheUri_version():
    """Tests that the Aquarius URL can use the custom metadataCacheUri key."""
    config_dict = {"metadataCacheUri": "http://ItWorked.com", "network": "rinkeby"}
    ocean_instance = Ocean(config=config_dict)
    assert "http://ItWorked.com" == ocean_instance.config.aquarius_url


def test_metadataStoreUri_version():
    """Tests that the Aquarius URL can fallback on the custom metadataStoreUri key."""
    config_dict = {"metadataStoreUri": "http://ItWorked.com", "network": "rinkeby"}
    ocean_instance = Ocean(config=config_dict)
    assert "http://ItWorked.com" == ocean_instance.config.aquarius_url


def test_config_from_filename():
    """Tests that a Config object can be set from a filename."""
    config_file_name = get_resource_path("config", "test_config.ini")
    config = Config(filename=config_file_name)

    assert config.aquarius_url == "https://custom-aqua.url"
    assert config.artifacts_path is not None
    assert config.metadata_store_url == config.aquarius_url
    assert config.provider_address == "0x00bd138abd70e2f00903268f3db08f2d25677c9e"
    assert isinstance(config.gas_limit, int)


def test_config_from_text():
    """Tests that a Config object can be set from raw text."""
    config_text = """
        [resources]
        aquarius.url = https://another-aqua.url
    """
    config = Config(text=config_text)
    assert config.aquarius_url == "https://another-aqua.url"


def test_network_config():
    assert (
        "ganache.infura.io"
        in ExampleConfig.get_network_config("ganache")["eth-network"]["network"]
    )
