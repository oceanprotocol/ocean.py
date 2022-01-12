#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from ocean_lib.agreements.file_objects import UrlFile
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.models_structures import ErcCreateData
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet


def test_marketplace_flow():
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
    nft_token = ocean.create_nft_token("NFTToken1", "NFT1", alice_wallet)
    token_address = nft_token.address
    assert token_address

    # Prepare data for ERC20 token
    erc20_data = ErcCreateData(
        template_index=1,
        strings=["Datatoken 1", "DT1"],
        addresses=[
            alice_wallet.address,
            alice_wallet.address,
            ZERO_ADDRESS,
            ocean.OCEAN_address,
        ],
        uints=[ocean.web3.toWei(100000, "ether"), 0],
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
        "author": "Treunt",
        "license": "CC0: PublicDomain",
    }

    # ocean.py offers multiple file types, but a simple url file should be enough for this example
    url_file = UrlFile(
        url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
    )

    # Encrypt file(s) using provider
    provider_url = config.provider_url + "/api/services/encrypt"
    encrypt_response = DataServiceProvider.encrypt([url_file], provider_url)
    encrypted_files = encrypt_response.content.decode("utf-8")

    # Publish asset with services on-chain.
    # The download (access service) is automatically created, but you can explore other options as well
    asset = ocean.assets.create(
        metadata, alice_wallet, encrypted_files, erc20_tokens_data=[erc20_data]
    )

    did = asset.did  # did contains the datatoken address
    assert did

    erc20_token = ocean.get_data_token(asset.get_service("access").data_token)
    OCEAN_token = ocean.get_data_token(ocean.OCEAN_address)

    ss_params = [
        ocean.web3.toWei(1, "ether"),
        OCEAN_token.decimals(),
        ocean.web3.toWei(10000, "ether"),
        2500000,
        ocean.web3.toWei(2000, "ether"),
    ]

    swap_fees = [ocean.web3.toWei(0.01, "ether"), ocean.web3.toWei(0.01, "ether")]
    bpool = ocean.create_pool(
        erc20_token, OCEAN_token, ss_params, swap_fees, alice_wallet
    )
    assert bpool.address

    # TODO: pricing and place pricing in readme

    bob_private_key = os.getenv("TEST_PRIVATE_KEY2")
    bob_wallet = Wallet(
        ocean.web3,
        bob_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )

    # Verify that Bob has ganache ETH
    assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

    # Verify that Bob has ganache OCEAN
    assert OCEAN_token.balanceOf(bob_wallet.address) > 0, "need ganache OCEAN"

    OCEAN_token.approve(
        bpool.address, ocean.web3.toWei("10000", "ether"), from_wallet=bob_wallet
    )

    bpool.swap_exact_amount_out(
        [OCEAN_token.address, erc20_token.address, ZERO_ADDRESS],
        [
            ocean.web3.toWei(10, "ether"),
            ocean.web3.toWei(1, "ether"),
            ocean.web3.toWei(10, "ether"),
            0,
        ],
        from_wallet=bob_wallet,
    )
    assert erc20_token.balanceOf(bob_wallet.address) >= ocean.web3.toWei(
        1, "ether"
    ), "Bob didn't get 1.0 datatokens"

    # TODO: order and pay
