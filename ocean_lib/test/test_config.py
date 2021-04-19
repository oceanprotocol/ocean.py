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


def test_metadata_cache_uri_property(monkeypatch):
    """Tests the 'metadata_cache_uri' property."""
    ENV_METADATA_CACHE_URI = environ_names_and_sections[NAME_METADATA_CACHE_URI][0]
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
