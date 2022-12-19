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
from ocean_lib.ocean.ocean import Ocean
from tests.resources.ddo_helpers import (
    get_first_service_by_type,
    get_registered_asset_with_access_service,
)


@pytest.mark.integration
def test_consume_flow(
    config: dict,
    publisher_wallet,
    consumer_wallet,
):
    ocean = Ocean(config)

    # Publish a plain asset with one data token on chain
    data_nft, dt, ddo = get_registered_asset_with_access_service(
        ocean,
        publisher_wallet,
    )

    service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)

    # Mint 50 datatokens in consumer wallet from publisher. Max cap = 100
    dt.mint(
        consumer_wallet.address,
        Web3.toWei("50", "ether"),
        {"from": publisher_wallet},
    )

    # Initialize service
    response = DataServiceProvider.initialize(
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

    ocean.assets.download_asset(
        ddo, consumer_wallet, destination, receipt.txid, service
    )

    assert (
        len(os.listdir(os.path.join(destination, os.listdir(destination)[0]))) == 1
    ), "The asset folder is empty."
