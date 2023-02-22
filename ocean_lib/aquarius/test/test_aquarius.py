#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.aquarius.aquarius import Aquarius
from ocean_lib.assets.ddo import DDO
from ocean_lib.example_config import METADATA_CACHE_URI


@pytest.mark.unit
def test_init():
    """Tests initialisation of Aquarius objects."""
    aqua = Aquarius("http://172.15.0.5:5000/api/aquarius/assets")
    assert aqua.base_url == "http://172.15.0.5:5000/api/aquarius/assets"


@pytest.mark.integration
def test_aqua_functions_for_single_ddo(publisher_ocean, publisher_wallet, file1):
    """Tests against single-ddo functions of Aquarius."""
    aquarius = publisher_ocean.assets._aquarius

    _, _, ddo1 = publisher_ocean.assets.create_url_asset(
        "Sample asset", file1.url, {"from": publisher_wallet}
    )

    metadata1 = ddo1.metadata

    ddo2 = aquarius.wait_for_ddo(ddo1.did)
    assert ddo2.metadata == ddo1.metadata

    ddo3 = publisher_ocean.assets.resolve(ddo1.did)
    assert ddo3.did == ddo1.did, "Aquarius could not resolve the did."
    assert ddo3.did == ddo2.did, "Aquarius could not resolve the did."

    aqua_uri = publisher_ocean.config_dict.get("METADATA_CACHE_URI")
    ddo4 = Aquarius.get_instance(aqua_uri).get_ddo(ddo2.did)
    assert isinstance(ddo4, DDO)
    assert ddo4.did == ddo2.did, "Aquarius could not resolve the did."

    metadata2 = aquarius.get_ddo_metadata(ddo2.did)
    assert metadata2 == metadata1


@pytest.mark.unit
def test_invalid_search_query():
    """Tests query search with an invalid query."""
    aquarius = Aquarius.get_instance(METADATA_CACHE_URI)
    search_query = "not_a_dict"
    with pytest.raises(TypeError):
        aquarius.query_search(search_query=search_query)


@pytest.mark.unit
def test_empty_responses():
    aquarius = Aquarius.get_instance(METADATA_CACHE_URI)
    assert aquarius.get_ddo_metadata("inexistent_ddo") == {}
