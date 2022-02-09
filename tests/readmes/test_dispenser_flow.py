#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.models_structures import (
    CreateErc20Data,
    DispenserData,
    CreateERC721DataNoDeployer,
)
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet


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
    erc721_token = ocean.create_nft_token("NFTToken1", "NFT1", alice_wallet)
    token_address = erc721_token.address
    assert token_address
    assert erc721_token.token_name() == "NFTToken1"
    assert erc721_token.symbol() == "NFT1"

    # Prepare data for ERC20 token
    cap = ocean.to_wei(100)
    erc20_data = CreateErc20Data(
        template_index=1,  # default value
        strings=["ERC20DT1", "ERC20DT1Symbol"],  # name & symbol for ERC20 token
        addresses=[
            alice_wallet.address,  # minter address
            alice_wallet.address,  # fee manager for this ERC20 token
            alice_wallet.address,  # publishing Market Address
            ZERO_ADDRESS,  # publishing Market Fee Token
        ],
        uints=[cap, 0],
        bytess=[b""],
    )
    erc20_token = erc721_token.create_datatoken(
        erc20_data=erc20_data, from_wallet=alice_wallet
    )

    assert erc20_token.address
    assert erc20_token.token_name() == "ERC20DT1"
    assert erc20_token.symbol() == "ERC20DT1Symbol"

    # Get the dispenser
    dispenser = ocean.dispenser

    max_amount = ocean.to_wei(50)
    dispenser_data = DispenserData(
        dispenser_address=dispenser.address,
        max_balance=max_amount,
        max_tokens=max_amount,
        with_mint=True,
        allowed_swapper=ZERO_ADDRESS,
    )

    erc20_token.create_dispenser(dispenser_data, from_wallet=alice_wallet)

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


def test_dispenser_flow_reduced():
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

    nft_factory = ocean.get_nft_factory()
    dispenser_address = ocean.dispenser.address

    cap = ocean.to_wei(10)
    erc721_data = CreateERC721DataNoDeployer(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,  # default value
        token_uri="https://oceanprotocol.com/nft/",
    )
    erc20_data = CreateErc20Data(
        template_index=1,  # default value
        strings=["ERC20DT1", "ERC20DT1Symbol"],  # name & symbol for ERC20 token
        addresses=[
            alice_wallet.address,  # minter address
            alice_wallet.address,  # fee manager for this ERC20 token
            alice_wallet.address,  # publishing Market Address
            ZERO_ADDRESS,  # publishing Market Fee Token
        ],
        uints=[cap, 0],
        bytess=[b""],
    )

    dispenser_data = DispenserData(
        dispenser_address=dispenser_address,
        max_tokens=ocean.to_wei("1"),
        max_balance=ocean.to_wei("1"),
        with_mint=True,
        allowed_swapper=ZERO_ADDRESS,
    )
    erc721_token, erc20_token = nft_factory.create_nft_erc_dispenser_in_one_call(
        erc721_data=erc721_data,
        erc20_data=erc20_data,
        dispenser_data=dispenser_data,
        from_wallet=alice_wallet,
    )
    assert erc721_token.address
    assert erc721_token.token_name() == "NFT"
    assert erc721_token.symbol() == "NFTSYMBOL"

    assert erc20_token.address
    assert erc20_token.token_name() == "ERC20DT1"
    assert erc20_token.symbol() == "ERC20DT1Symbol"

    dispenser_status = ocean.dispenser.status(erc20_token.address)
    assert dispenser_status[0] is True
    assert dispenser_status[1] == nft_factory.address
    assert dispenser_status[2] is True
