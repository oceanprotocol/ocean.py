#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import shutil

import pytest
from brownie.network import accounts
from web3.main import Web3


from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.exceptions import InsufficientBalance
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.ddo_helpers import (
    get_first_service_by_type,
    get_registered_asset_with_access_service,
    get_registered_asset_with_access_service_using_enterprise_template,
)
from tests.resources.helper_functions import send_mock_usdc_to_address

toWei, fromWei = Web3.toWei, Web3.fromWei


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
        provider_fee_address=provider_fees["providerFeeAddress"],
        provider_fee_token=provider_fees["providerFeeToken"],
        provider_fee_amount=provider_fees["providerFeeAmount"],
        v=provider_fees["v"],
        r=provider_fees["r"],
        s=provider_fees["s"],
        valid_until=provider_fees["validUntil"],
        provider_data=provider_fees["providerData"],
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

    ocean.assets.download_asset(
        ddo, consumer_wallet, destination, receipt.txid, service
    )

    assert (
        len(os.listdir(os.path.join(destination, os.listdir(destination)[0]))) == 1
    ), "The asset folder is empty."


@pytest.mark.integration
def test_compact_publish_and_consume(
    config: dict,
    publisher_wallet,
    consumer_wallet,
):
    data_provider = DataServiceProvider
    ocean_assets = OceanAssets(config, data_provider)

    # publish
    name = "My asset"
    url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
    (data_nft, datatoken, ddo) = ocean_assets.create_url_asset(
        name, url, publisher_wallet
    )

    # share access
    datatoken.mint(
        consumer_wallet.address, Web3.toWei(1, "ether"), {"from": publisher_wallet}
    )

    # consume
    _ = ocean_assets.download_file(ddo.did, consumer_wallet)


@pytest.mark.integration
def test_ocean_assets_download_with_enterprise_template_and_dispenser(
    config: dict,
    publisher_wallet,
    consumer_wallet,
):
    data_provider = DataServiceProvider
    ocean_assets = OceanAssets(config, data_provider)
    # create asset using enterprise template
    (
        data_nft_2,
        datatoken_2,
        ddo_2,
    ) = get_registered_asset_with_access_service_using_enterprise_template(
        ocean_assets, publisher_wallet
    )
    datatoken_2.create_dispenser({"from": publisher_wallet})
    _ = ocean_assets.download_file(ddo_2.did, consumer_wallet)


@pytest.mark.integration
def test_ocean_assets_download_with_enterprise_template_and_fixedrate(
    config: dict, publisher_wallet, consumer_wallet
):
    data_provider = DataServiceProvider
    ocean_assets = OceanAssets(config, data_provider)
    # create asset using enterprise template
    (
        data_nft_2,
        datatoken_2,
        ddo_2,
    ) = get_registered_asset_with_access_service_using_enterprise_template(
        ocean_assets, publisher_wallet
    )
    fre_address = get_address_of_type(config, "FixedPrice")
    base_token_address = get_address_of_type(config, "MockUSDC")
    datatoken_2.create_fixed_rate(
        fre_address,
        base_token_address,
        publisher_wallet.address,
        ZERO_ADDRESS,
        datatoken_2.address,
        6,
        18,
        toWei(1, "ether"),
        0,
        1,
        {"from": publisher_wallet},
    )
    empty_wallet = accounts.add()

    with pytest.raises(InsufficientBalance):
        _ = ocean_assets.download_file(ddo_2.did, empty_wallet)
    # mint 1 Dai and try again
    dai_datatoken = Datatoken(config, base_token_address)
    send_mock_usdc_to_address(config, consumer_wallet.address, 2)
    # now it should pass
    _ = ocean_assets.download_file(ddo_2.did, consumer_wallet)
