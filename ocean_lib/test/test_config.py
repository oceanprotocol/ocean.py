#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

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
