#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import os

import pytest
from ocean_lib.config import (
    NAME_AQUARIUS_URL,
    NAME_METADATA_CACHE_URI,
    Config,
    deprecated_environ_names,
    environ_names,
)


def test_metadata_cache_uri_property(monkeypatch):
    """Tests the 'metadata_cache_uri' property."""
    ENV_METADATA_CACHE_URI = environ_names[NAME_METADATA_CACHE_URI][0]
    ENV_AQUARIUS_URL = deprecated_environ_names[NAME_AQUARIUS_URL][0]

    # Validate defaults
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


def test_load_environ():
    """Tests the fallback to AQUARIUS_URL env var."""
    config = Config()
    temp_config = Config()
    temp_config.__dict__ = copy.deepcopy(config.__dict__)
    temp_config.__dict__["_sections"]["eth-network"][
        "aquarius.url"
    ] = "METADATA_CACHE_URI"
    assert config.__dict__["_sections"]["eth-network"]["aquarius.url"] == "AQUARIUS_URL"
    assert (
        temp_config.__dict__["_sections"]["eth-network"]["aquarius.url"]
        != "AQUARIUS_URL"
    )
    assert os.getenv(
        temp_config.__dict__["_sections"]["eth-network"]["aquarius.url"]
    ) == os.getenv(config.__dict__["_sections"]["eth-network"]["aquarius.url"])
