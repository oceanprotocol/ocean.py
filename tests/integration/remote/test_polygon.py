#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import warnings

import pytest

from .util import get_wallets, random_chars
from ocean_lib.ocean.ocean import Ocean


@pytest.mark.integration
def test_ocean_tx__create_url_asset(tmp_path):
    """On Mumbai, do the Ocean txs for create_url_asset(). Captures issue:https://github.com/oceanprotocol/ocean.py/issues/1007#issuecomment-1276286245"""

    # setup
    config = _remote_config_polygon(tmp_path)
    ocean = Ocean(config)
    (alice_wallet, _) = get_wallets(ocean)

    # Alice call create_url_asset
    # avoid "replacement transaction underpriced" error: make each tx diff't
    name = random_chars()
    url = "https://arweave.net/qctEbPb3CjvU8LmV3G_mynX74eCxo1domFQIlOBH1xU"
    try:  # it can get away with "insufficient funds" errors, but not others
        print("Call create_url_asset(), and wait for it to complete...")
        asset = ocean.assets.create_url_asset(name, url, alice_wallet)

    except ValueError as error:
        if "insufficient funds" in str(error):
            warnings.warn(UserWarning("Warning: Insufficient test MATIC"))
            return
        raise (error)

    assert asset is not None
    datatoken_address = asset.datatokens[0]["address"]
    datatoken = ocean.get_datatoken(datatoken_address)
    assert datatoken is not None
    print("Success")


def _remote_config_polygon(tmp_path):
    config = {
        "RPC_URL": "https://polygon-rpc.com",
        "BLOCK_CONFIRMATIONS": 0,
        "TRANSACTION_TIMEOUT": 60,
        "METADATA_CACHE_URI": "https://v4.aquarius.oceanprotocol.com",
        "PROVIDER_URL": "https://v4.provider.polygon.oceanprotocol.com",
        "DOWNLOADS_PATH": "consume-downloads",
    }

    # -ensure config is truly remote
    assert "polygon" in config["RPC_URL"]
    assert "oceanprotocol.com" in config["METADATA_CACHE_URI"]
    assert "oceanprotocol.com" in config["PROVIDER_URL"]

    return config
