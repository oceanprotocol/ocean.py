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
        datatoken_name="Datatoken1",
        datatoken_symbol="DT1",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=publisher_wallet.address,
        datatoken_publishing_market_address=publishing_market_wallet.address,
        fee_token_address=publisher_ocean_instance.OCEAN_address,
        datatoken_cap=publisher_ocean_instance.to_wei(1_410_000_000),
        publishing_market_fee_amount=10,
        bytess=[b""],
        from_wallet=publisher_wallet,
    )

    # Verify that PublishMarketFeeChanged event emitted
