#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import shutil

import pytest

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.datatoken_base import DatatokenArguments, DatatokenBase
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.ocean.util import to_wei
from ocean_lib.structures.file_objects import GraphqlQuery
from tests.resources.ddo_helpers import get_first_service_by_type


@pytest.mark.integration
def test_consume_simple_graphql_query(
    config: dict,
    publisher_wallet,
    consumer_wallet,
):
    data_provider = DataServiceProvider
    ocean = Ocean(config)
    url = "http://172.15.0.15:8030/graphql"
    query = """
        query{
            indexingStatuses{
                subgraph
                chains
                node
            }
        }
        """

    data_nft, dt, ddo = ocean.assets.create_graphql_asset(
        "Data NFTs in Ocean", url, query, {"from": publisher_wallet}
    )

    assert ddo, "The ddo is not created."
    assert ddo.nft["address"] == data_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "Data NFTs in Ocean: DT1"

    service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)

    # Mint 50 datatokens in consumer wallet from publisher. Max cap = 100
    dt.mint(
        consumer_wallet.address,
        to_wei(50),
        {"from": publisher_wallet},
    )

    # Initialize service
    response = data_provider.initialize(
        did=ddo.did, service=service, consumer_address=consumer_wallet.address
    )
    assert response
    assert response.status_code == 200
    assert response.json()["providerFee"]
    provider_fees = response.json()["providerFee"]

    # Start order for consumer
    receipt = dt.start_order(
        consumer=consumer_wallet.address,
        service_index=ddo.get_index_of_service(service),
        provider_fees=provider_fees,
        tx_dict={"from": consumer_wallet},
    )

    # Download file
    destination = config["DOWNLOADS_PATH"]
    if not os.path.isabs(destination):
        destination = os.path.abspath(destination)

    if os.path.exists(destination) and len(os.listdir(destination)) > 0:
        list(
            map(
                lambda d: shutil.rmtree(os.path.join(destination, d)),
                os.listdir(destination),
            )
        )

    if not os.path.exists(destination):
        os.makedirs(destination)

    assert len(os.listdir(destination)) == 0

    ocean.assets.download_asset(
        ddo,
        consumer_wallet,
        destination,
        receipt.txid,
        service,
    )
    file_path = os.path.join(destination, os.listdir(destination)[0])
    assert len(os.listdir(file_path)) == 1, "The asset folder is empty."

    with open(os.path.join(file_path, os.listdir(file_path)[0])) as f:
        contents = f.readlines()
        content = json.loads(contents[0])
        assert "data" in content.keys()
        assert "indexingStatuses" in content["data"].keys()
