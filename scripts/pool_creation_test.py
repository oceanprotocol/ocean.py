#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest

from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.structures.abi_tuples import CreateErc20Data
from ocean_lib.structures.file_objects import UrlFile
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import pretty_ether_and_wei
from ocean_lib.web3_internal.wallet import Wallet


@pytest.mark.skip(reason="This test is slow and not needed in the CI")
def test_stressed_pool_creation():
    config = ExampleConfig.get_config()
    ocean = Ocean(config)

    # Create Alice's wallet
    alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
    alice_wallet = Wallet(
        ocean.web3,
        alice_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )
    assert alice_wallet.address

    # Mint OCEAN
    mint_fake_OCEAN(config)
    assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"

    # Publish an NFT token
    for _ in range(3000):
        erc721_nft = ocean.create_erc721_nft("NFTToken1", "NFT1", alice_wallet)
        token_address = erc721_nft.address
        assert token_address

        # Prepare data for ERC20 token
        erc20_data = CreateErc20Data(
            template_index=1,
            strings=["Datatoken 1", "DT1"],
            addresses=[
                alice_wallet.address,
                alice_wallet.address,
                ZERO_ADDRESS,
                ocean.OCEAN_address,
            ],
            uints=[ocean.to_wei(100000), 0],
            bytess=[b""],
        )

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
            metadata, alice_wallet, encrypted_files, erc20_tokens_data=[erc20_data]
        )

        did = asset.did  # did contains the datatoken address
        assert did

        erc20_token = ocean.get_datatoken(asset.get_service("access").datatoken)
        OCEAN_token = ocean.get_datatoken(ocean.OCEAN_address)

        ss_params = [
            ocean.to_wei(1),
            OCEAN_token.decimals(),
            ocean.to_wei(10000),
            2500000,
            ocean.to_wei(2000),
        ]
        swap_fees = [ocean.to_wei("0.01"), ocean.to_wei("0.01")]
        bpool = ocean.create_pool(
            erc20_token, OCEAN_token, ss_params, swap_fees, alice_wallet
        )
        assert bpool.address

        prices = bpool.get_amount_in_exact_out(
            OCEAN_token.address,
            erc20_token.address,
            ocean.to_wei(1),
            ocean.to_wei("0.01"),
        )
        price_in_OCEAN = prices[0]
        formatted_price = pretty_ether_and_wei(price_in_OCEAN, "OCEAN")
        assert formatted_price