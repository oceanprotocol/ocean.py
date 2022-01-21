#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import os

import pytest
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.ddo_helpers import get_registered_asset_with_access_service
from tests.resources.helper_functions import get_another_consumer_ocean_instance


@pytest.mark.parametrize("consumer_type", ["publisher", "another_user"])
def test_market_flow(
    publisher_wallet,
    consumer_wallet,
    publisher_ocean_instance,
    consumer_ocean_instance,
    another_consumer_wallet,
    consumer_type,
):
    """Tests that an order is correctly placed on the market.

    The parameter implicit_none sends the payload with an empty key as the delegated consumer.
    The parameter explicit_none sends None as the delegated consumer, explicitly."""
    publisher_ocean = publisher_ocean_instance
    consumer_ocean = consumer_ocean_instance
    another_consumer_ocean = get_another_consumer_ocean_instance(use_provider_mock=True)

    asset = get_registered_asset_with_access_service(publisher_ocean, publisher_wallet)
    service = asset.get_service("access")
    erc20_token = publisher_ocean.get_datatoken(service.datatoken)

    # Mint data tokens and assign to publisher
    erc20_token.mint(
        account_address=publisher_wallet.address,
        value=to_wei(50),
        from_wallet=publisher_wallet,
    )

    # Give the consumer some datatokens so they can order the service
    erc20_token.transfer(consumer_wallet.address, to_wei(10), publisher_wallet)

    # Place order for the download service
    if consumer_type == "publisher":
        order_tx_id = consumer_ocean.assets.pay_for_service(
            asset, service, consumer_wallet
        )
        asset_folder = consumer_ocean.assets.download_asset(
            asset,
            service.service_endpoint,
            consumer_wallet,
            consumer_ocean.config.downloads_path,
            order_tx_id,
        )
    else:
        order_tx_id = consumer_ocean.assets.pay_for_service(
            asset, service, consumer_wallet, another_consumer_wallet.address
        )
        asset_folder = consumer_ocean.assets.download_asset(
            asset,
            service.service_endpoint,
            another_consumer_wallet,
            another_consumer_ocean.config.downloads_path,
            order_tx_id,
        )

    assert len(os.listdir(asset_folder)) >= 1, "The asset folder is empty."

    orders = consumer_ocean.get_user_orders(
        consumer_wallet.address, erc20_token.address
    )
    assert (
        orders
    ), f"no orders found using the order history: datatoken {erc20_token.address}, consumer {consumer_wallet.address}"

    orders = consumer_ocean.get_user_orders(
        consumer_wallet.address,
        consumer_ocean.web3.toChecksumAddress(erc20_token.address),
    )
    assert (
        orders
    ), f"no orders found using the order history: datatoken {erc20_token.address}, consumer {consumer_wallet.address}"

    orders = consumer_ocean.get_user_orders(consumer_wallet.address)
    assert (
        orders
    ), f"no orders found using the order history: datatoken {erc20_token.address}, consumer {consumer_wallet.address}"
