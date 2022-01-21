#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import os

import pytest
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.services.service import Service
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.ddo_helpers import get_registered_asset_with_access_service
from tests.resources.helper_functions import (
    get_another_consumer_ocean_instance,
    get_consumer_ocean_instance,
    get_publisher_ocean_instance,
)


def test_market_flow(
    publisher_wallet, consumer_wallet, publisher_ocean_instance, consumer_ocean_instance
):
    """Tests that an order is correctly placed on the market.

    The parameter implicit_none sends the payload with an empty key as the delegated consumer.
    The parameter explicit_none sends None as the delegated consumer, explicitly."""
    publisher_ocean = publisher_ocean_instance
    consumer_ocean = consumer_ocean_instance

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
    order_tx_id = consumer_ocean.assets.pay_for_service(asset, service, consumer_wallet)

    asset_folder = consumer_ocean.assets.download_asset(
        asset,
        service.service_endpoint,
        consumer_wallet,
        consumer_ocean.config.downloads_path,
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


@pytest.mark.skip(reason="TODO: reinstate integration tests")
def test_payer_market_flow(publisher_wallet, consumer_wallet, another_consumer_wallet):
    """Tests that an order can be placed for a delegated consumer, other than the payer."""
    pub_wallet = publisher_wallet

    publisher_ocean = get_publisher_ocean_instance()
    consumer_ocean = get_consumer_ocean_instance()
    another_consumer_ocean = get_another_consumer_ocean_instance(use_provider_mock=True)

    # Register Asset
    # Register asset
    # TODO was get_metadata, but obsolete
    # asset = get_registered_ddo(publisher_ocean, get_metadata(), pub_wallet)
    asset = None
    assert isinstance(asset, Asset)
    assert asset.datatoken_address, "The asset does not have a token address."

    service = asset.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    sa = Service.from_json(service.as_dictionary())

    # Mint data tokens and assign to publisher
    dt = publisher_ocean.get_datatoken(asset.datatoken_address)
    # mint_tokens_and_wait(dt, pub_wallet.address, pub_wallet)

    ######
    # Give the consumer some datatokens so they can order the service
    try:
        tx_id = dt.transfer(consumer_wallet.address, to_wei(10), pub_wallet)
        dt.verify_transfer_tx(tx_id, pub_wallet.address, consumer_wallet.address)
    except (AssertionError, Exception) as e:
        print(e)
        raise

    ######
    # Place order for the download service
    order_requirements = consumer_ocean.assets.order(
        asset.did, another_consumer_wallet.address, sa.index
    )

    ######
    # Pay for the service and have another_consumer_wallet as consumer
    _order_tx_id = consumer_ocean.assets.pay_for_service(
        consumer_ocean.web3,
        order_requirements.amount,
        order_requirements.datatoken_address,
        asset.did,
        service.index,
        "0xF9f2DB837b3db03Be72252fAeD2f6E0b73E428b9",
        consumer_wallet,
        another_consumer_wallet.address,
    )
    asset_folder = None
    assert asset_folder is None
    if asset_folder is None:
        # Download the asset files
        asset_folder = another_consumer_ocean.assets.download(
            asset.did,
            sa.index,
            another_consumer_wallet,
            _order_tx_id,
            another_consumer_ocean.config.downloads_path,
        )
    assert len(os.listdir(asset_folder)) >= 1

    orders = consumer_ocean.get_user_orders(consumer_wallet.address, asset.asset_id)
    assert (
        orders
    ), f"no orders found using the order history: datatoken {asset.asset_id}, consumer {consumer_wallet.address}"

    orders = consumer_ocean.get_user_orders(
        consumer_wallet.address, consumer_ocean.web3.toChecksumAddress(asset.asset_id)
    )
    assert (
        orders
    ), f"no orders found using the order history: datatoken {asset.asset_id}, consumer {consumer_wallet.address}"

    orders = consumer_ocean.get_user_orders(consumer_wallet.address)
    assert (
        orders
    ), f"no orders found using the order history: datatoken {asset.asset_id}, consumer {consumer_wallet.address}"
