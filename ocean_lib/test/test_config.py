#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from ocean_lib.config import Config
import copy


def test_metadata_cache_uri_property():
    """Tests if the URL of the aquarius matches 'metadata_cache_uri' property."""
    config = Config()
    metadata_cache_uri = config.metadata_cache_uri
    assert metadata_cache_uri
    assert metadata_cache_uri.startswith("https://aquarius")
    assert metadata_cache_uri == "https://aquarius.marketplace.oceanprotocol.com"


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
