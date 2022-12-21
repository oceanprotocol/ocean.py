#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import shutil

import pytest
from brownie import network
from web3.main import Web3

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.ocean_assets import DatatokenArguments, OceanAssets
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.structures.file_objects import SmartContractCall
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.ddo_helpers import get_first_service_by_type


@pytest.mark.integration
def test_consume_parametrized_onchain_data(
    config: dict,
    publisher_wallet,
    consumer_wallet,
):
    data_provider = DataServiceProvider
    ocean_assets = OceanAssets(config, data_provider)
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }
    abi = {
        "inputs": [{"internalType": "address", "name": "baseToken", "type": "address"}],
        "name": "getOPCFee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
    router_address = get_address_of_type(config, "Router")
    onchain_data = SmartContractCall(
        address=router_address, chainId=network.chain[-1].number, abi=abi
    )

    files = [onchain_data]

    # to consume dataset, consumer needs to send a value for nftAddress
    consumer_parameters = [
        {
            "name": "baseToken",
            "type": "text",
            "label": "baseToken",
            "required": True,
            "description": "baseToken to check for fee",
            "default": "0x0000000000000000000000000000000000000000",
        }
    ]

    # Publish a plain asset with one data token on chain
    dt_arg = DatatokenArguments(files=files, consumer_parameters=consumer_parameters)
    data_nft, _, ddo = ocean_assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        datatoken_args=[dt_arg],
    )

    assert ddo, "The ddo is not created."
    assert ddo.nft["name"] == "Sample asset"
    assert ddo.nft["symbol"] == "Sample asset"
    assert ddo.nft["address"] == data_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "Datatoken 1"
    assert ddo.datatokens[0]["symbol"] == "DT1"

    service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)
    dt = Datatoken(config, ddo.datatokens[0]["address"])

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
        consume_market_order_fee_address=ZERO_ADDRESS,
        consume_market_order_fee_token=ZERO_ADDRESS,
        consume_market_order_fee_amount=0,
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

    # this is where user is sending the required consumer_parameters
    userdata = {"baseToken": ddo.nft_address.lower()}
    ocean_assets.download_asset(
        ddo, consumer_wallet, destination, receipt.txid, service, userdata=userdata
    )

    dir_files = os.listdir(os.path.join(destination, os.listdir(destination)[0]))
    assert len(dir_files) == len(files), "The asset folder is empty."
