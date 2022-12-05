#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.aquarius.aquarius import Aquarius
from ocean_lib.assets.ddo import DDO
from ocean_lib.ocean.ocean_assets import DatatokenArguments


@pytest.mark.unit
def test_init():
    """Tests initialisation of Aquarius objects."""
    aqua = Aquarius("http://172.15.0.5:5000/api/aquarius/assets")
    assert aqua.base_url == "http://172.15.0.5:5000/api/aquarius/assets"


@pytest.mark.integration
def test_aqua_functions_for_single_ddo(
    publisher_ocean_instance, aquarius_instance, publisher_wallet, config, file1
):
    """Tests against single-ddo functions of Aquarius."""
    metadata1 = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }

    ddo1 = publisher_ocean_instance.assets.create(
        metadata=metadata1,
        publisher_wallet=publisher_wallet,
        datatoken_arguments=[
            DatatokenArguments(
                template_index=1, name="Datatoken 1", symbol="DT1", files=[file1]
            )
        ],
    )

    ddo2 = aquarius_instance.wait_for_ddo(ddo1.did)
    assert ddo2.metadata == ddo1.metadata

    ddo3 = publisher_ocean_instance.assets.resolve(ddo1.did)
    assert ddo3.did == ddo1.did, "Aquarius could not resolve the did."
    assert ddo3.did == ddo2.did, "Aquarius could not resolve the did."

    aqua_uri = publisher_ocean_instance.config_dict.get("METADATA_CACHE_URI")
    ddo4 = Aquarius.get_instance(aqua_uri).get_ddo(ddo2.did)
    assert isinstance(ddo4, DDO)
    assert ddo4.did == ddo2.did, "Aquarius could not resolve the did."

    metadata2 = aquarius_instance.get_ddo_metadata(ddo2.did)
    assert metadata2 == metadata1


@pytest.mark.unit
def test_invalid_search_query(aquarius_instance):
    """Tests query search with an invalid query."""
    search_query = "not_a_dict"
    with pytest.raises(TypeError):
        aquarius_instance.query_search(search_query=search_query)


@pytest.mark.unit
def test_empty_responses(aquarius_instance):
    assert aquarius_instance.get_ddo_metadata("inexistent_ddo") == {}
