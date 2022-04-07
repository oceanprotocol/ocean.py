#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from concurrent.futures import ThreadPoolExecutor

import pytest

from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.structures.file_objects import UrlFile
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import pretty_ether_and_wei
from tests.resources.ddo_helpers import get_first_service_by_type
from tests.resources.helper_functions import generate_wallet


def asset_displayed_on_sale(ocean: Ocean):
    wallet = generate_wallet()
    erc721_nft = ocean.create_erc721_nft("NFTToken1", "NFT1", wallet)
    token_address = erc721_nft.address
    assert token_address

    # Specify metadata and services, using the Branin test dataset
    date_created = "2021-12-28T10:55:11Z"
    metadata = {
        "created": date_created,
        "updated": date_created,
        "description": "Branin dataset",
        "name": "Branin dataset",
        "type": "dataset",
        "author": "Trent",
        "license": "CC0: PublicDomain",
    }

    # ocean.py offers multiple file types, but a simple url file should be enough for this example
    url_file = UrlFile(
        url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
    )

    # Encrypt file(s) using provider
    encrypted_files = ocean.assets.encrypt_files([url_file])

    # Publish asset with services on-chain.
    # The download (access service) is automatically created, but you can explore other options as well
    asset = ocean.assets.create(
        metadata=metadata,
        publisher_wallet=wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_nft.address,
        erc20_templates=[1],
        erc20_names=["Datatoken 1"],
        erc20_symbols=["DT1"],
        erc20_minters=[wallet.address],
        erc20_fee_managers=[wallet.address],
        erc20_publish_market_order_fee_addresses=[ZERO_ADDRESS],
        erc20_publish_market_order_fee_tokens=[ocean.OCEAN_address],
        erc20_caps=[ocean.to_wei(100000)],
        erc20_publish_market_order_fee_amounts=[0],
        erc20_bytess=[[b""]],
    )

    did = asset.did  # did contains the datatoken address
    assert did

    erc20_token = ocean.get_datatoken(
        get_first_service_by_type(asset, "access").datatoken
    )
    OCEAN_token = ocean.get_datatoken(ocean.OCEAN_address)

    bpool = ocean.create_pool(
        erc20_token=erc20_token,
        base_token=OCEAN_token,
        rate=ocean.to_wei(1),
        vesting_amount=ocean.to_wei(10000),
        vesting_blocks=2500000,
        base_token_amount=ocean.to_wei(2000),
        lp_swap_fee_amount=ocean.to_wei("0.01"),
        publish_market_swap_fee_amount=ocean.to_wei("0.01"),
        from_wallet=wallet,
    )
    assert bpool.address

    prices = bpool.get_amount_in_exact_out(
        OCEAN_token.address, erc20_token.address, ocean.to_wei(1), ocean.to_wei("0.01")
    )
    price_in_OCEAN = prices[0]
    formatted_price = pretty_ether_and_wei(price_in_OCEAN, "OCEAN")
    assert formatted_price


def concurrent_pool_creation(concurrent_flows: int, duration: int):
    config = ExampleConfig.get_config()
    ocean = Ocean(config)
    mint_fake_OCEAN(config)
    with ThreadPoolExecutor(max_workers=concurrent_flows) as executor:
        for _ in range(concurrent_flows * duration):
            executor.submit(asset_displayed_on_sale, ocean)


@pytest.mark.slow
def test_concurrent_pool_creation():
    concurrent_flows_values = [1, 3, 20]
    reps = [3000, 1000, 50]
    for counter in range(len(concurrent_flows_values)):
        concurrent_pool_creation(concurrent_flows_values[counter], reps[counter])
