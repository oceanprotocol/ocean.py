#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import random
import shutil
from concurrent.futures import ThreadPoolExecutor

import pytest
from web3.main import Web3

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.ddo_helpers import (
    build_credentials_dict,
    get_first_service_by_type,
)
from tests.resources.helper_functions import deploy_erc721_erc20, generate_wallet


def consume_flow(ocean: Ocean, config: dict, tmpdir, files):
    consumer_wallet = publisher_wallet = generate_wallet()
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

    data_nft, datatoken = deploy_erc721_erc20(
        config, publisher_wallet, publisher_wallet
    )

    files = [random.choice(files)]

    ddo = ocean.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        files=files,
        data_nft_address=data_nft.address,
        datatoken_templates=[1],
        datatoken_names=["Datatoken 1"],
        datatoken_symbols=["DT1"],
        datatoken_minters=[publisher_wallet.address],
        datatoken_fee_managers=[publisher_wallet.address],
        datatoken_publish_market_order_fee_addresses=[ZERO_ADDRESS],
        datatoken_publish_market_order_fee_tokens=[ocean.OCEAN_address],
        datatoken_publish_market_order_fee_amounts=[0],
        datatoken_bytess=[[b""]],
    )

    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == data_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "Datatoken 1"
    assert ddo.datatokens[0]["symbol"] == "DT1"
    assert ddo.credentials == build_credentials_dict()

    service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)

    # Initialize service
    response = data_provider.initialize(
        did=ddo.did, service=service, consumer_address=publisher_wallet.address
    )
    assert response
    assert response.status_code == 200
    assert response.json()["providerFee"]

    datatoken.mint(
        consumer_wallet.address,
        Web3.toWei(20, "ether"),
        {"from": publisher_wallet},
    )
    # Start order for consumer
    provider_fees = response.json()["providerFee"]
    receipt = datatoken.start_order(
        consumer=consumer_wallet.address,
        service_index=ddo.get_index_of_service(service),
        provider_fee_address=provider_fees["providerFeeAddress"],
        provider_fee_token=provider_fees["providerFeeToken"],
        provider_fee_amount=provider_fees["providerFeeAmount"],
        v=provider_fees["v"],
        r=provider_fees["r"],
        s=provider_fees["s"],
        valid_until=provider_fees["validUntil"],
        provider_data=provider_fees["providerData"],
        consume_market_order_fee_address=consumer_wallet.address,
        consume_market_order_fee_token=datatoken.address,
        consume_market_order_fee_amount=0,
        transaction_parameters={"from": consumer_wallet},
    )
    # Download file
    destination = _create_downloads_path(tmpdir)

    ocean.assets.download_asset(
        ddo, consumer_wallet, destination, receipt.txid,
    )

    assert (
        len(os.listdir(os.path.join(destination, os.listdir(destination)[0]))) > 0
    ), "The asset folder is empty."


def concurrent_consume_flow(concurrent_flows: int, repetitions: int, tmpdir, files):
    config = ExampleConfig.get_config()
    ocean = Ocean(config)
    mint_fake_OCEAN(config)
    with ThreadPoolExecutor(max_workers=concurrent_flows) as executor:
        for _ in range(concurrent_flows * repetitions):
            executor.submit(consume_flow, ocean, config, tmpdir, files)


@pytest.mark.slow
@pytest.mark.parametrize(
    ["concurrent_flows", "repetitions"], [(1, 300), (3, 100), (20, 5)]
)
def test_concurrent_consume_flow(
    concurrent_flows, repetitions, tmpdir, file1, file2, file3
):
    files = [file1, file2, file3]
    concurrent_consume_flow(concurrent_flows, repetitions, tmpdir, files)


def _create_downloads_path(tmpdir):
    destination = tmpdir
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
        os.mkdir(destination)

    assert len(os.listdir(destination)) == 0

    return destination
