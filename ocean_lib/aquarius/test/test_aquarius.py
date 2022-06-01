#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.aquarius.aquarius import Aquarius
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.web3_internal.constants import ZERO_ADDRESS


@pytest.mark.unit
def test_init():
    """Tests initialisation of Aquarius objects."""
    aqua = Aquarius("http://something/api/aquarius/assets")
    assert (
        aqua.base_url == "http://something/api/aquarius/assets"
    ), "Different URL from the specified one."


@pytest.mark.integration
def test_aqua_functions_for_single_ddo(
    publisher_ocean_instance, aquarius_instance, publisher_wallet, config, file1
):
    """Tests against single-ddo functions of Aquarius."""
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }

    encrypted_files = publisher_ocean_instance.assets.encrypt_files([file1])

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        datatoken_templates=[1],
        datatoken_names=["Datatoken 1"],
        datatoken_symbols=["DT1"],
        datatoken_minters=[publisher_wallet.address],
        datatoken_fee_managers=[publisher_wallet.address],
        datatoken_publish_market_order_fee_addresses=[ZERO_ADDRESS],
        datatoken_publish_market_order_fee_tokens=[
            publisher_ocean_instance.OCEAN_address
        ],
        datatoken_publish_market_order_fee_amounts=[0],
        datatoken_bytess=[[b""]],
    )

    asset = aquarius_instance.wait_for_asset(ddo.did)

    assert asset.metadata == ddo.metadata

    res = publisher_ocean_instance.assets.resolve(ddo.did)
    assert res.did == ddo.did, "Aquarius could not resolve the did."
    assert res.did == asset.did, "Aquarius could not resolve the did."

    resolved_asset_from_metadata_cache_uri = resolve_asset(
        asset.did, metadata_cache_uri=publisher_ocean_instance.config.metadata_cache_uri
    )
    assert isinstance(
        resolved_asset_from_metadata_cache_uri, Asset
    ), "The resolved asset is not an instance of Asset."
    assert (
        resolved_asset_from_metadata_cache_uri.did == asset.did
    ), "Resolve asset function call is unsuccessful."

    chain_metadata = aquarius_instance.get_asset_metadata(asset.did)
    assert metadata == chain_metadata


@pytest.mark.unit
def test_invalid_search_query(aquarius_instance):
    """Tests query search with an invalid query."""
    search_query = "not_a_dict"
    with pytest.raises(TypeError):
        aquarius_instance.query_search(search_query=search_query)


@pytest.mark.unit
def test_empty_responses(aquarius_instance):
    assert aquarius_instance.get_asset_metadata("inexistent_ddo") == {}
