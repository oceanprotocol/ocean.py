#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.config import (
    NAME_AQUARIUS_URL,
    NAME_METADATA_CACHE_URI,
    Config,
    deprecated_environ_names,
    environ_names_and_sections,
)


def test_metadata_cache_uri_set_via_config_options(caplog):
    """Tests the metadata_cache_uri property fallback logic when set via a config dict"""
    config_dict = {"resources": {"metadata_cache.uri": "https://custom-aqua.uri"}}
    config = Config(options_dict=config_dict)
    assert config.metadata_cache_uri == "https://custom-aqua.uri"

    config_dict = {
        "resources": {
            "metadata_cache.uri": "https://custom-aqua.uri",
            "aquarius.url": "https://another-aqua.url",
        }
    }
    with pytest.raises(ValueError):
        config = Config(options_dict=config_dict)

    config_dict = {"resources": {"aquarius.url": "https://another-aqua.url"}}
    config = Config(options_dict=config_dict)
    assert config.metadata_cache_uri == "https://another-aqua.url"
    assert (
        "Config: resources.aquarius.url option is deprecated. "
        "Use resources.metadata_cache.uri instead." in caplog.text
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
        config = Config()

    monkeypatch.delenv(ENV_METADATA_CACHE_URI)
    config = Config()
    assert config.metadata_cache_uri == "https://another-aqua.url"
    assert (
        "Config: AQUARIUS_URL envvar is deprecated. Use METADATA_CACHE_URI instead."
        in caplog.text
    )
