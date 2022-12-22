#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import os

import pytest
from web3.main import Web3

from ocean_lib.models.datatoken import FeeTokenInfo
from tests.resources.ddo_helpers import get_registered_asset_with_access_service
from tests.resources.helper_functions import get_another_consumer_ocean_instance


@pytest.mark.integration
@pytest.mark.parametrize("consumer_type", ["publisher", "another_user"])
def test_market_flow(
    publisher_wallet,
    consumer_wallet,
    publisher_ocean,
    consumer_ocean,
    another_consumer_wallet,
    consumer_type,
):
    """Tests that an order is correctly placed on the market.

    The parameter implicit_none sends the payload with an empty key as the delegated consumer.
    The parameter explicit_none sends None as the delegated consumer, explicitly."""
    consumer_ocean = consumer_ocean
    another_consumer_ocean = get_another_consumer_ocean_instance(use_provider_mock=True)

    data_nft, datatoken, ddo = get_registered_asset_with_access_service(
        publisher_ocean, publisher_wallet
    )
    service = ddo.services[0]

    # Mint data tokens and assign to publisher
    datatoken.mint(
        publisher_wallet.address,
        Web3.toWei(50, "ether"),
        {"from": publisher_wallet},
    )

    # Give the consumer some datatokens so they can order the service
    datatoken.transfer(
        consumer_wallet.address, Web3.toWei(10, "ether"), {"from": publisher_wallet}
    )

    # Place order for the download service
    if consumer_type == "publisher":
        order_tx_id = consumer_ocean.assets.pay_for_access_service(
            ddo,
            consumer_wallet,
            service=service,
            consume_market_fees=FeeTokenInfo(token=datatoken.address),
        )
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
            consumer_wallet,
            service=service,
            consume_market_fees=FeeTokenInfo(
                address=another_consumer_wallet.address,
                token=datatoken.address,
            ),
            consumer_address=another_consumer_wallet.address,
        )
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
        Web3.toChecksumAddress(datatoken.address),
    )
    assert (
        orders
    ), f"no orders found using the order history: datatoken {datatoken.address}, consumer {consumer_wallet.address}"


@pytest.mark.integration
def test_pay_for_access_service_good_default(
    publisher_wallet,
    consumer_wallet,
    publisher_ocean,
    consumer_ocean,
):
    data_nft, datatoken, ddo = get_registered_asset_with_access_service(
        publisher_ocean, publisher_wallet
    )
    service = ddo.services[0]

    # Mint datatokens to consumer
    datatoken.mint(
        consumer_wallet.address, Web3.toWei(50, "ether"), {"from": publisher_wallet}
    )

    # Place order for the download service
    # - Here, use good defaults for service, and fee-related args
    order_tx_id = consumer_ocean.assets.pay_for_access_service(ddo, consumer_wallet)

    asset_folder = consumer_ocean.assets.download_asset(
        ddo,
        consumer_wallet,
        consumer_ocean.config_dict["DOWNLOADS_PATH"],
        order_tx_id,
        service,
    )

    # basic check. Leave thorough checks to other tests here
    assert len(os.listdir(asset_folder)) >= 1, "The asset folder is empty."
