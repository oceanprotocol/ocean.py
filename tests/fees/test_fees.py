#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import get_wallet


@pytest.fixture
def publishing_market_wallet():
    return get_wallet(4)


@pytest.fixture
def consuming_market_wallet():
    return get_wallet(5)


@pytest.mark.skip
def test_fees(
    publisher_ocean_instance: Ocean,
    publisher_wallet: Wallet,
    publishing_market_wallet: Wallet,
    # consumer_wallet: Wallet,
    # provider_wallet: Wallet,
):
    # Create data NFT
    data_nft = publisher_ocean_instance.create_erc721_nft(
        "NFTToken1", "NFT1", publisher_wallet
    )

    # Create datatoken
    datatoken = data_nft.create_datatoken(
        template_index=1,
        name="Datatoken1",
        symbol="DT1",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publishing_market_wallet.address,
        publish_market_order_fee_token=publisher_ocean_instance.OCEAN_address,
        cap=publisher_ocean_instance.to_wei(1_410_000_000),
        publish_market_order_fee_amount=10,
        bytess=[b""],
        from_wallet=publisher_wallet,
    )

    # Verify that PublishMarketFeeChanged event emitted
