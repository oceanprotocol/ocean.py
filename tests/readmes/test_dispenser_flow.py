#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest

from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet


@pytest.mark.integration
def test_dispenser_flow_readme():
    """This test mirrors the dispenser-flow.md README.
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
    erc721_nft = ocean.create_erc721_nft("NFTToken1", "NFT1", alice_wallet)
    token_address = erc721_nft.address
    assert token_address
    assert erc721_nft.token_name() == "NFTToken1"
    assert erc721_nft.symbol() == "NFT1"

    # Prepare data for ERC20 token
    cap = ocean.to_wei(100)
    erc20_token = erc721_nft.create_datatoken(
        template_index=1,  # default value
        name="ERC20DT1",  # name for ERC20 token
        symbol="ERC20DT1Symbol",  # symbol for ERC20 token
        minter=alice_wallet.address,  # minter address
        fee_manager=alice_wallet.address,  # fee manager for this ERC20 token
        publish_market_address=alice_wallet.address,  # publishing Market Address
        publish_market_fee_token=ZERO_ADDRESS,  # publishing Market Fee Token
        cap=cap,
        publish_market_fee_amount=0,
        bytess=[b""],
        from_wallet=alice_wallet,
    )

    assert erc20_token.address
    assert erc20_token.token_name() == "ERC20DT1"
    assert erc20_token.symbol() == "ERC20DT1Symbol"

    # Get the dispenser
    dispenser = ocean.dispenser

    max_amount = ocean.to_wei(50)
    erc20_token.create_dispenser(
        dispenser_address=dispenser.address,
        max_balance=max_amount,
        max_tokens=max_amount,
        with_mint=True,
        allowed_swapper=ZERO_ADDRESS,
        from_wallet=alice_wallet,
    )

    dispenser_status = dispenser.status(erc20_token.address)
    assert dispenser_status[0] is True
    assert dispenser_status[1] == alice_wallet.address
    assert dispenser_status[2] is True

    initial_balance = erc20_token.balanceOf(alice_wallet.address)
    assert initial_balance == 0
    dispenser.dispense_tokens(
        erc20_token=erc20_token, amount=max_amount, consumer_wallet=alice_wallet
    )
    assert erc20_token.balanceOf(alice_wallet.address) == max_amount
