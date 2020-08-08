#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import os

from ocean_utils.agreements.service_agreement import ServiceAgreement
from ocean_utils.agreements.service_types import ServiceTypes

from ocean_lib.assets.asset import Asset
from tests.resources.helper_functions import (
    get_consumer_wallet,
    get_publisher_wallet,
    get_registered_ddo,
    get_publisher_ocean_instance,
    get_consumer_ocean_instance,
    mint_tokens_and_wait,
)


def test_market_flow():
    pub_wallet = get_publisher_wallet()

    publisher_ocean = get_publisher_ocean_instance()
    consumer_ocean = get_consumer_ocean_instance()

    # Register Asset
    asset = get_registered_ddo(publisher_ocean, pub_wallet)
    assert isinstance(asset, Asset)
    assert asset.data_token_address

    consumer_wallet = get_consumer_wallet()

    service = asset.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    sa = ServiceAgreement.from_json(service.as_dictionary())

    # Mint data tokens and assign to publisher
    dt = publisher_ocean.get_data_token(asset.data_token_address)
    mint_tokens_and_wait(dt, pub_wallet.address, pub_wallet)

    ######
    # Give the consumer some datatokens so they can order the service
    try:
        tx_id = dt.transfer_tokens(consumer_wallet.address, 10, pub_wallet)
        dt.verify_transfer_tx(tx_id, pub_wallet.address, consumer_wallet.address)
    except (AssertionError, Exception) as e:
        print(e)
        raise

    ######
    # Place order for the download service
    order_requirements = consumer_ocean.assets.order(asset.did, consumer_wallet.address, sa.index)

    ######
    # Pay for the service
    payment_tx_id = consumer_ocean.assets.pay_for_service(
        order_requirements.amount,
        order_requirements.data_token_address,
        order_requirements.receiver_address,
        consumer_wallet
    )
    ######
    # Download the asset files
    asset_folder = consumer_ocean.assets.download(
        asset.did,
        sa.index,
        consumer_wallet,
        payment_tx_id,
        consumer_ocean.config.downloads_path
    )

    assert len(os.listdir(asset_folder)) > 1
