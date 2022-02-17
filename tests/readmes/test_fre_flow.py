#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.structures.abi_tuples import CreateErc20Data
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet


def test_fre_flow_readme():
    """This test mirrors the fixed-rate-exchange-flow.md README.
    As such, it does not use the typical pytest fixtures.
    """

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
    erc721_nft = ocean.create_erc721_nft(
        "NFTToken1", "NFT1", alice_wallet, "https://oceanprotocol.com/nft/"
    )
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
        uints=[ocean.to_wei(200), 0],
        bytess=[b""],
    )

    erc20_token = erc721_nft.create_datatoken(erc20_data, alice_wallet)
    print(f"token_address = '{erc20_token.address}'")

    # Mint the datatokens
    erc20_token.mint(alice_wallet.address, ocean.to_wei(100), alice_wallet)

    # Bob buys at fixed rate data tokens
    bob_private_key = os.getenv("TEST_PRIVATE_KEY2")
    bob_wallet = Wallet(
        ocean.web3,
        bob_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )
    print(f"bob_wallet.address = '{bob_wallet.address}'")

    # Verify that Bob has ganache ETH
    assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

    OCEAN_token = ocean.get_datatoken(ocean.OCEAN_address)

    # Create exchange_id for a new exchange
    exchange_id = ocean.create_fixed_rate(
        erc20_token=erc20_token,
        base_token=OCEAN_token,
        amount=ocean.to_wei(100),
        from_wallet=alice_wallet,
    )

    # Approve tokens for Bob
    fixed_price_address = ocean.fixed_rate_exchange.address
    erc20_token.approve(fixed_price_address, ocean.to_wei(100), bob_wallet)
    OCEAN_token.approve(fixed_price_address, ocean.to_wei(100), bob_wallet)

    tx_result = ocean.fixed_rate_exchange.buy_dt(
        exchange_id=exchange_id,
        datatoken_amount=ocean.to_wei(20),
        max_base_token_amount=ocean.to_wei(50),
        consume_market_address=ZERO_ADDRESS,
        consume_market_swap_fee_amount=0,
        from_wallet=bob_wallet,
    )
    assert tx_result, "failed buying data tokens at fixed rate for Bob"

    # Search for exchange_id from a specific block retrieved at 3rd step
    # for a certain data token address (e.g. erc20_token.address).
    datatoken_address = erc20_token.address
    nft_factory = ocean.get_nft_factory()
    logs = nft_factory.search_exchange_by_datatoken(
        ocean.fixed_rate_exchange,
        datatoken_address,
        exchange_owner=alice_wallet.address,
    )
    assert logs, f"No exchange has {datatoken_address} address."
    assert len(logs) == 1

    exchange_id = logs[0]
    assert exchange_id
    assert isinstance(exchange_id, bytes)
