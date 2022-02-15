#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os

from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.models_structures import (
    CreateErc20Data,
    DispenserData,
    OrderParams,
)
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet


def test_erc20_enterprise_flow_with_dispenser():
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

    # Prepare data for ERC20 Enterprise token
    cap = ocean.to_wei(200)
    erc20_data = CreateErc20Data(
        template_index=2,  # this is the value for ERC20 Enterprise token
        strings=[
            "ERC20DT1",
            "ERC20DT1Symbol",
        ],  # name & symbol for ERC20 Enterprise token
        addresses=[
            alice_wallet.address,  # minter address
            alice_wallet.address,  # fee manager for this ERC20 Enterprise token
            alice_wallet.address,  # publishing Market Address
            ZERO_ADDRESS,  # publishing Market Fee Token
        ],
        uints=[cap, 0],
        bytess=[b""],
    )
    erc20_enterprise_token = erc721_nft.create_datatoken(
        erc20_data=erc20_data, from_wallet=alice_wallet
    )

    assert erc20_enterprise_token.address
    assert erc20_enterprise_token.token_name() == "ERC20DT1"
    assert erc20_enterprise_token.symbol() == "ERC20DT1Symbol"

    bob_private_key = os.getenv("TEST_PRIVATE_KEY2")
    bob_wallet = Wallet(
        ocean.web3,
        bob_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )

    # Verify that Bob has ganache ETH
    assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

    # Bob gets 1 DT from dispenser and then startsOrder, while burning that DT
    dispenser = ocean.dispenser
    dispenser_data = DispenserData(
        dispenser_address=dispenser.address,
        allowed_swapper=ZERO_ADDRESS,
        max_balance=ocean.to_wei(50),
        with_mint=True,
        max_tokens=ocean.to_wei(50),
    )
    tx = erc20_enterprise_token.create_dispenser(
        dispenser_data=dispenser_data, from_wallet=alice_wallet
    )
    assert tx, "Dispenser not created!"

    OCEAN_token = ocean.get_datatoken(ocean.OCEAN_address)
    consume_fee_amount = ocean.to_wei(2)
    erc20_enterprise_token.set_publishing_market_fee(
        publish_market_fee_address=bob_wallet.address,
        publish_market_fee_token=OCEAN_token.address,  # can be also USDC, DAI
        publish_market_fee_amount=consume_fee_amount,
        from_wallet=alice_wallet,
    )

    # Approve tokens
    OCEAN_token.approve(
        spender=erc20_enterprise_token.address,
        amount=consume_fee_amount,
        from_wallet=alice_wallet,
    )

    # Prepare data for order
    provider_fees = ocean.build_compute_provider_fees(
        provider_data={"timeout": 0},
        provider_fee_address=alice_wallet.address,
        provider_fee_token=OCEAN_token.address,
        provider_fee_amount=0,
        valid_until=1958133628,  # 2032
    )

    consume_fees = ocean.build_consume_fees(
        bob_wallet.address,
        erc20_enterprise_token.address,
        0,
    )

    initial_bob_balance = OCEAN_token.balanceOf(bob_wallet.address)
    order_params = OrderParams(bob_wallet.address, 1, provider_fees, consume_fees)

    erc20_enterprise_token.buy_from_dispenser_and_order(
        order_params=order_params,
        dispenser_address=dispenser.address,
        from_wallet=alice_wallet,
    )
    increased_balance = OCEAN_token.balanceOf(bob_wallet.address)
    assert initial_bob_balance < increased_balance


def test_erc20_enterprise_flow_with_fre():
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

    # Prepare data for ERC20 Enterprise token
    cap = ocean.to_wei(200)
    erc20_data = CreateErc20Data(
        template_index=2,  # this is the value for ERC20 Enterprise token
        strings=[
            "ERC20DT1",
            "ERC20DT1Symbol",
        ],  # name & symbol for ERC20 Enterprise token
        addresses=[
            alice_wallet.address,  # minter address
            alice_wallet.address,  # fee manager for this ERC20 Enterprise token
            alice_wallet.address,  # publishing Market Address
            ZERO_ADDRESS,  # publishing Market Fee Token
        ],
        uints=[cap, 0],
        bytess=[b""],
    )
    erc20_enterprise_token = erc721_nft.create_datatoken(
        erc20_data=erc20_data, from_wallet=alice_wallet
    )

    assert erc20_enterprise_token.address
    assert erc20_enterprise_token.token_name() == "ERC20DT1"
    assert erc20_enterprise_token.symbol() == "ERC20DT1Symbol"

    bob_private_key = os.getenv("TEST_PRIVATE_KEY2")
    bob_wallet = Wallet(
        ocean.web3,
        bob_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )

    # Verify that Bob has ganache ETH
    assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

    # Bob buys 1 DT from the FRE and then startsOrder, while burning that DT
    fixed_rate_exchange = ocean.fixed_rate_exchange
    OCEAN_token = ocean.get_datatoken(ocean.OCEAN_address)

    exchange_id = ocean.create_fixed_rate(
        erc20_token=erc20_enterprise_token,
        base_token=OCEAN_token,
        amount=ocean.to_wei(25),
        from_wallet=alice_wallet,
    )

    # Prepare data for order
    provider_fees = ocean.build_compute_provider_fees(
        provider_data={"timeout": 0},
        provider_fee_address=alice_wallet.address,
        provider_fee_token=OCEAN_token.address,
        provider_fee_amount=0,
        valid_until=1958133628,  # 2032
    )
    consume_fees = ocean.build_consume_fees(
        bob_wallet.address,
        erc20_enterprise_token.address,
        ocean.to_wei(2),
    )

    order_params = OrderParams(bob_wallet.address, 1, provider_fees, consume_fees)

    fre_params = (
        fixed_rate_exchange.address,
        exchange_id,
        ocean.to_wei(10),
        ocean.to_wei("0.001"),  # 1e15 => 0.1%
        bob_wallet.address,
    )
    erc20_enterprise_token.mint(alice_wallet.address, ocean.to_wei(20), alice_wallet)

    # Approve tokens
    OCEAN_token.approve(
        spender=erc20_enterprise_token.address,
        amount=ocean.to_wei(1000),
        from_wallet=alice_wallet,
    )

    # Transfer some ERC20 Enterprise tokens to Bob for buying from the FRE
    erc20_enterprise_token.transfer(bob_wallet.address, ocean.to_wei(15), alice_wallet)
    OCEAN_token.approve(
        spender=erc20_enterprise_token.address,
        amount=ocean.to_wei(1000),
        from_wallet=bob_wallet,
    )
    erc20_enterprise_token.approve(
        spender=erc20_enterprise_token.address,
        amount=ocean.to_wei(1000),
        from_wallet=bob_wallet,
    )
    tx_id = erc20_enterprise_token.buy_from_fre_and_order(
        order_params=order_params, fre_params=fre_params, from_wallet=bob_wallet
    )
    tx_receipt = ocean.web3.eth.wait_for_transaction_receipt(tx_id)
    assert tx_receipt.status == 1, "failed buying data tokens from FRE."
