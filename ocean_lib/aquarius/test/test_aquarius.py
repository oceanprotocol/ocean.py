#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.aquarius.aquarius import Aquarius
from ocean_lib.ddo.ddo import DDO
from ocean_lib.web3_internal.constants import ZERO_ADDRESS


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
        "name": "Sample DDO",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }

    OCEAN_addr = publisher_ocean_instance.OCEAN_address
    ddo1 = publisher_ocean_instance.ddo.create(
        metadata=metadata1,
        publisher_wallet=publisher_wallet,
        files=[file1],
        datatoken_templates=[1],
        datatoken_names=["Datatoken 1"],
        datatoken_symbols=["DT1"],
        datatoken_minters=[publisher_wallet.address],
        datatoken_fee_managers=[publisher_wallet.address],
        datatoken_publish_market_order_fee_addresses=[ZERO_ADDRESS],
        datatoken_publish_market_order_fee_tokens=[OCEAN_addr],
        datatoken_publish_market_order_fee_amounts=[0],
        datatoken_bytess=[[b""]],
    )

    ddo2 = aquarius_instance.wait_for_ddo(ddo1.did)
    assert ddo2.metadata == ddo1.metadata

    ddo3 = publisher_ocean_instance.ddo.resolve(ddo1.did)
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
