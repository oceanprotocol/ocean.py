#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.aquarius.aquarius import Aquarius
from tests.resources.ddo_helpers import wait_for_ddo


def test_init():
    """Tests initialisation of Aquarius objects."""
    aqua = Aquarius("http://something/api/aquarius/assets")
    assert (
        aqua.base_url == "http://something/api/aquarius/assets"
    ), "Different URL from the specified one."


def test_aqua_functions_for_single_ddo(
    publisher_ocean_instance, metadata, aquarius_instance, publisher_wallet
):
    """Tests against single-ddo functions of Aquarius."""
    metadata_copy = metadata.copy()

    ddo = publisher_ocean_instance.assets.create(metadata_copy, publisher_wallet)
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    aqua_metadata = aquarius_instance.get_asset_metadata(ddo.did)

    del aqua_metadata["main"]["datePublished"]
    assert aqua_metadata["main"] == ddo.metadata["main"]
    assert aqua_metadata["encryptedFiles"] == ddo.metadata["encryptedFiles"]

    res = aquarius_instance.get_asset_ddo(ddo.did)
    assert res.did == ddo.did, "Aquarius could not resolve the did."


def test_invalid_search_query(aquarius_instance):
    """Tests query search with an invalid query."""
    search_query = "not_a_dict"
    with pytest.raises(TypeError):
        aquarius_instance.query_search(search_query=search_query)
