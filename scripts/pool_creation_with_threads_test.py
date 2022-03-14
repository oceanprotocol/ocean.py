#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import threading

import pytest

from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.structures.file_objects import UrlFile
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import pretty_ether_and_wei
from ocean_lib.web3_internal.wallet import Wallet


def asset_displayed_on_sale(ocean: Ocean, wallet: Wallet):
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
        erc20_publishing_market_addresses=[ZERO_ADDRESS],
        fee_token_addresses=[ocean.OCEAN_address],
        erc20_cap_values=[ocean.to_wei(100000)],
        publishing_fee_amounts=[0],
        erc20_bytess=[[b""]],
    )

    did = asset.did  # did contains the datatoken address
    assert did

    erc20_token = ocean.get_datatoken(asset.get_service("access").datatoken)
    OCEAN_token = ocean.get_datatoken(ocean.OCEAN_address)

    bpool = ocean.create_pool(
        erc20_token=erc20_token,
        base_token=OCEAN_token,
        rate=ocean.to_wei(1),
        vesting_amount=ocean.to_wei(10000),
        vested_blocks=2500000,
        initial_liq=ocean.to_wei(2000),
        lp_swap_fee=ocean.to_wei("0.01"),
        market_swap_fee=ocean.to_wei("0.01"),
        from_wallet=wallet,
    )
    assert bpool.address

    prices = bpool.get_amount_in_exact_out(
        OCEAN_token.address, erc20_token.address, ocean.to_wei(1), ocean.to_wei("0.01")
    )
    price_in_OCEAN = prices[0]
    formatted_price = pretty_ether_and_wei(price_in_OCEAN, "OCEAN")
    assert formatted_price


@pytest.mark.slow
def test_pool_creation_with_threads():
    config = ExampleConfig.get_config()
    ocean = Ocean(config)
    alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
    alice_wallet = Wallet(
        ocean.web3,
        alice_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )
    assert alice_wallet.address
    bob_private_key = os.getenv("TEST_PRIVATE_KEY2")
    bob_wallet = Wallet(
        ocean.web3,
        bob_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )
    assert bob_wallet.address
    carol_private_key = os.getenv("TEST_PRIVATE_KEY3")
    carol_wallet = Wallet(
        ocean.web3,
        carol_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )
    assert carol_wallet.address
    # Mint OCEAN
    mint_fake_OCEAN(config)
    assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"
    assert bob_wallet.web3.eth.get_balance(bob_wallet.address) > 0, "need ETH"
    assert carol_wallet.web3.eth.get_balance(carol_wallet.address) > 0, "need ETH"

    threads = list()
    t1 = threading.Thread(
        target=asset_displayed_on_sale,
        args=(
            ocean,
            alice_wallet,
        ),
    )
    threads.append(t1)
    t2 = threading.Thread(
        target=asset_displayed_on_sale,
        args=(
            ocean,
            bob_wallet,
        ),
    )
    threads.append(t2)
    t3 = threading.Thread(
        target=asset_displayed_on_sale,
        args=(
            ocean,
            carol_wallet,
        ),
    )
    threads.append(t3)
    t1.start()
    t2.start()
    t3.start()
    for index, thread in enumerate(threads):
        print(f"Main    : before joining thread {index}.")
        thread.join()
        print(f"Main    : thread {index} done")
