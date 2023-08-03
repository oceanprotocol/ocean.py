#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json

import pytest
from web3 import Web3

from ocean_lib.ocean.ocean import Ocean


@pytest.mark.unit
def test_metadataCacheUri_config_key():
    """Tests that the metadata_cache_uri config property can be set using the
    `metadataCacheUri` config dict key when created via the Ocean __init__"""
    config_dict = {
        "NETWORK_NAME": "development",
        "METADATA_CACHE_URI": "http://v4.aquarius.oceanprotocol.com",
        "PROVIDER_URL": "http://172.15.0.4:8030",
        "DOWNLOADS_PATH": "consume-downloads",
        "ADDRESS_FILE": "~/.ocean/ocean-contracts/artifacts/address.json",
        "CHAIN_ID": 8996,
        "web3_instance": Web3(),
    }
    ocean_instance = Ocean(config_dict=config_dict)
    assert (
        "http://v4.aquarius.oceanprotocol.com"
        == ocean_instance.config_dict["METADATA_CACHE_URI"]
    )


@pytest.mark.unit
def test_incomplete():
    """Tests that the metadata_cache_uri config property can be set using the
    `metadataCacheUri` config dict key when created via the Ocean __init__"""
    config_dict = {
        "METADATA_CACHE_URI": "http://ItWorked.com",
    }

    with pytest.raises(Exception) as exception_info:
        Ocean(config_dict=config_dict)

    exception_response = json.loads(exception_info.value.args[0])
    assert exception_response["NETWORK_NAME"] == "required"
