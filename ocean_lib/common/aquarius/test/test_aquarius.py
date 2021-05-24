#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.common.aquarius.aquarius import Aquarius
from tests.resources.ddo_helpers import wait_for_ddo
from tests.resources.helper_functions import get_publisher_wallet


def test_init():
    """Tests initialisation of Aquarius objects."""
    aqua = Aquarius("http://something/api/v1/aquarius/assets")
    assert aqua.url == "http://something/api/v1/aquarius/assets/ddo"
    assert aqua.root_url == "http://something"


def test_aqua_functions_for_single_ddo(
    publisher_ocean_instance, metadata, aquarius_instance
):
    """Tests against single-ddo functions of Aquarius."""
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()

    ddo = publisher_ocean_instance.assets.create(metadata_copy, publisher)
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    aqua_metadata = aquarius_instance.get_asset_metadata(ddo.did)

    del aqua_metadata["main"]["datePublished"]
    assert aqua_metadata["main"] == ddo.metadata["main"]
    assert aqua_metadata["encryptedFiles"] == ddo.metadata["encryptedFiles"]

    res = aquarius_instance.get_asset_ddo(ddo.did)
    assert res.did == ddo.did

    res = aquarius_instance.text_search(ddo.did)
    assert len(res)


def test_aqua_function_for_multiple_ddos(aquarius_instance):
    """Tests against multiple-ddo functions of Aquarius."""
    assert aquarius_instance.list_assets()
    assert aquarius_instance.list_assets_ddo()


def test_metadata_invalid(aquarius_instance):
    """Tests metadata validation failure."""
    result, errors = aquarius_instance.validate_metadata(
        {"some_dict": "that is invalid"}
    )
    assert result is False
    assert errors[0]["message"] == "'main' is a required property"
