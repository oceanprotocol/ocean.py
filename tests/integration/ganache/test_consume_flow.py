#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import shutil

import pytest
from web3.main import Web3

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.ocean.util import get_address_of_type
from tests.resources.ddo_helpers import get_first_service_by_type

ARWEAVE_TRANSACTION_ID = "a4qJoQZa1poIv5guEzkfgZYSAD0uYm7Vw4zm_tCswVQ"


@pytest.mark.integration
@pytest.mark.parametrize("asset_type", ["simple", "graphql", "onchain", "arweave"])
def test_consume_asset(config: dict, publisher_wallet, consumer_wallet, asset_type):
    data_provider = DataServiceProvider
    ocean_assets = OceanAssets(config, data_provider)

    if asset_type == "simple":
        url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
        data_nft, dt, ddo = ocean_assets.create_url_asset(
            "Data NFTs in Ocean", url, publisher_wallet
        )
    elif asset_type == "arweave":
        data_nft, dt, ddo = ocean_assets.create_arweave_asset(
            "Data NFTs in Ocean", ARWEAVE_TRANSACTION_ID, publisher_wallet
        )
    elif asset_type == "onchain":
        abi = {
            "inputs": [],
            "name": "swapOceanFee",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        }
        router_address = get_address_of_type(config, "Router")

        data_nft, dt, ddo = ocean_assets.create_onchain_asset(
            "Data NFTs in Ocean", router_address, abi, publisher_wallet
        )
    else:
        url = "http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
        query = """
            query{
                nfts(orderby: createdtimestamp,orderdirection:desc){
                    id
                    symbol
                    createdtimestamp
                }
            }
            """

        data_nft, dt, ddo = ocean_assets.create_graphql_asset(
            "Data NFTs in Ocean", url, query, publisher_wallet
        )

    assert ddo, "The ddo is not created."
    assert ddo.nft["address"] == data_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "Data NFTs in Ocean: DT1"

    service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)

    # Mint 50 datatokens in consumer wallet from publisher. Max cap = 100
    dt.mint(
        consumer_wallet.address,
        Web3.toWei("50", "ether"),
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
        transaction_parameters={"from": consumer_wallet},
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

    ocean_assets.download_asset(
        ddo,
        consumer_wallet,
        destination,
        receipt.txid,
        service,
    )

    assert (
        len(os.listdir(os.path.join(destination, os.listdir(destination)[0]))) == 1
    ), "The asset folder is empty."
