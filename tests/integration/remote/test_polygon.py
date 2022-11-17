#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import warnings

import pytest
from brownie.network import accounts, priority_fee

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.utils import connect_to_network

from .util import get_wallets, random_chars


@pytest.mark.integration
def test_ocean_tx__create_url_asset(tmp_path):
    """On Polygon, do the Ocean txs for create_url_asset(). Captures issue:https://github.com/oceanprotocol/ocean.py/issues/1007#issuecomment-1276286245"""
    # setup
    connect_to_network("polygon")
    config = _remote_config_polygon(tmp_path)
    ocean = Ocean(config)
    accounts.clear()
    (alice_wallet, _) = get_wallets(ocean)

    priority_fee("75 gwei")

    # Alice call create_url_asset
    # avoid "replacement transaction underpriced" error: make each tx diff't
    name = random_chars()
    url = "https://arweave.net/qctEbPb3CjvU8LmV3G_mynX74eCxo1domFQIlOBH1xU"
    try:  # it can get away with "insufficient funds" errors, but not others
        print("Call create_url_asset(), and wait for it to complete...")
        (_, datatoken, _) = ocean.assets.create_url_asset(
            name, url, alice_wallet, wait_for_aqua=False
        )
        assert isinstance(datatoken, Datatoken)

    except ValueError as error:
        if "insufficient funds" in str(error):
            warnings.warn(UserWarning("Warning: Insufficient Polygon MATIC"))
            return
        raise (error)

    print("Success")


def _remote_config_polygon(tmp_path):
    config = {
        "NETWORK_NAME": "polygon",
        "METADATA_CACHE_URI": "https://v4.aquarius.oceanprotocol.com",
        "PROVIDER_URL": "https://v4.provider.polygon.oceanprotocol.com",
        "DOWNLOADS_PATH": "consume-downloads",
    }

    return config
