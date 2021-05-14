#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_resolver import resolve_asset
from tests.resources.ddo_helpers import wait_for_ddo
from tests.resources.helper_functions import get_publisher_wallet


def test_resolve_asset(publisher_ocean_instance, metadata):
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()

    asset = publisher_ocean_instance.assets.create(metadata_copy, publisher)
    wait_for_ddo(publisher_ocean_instance, asset.did)
    assert asset is not None, "The asset is not cached."

    resolved_asset = resolve_asset(
        asset.did,
        publisher_ocean_instance.config.metadata_cache_uri,
        asset.data_token_address,
    )
    assert isinstance(asset, Asset), "The asset does not have Asset instance."
    assert isinstance(resolved_asset, Asset), "The asset does not have Asset instance."
    assert (
        resolved_asset.did == asset.did
    ), "Resolve asset function call is unsuccessful."


def test_bad_resolved_asset(publisher_ocean_instance, metadata):
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()

    asset = publisher_ocean_instance.assets.create(metadata_copy, publisher)
    wait_for_ddo(publisher_ocean_instance, asset.did)
    assert asset is not None, "The asset is not cached."

    with pytest.raises(AssertionError) as err:
        resolve_asset(asset.did)
    assert (
        err.value.args[0] == "One of metadata_cache_uri or token_address is required."
    )
