#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json

import pytest

from ocean_lib.ocean.ocean import Ocean


@pytest.mark.unit
def test_metadataCacheUri_config_key():
    """Tests that the metadata_cache_uri config property can be set using the
    `metadataCacheUri` config dict key when created via the Ocean __init__"""
    config_dict = {
        "NETWORK_NAME": "development",
        "METADATA_CACHE_URI": "http://ItWorked.com",
        "BLOCK_CONFIRMATIONS": 0,
        "TRANSACTION_TIMEOUT": 10 * 60,  # 10 minutes
        "PROVIDER_URL": "http://172.15.0.4:8030",
        "DOWNLOADS_PATH": "consume-downloads",
        "ADDRESS_FILE": "~/.ocean/ocean-contracts/artifacts/address.json",
    }
    ocean_instance = Ocean(config_dict=config_dict)
    assert "http://ItWorked.com" == ocean_instance.config_dict["METADATA_CACHE_URI"]


@pytest.mark.unit
def test_incomplete():
    """Tests that the metadata_cache_uri config property can be set using the
    `metadataCacheUri` config dict key when created via the Ocean __init__"""
    config_dict = {
        "METADATA_CACHE_URI": "http://ItWorked.com",
        "TRANSACTION_TIMEOUT": "some string",
    }

    with pytest.raises(Exception) as exception_info:
        Ocean(config_dict=config_dict)

    exception_response = json.loads(exception_info.value.args[0])
    assert exception_response["NETWORK_NAME"] == "required"
    assert exception_response["TRANSACTION_TIMEOUT"] == "must be int"
