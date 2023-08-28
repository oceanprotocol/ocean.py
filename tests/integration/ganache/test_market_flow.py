#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import os

import pytest
from web3.main import Web3

from ocean_lib.models.datatoken_base import TokenFeeInfo
from ocean_lib.ocean.util import to_wei
from tests.resources.helper_functions import get_another_consumer_ocean_instance


@pytest.mark.integration
@pytest.mark.parametrize("consumer_type", ["publisher", "another_user"])
def test_market_flow(
    publisher_wallet,
    consumer_wallet,
    basic_asset,
    consumer_ocean,
    another_consumer_wallet,
    consumer_type,
):
    """Tests that an order is correctly placed on the market.

    The parameter implicit_none sends the payload with an empty key as the delegated consumer.
    The parameter explicit_none sends None as the delegated consumer, explicitly."""
    consumer_ocean = consumer_ocean
    another_consumer_ocean = get_another_consumer_ocean_instance(use_provider_mock=True)

    data_nft, datatoken, ddo = basic_asset
    service = ddo.services[0]

    # Mint data tokens and assign to publisher
    datatoken.mint(
        publisher_wallet.address,
        to_wei(50),
        {"from": publisher_wallet},
    )

    # Give the consumer some datatokens so they can order the service
    datatoken.transfer(consumer_wallet.address, to_wei(10), {"from": publisher_wallet})

    # Place order for the download service
    if consumer_type == "publisher":
        order_tx_id = consumer_ocean.assets.pay_for_access_service(
            ddo,
            {"from": consumer_wallet},
            service=service,
            consume_market_fees=TokenFeeInfo(token=datatoken.address),
        ).hex()
        asset_folder = consumer_ocean.assets.download_asset(
            ddo,
            consumer_wallet,
            consumer_ocean.config_dict["DOWNLOADS_PATH"],
            order_tx_id,
            service,
        )
    else:
        order_tx_id = consumer_ocean.assets.pay_for_access_service(
            ddo,
            {"from": consumer_wallet},
            service=service,
            consume_market_fees=TokenFeeInfo(
                address=another_consumer_wallet.address,
                token=datatoken.address,
            ),
            consumer_address=another_consumer_wallet.address,
        ).hex()
        asset_folder = consumer_ocean.assets.download_asset(
            ddo,
            another_consumer_wallet,
            another_consumer_ocean.config_dict["DOWNLOADS_PATH"],
            order_tx_id,
            service,
        )

    assert len(os.listdir(asset_folder)) >= 1, "The asset folder is empty."

    orders = consumer_ocean.get_user_orders(consumer_wallet.address, datatoken.address)
    assert (
        orders
    ), f"no orders found using the order history: datatoken {datatoken.address}, consumer {consumer_wallet.address}"

    orders = consumer_ocean.get_user_orders(
        consumer_wallet.address,
        Web3.to_checksum_address(datatoken.address),
    )
    assert (
        orders
    ), f"no orders found using the order history: datatoken {datatoken.address}, consumer {consumer_wallet.address}"


@pytest.mark.integration
def test_pay_for_access_service_good_default(
    basic_asset,
    publisher_wallet,
    consumer_wallet,
    consumer_ocean,
):
    data_nft, datatoken, ddo = basic_asset
    service = ddo.services[0]

    # Mint datatokens to consumer
    datatoken.mint(consumer_wallet.address, to_wei(50), {"from": publisher_wallet})

    # Place order for the download service
    # - Here, use good defaults for service, and fee-related args
    order_tx_id = consumer_ocean.assets.pay_for_access_service(
        ddo, {"from": consumer_wallet}
    ).hex()

    asset_folder = consumer_ocean.assets.download_asset(
        ddo,
        consumer_wallet,
        consumer_ocean.config_dict["DOWNLOADS_PATH"],
        order_tx_id,
        service,
    )

    # basic check. Leave thorough checks to other tests here
    assert len(os.listdir(asset_folder)) >= 1, "The asset folder is empty."
