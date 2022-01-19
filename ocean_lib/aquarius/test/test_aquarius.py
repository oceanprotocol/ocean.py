#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.agreements.file_objects import FilesTypeFactory
from ocean_lib.aquarius.aquarius import Aquarius
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.models_structures import ErcCreateData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import get_address_of_type


def test_init():
    """Tests initialisation of Aquarius objects."""
    aqua = Aquarius("http://something/api/aquarius/assets")
    assert (
        aqua.base_url == "http://something/api/aquarius/assets"
    ), "Different URL from the specified one."


def test_aqua_functions_for_single_ddo(
    publisher_ocean_instance, aquarius_instance, publisher_wallet, config
):
    """Tests against single-ddo functions of Aquarius."""
    erc20_data = ErcCreateData(
        template_index=1,
        strings=["Datatoken 1", "DT1"],
        addresses=[
            publisher_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
            get_address_of_type(config, "Ocean"),
        ],
        uints=[to_wei("0.5"), 0],
        bytess=[b""],
    )
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }

    data_provider = DataServiceProvider
    file1_dict = {"type": "url", "url": "https://url.com/file1.csv", "method": "GET"}
    file1 = FilesTypeFactory(file1_dict)
    encrypt_response = data_provider.encrypt(
        [file1], "http://172.15.0.4:8030/api/services/encrypt"
    )
    encrypted_files = encrypt_response.content.decode("utf-8")

    ddo = publisher_ocean_instance.assets.create(
        metadata, publisher_wallet, encrypted_files, erc20_tokens_data=[erc20_data]
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


def test_invalid_search_query(aquarius_instance):
    """Tests query search with an invalid query."""
    search_query = "not_a_dict"
    with pytest.raises(TypeError):
        aquarius_instance.query_search(search_query=search_query)
