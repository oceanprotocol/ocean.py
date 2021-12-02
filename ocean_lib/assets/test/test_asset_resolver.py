#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json

import pytest
from ocean_lib.assets.asset import V3Asset
from ocean_lib.assets.asset_resolver import resolve_asset
from tests.resources.ddo_helpers import wait_for_ddo


def test_resolve_asset(publisher_ocean_instance, metadata, publisher_wallet):
    metadata_copy = metadata.copy()
    blob = json.dumps(
        {"t": 1, "url": publisher_ocean_instance.config.metadata_cache_uri}
    )

    asset = publisher_ocean_instance.assets.create(
        metadata_copy, publisher_wallet, dt_blob=blob
    )
    wait_for_ddo(publisher_ocean_instance, asset.did)
    assert asset is not None, "The asset is not cached."
    assert isinstance(asset, V3Asset), "The asset does not have Asset instance."

    # resolve asset from metadata_cache_uri
    resolved_asset_from_metadata_cache_uri = resolve_asset(
        asset.did, metadata_cache_uri=publisher_ocean_instance.config.metadata_cache_uri
    )
    assert isinstance(
        resolved_asset_from_metadata_cache_uri, V3Asset
    ), "The resolved asset is not an instance of Asset."
    assert (
        resolved_asset_from_metadata_cache_uri.did == asset.did
    ), "Resolve asset function call is unsuccessful."


def test_bad_resolved_asset():
    with pytest.raises(AssertionError) as err:
        resolve_asset("0x1")
    assert err.value.args[0] == "metadata_cache_uri is required."
