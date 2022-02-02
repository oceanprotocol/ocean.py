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
    ProviderFees,
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
    nft_token = ocean.create_nft_token("NFTToken1", "NFT1", alice_wallet)
    token_address = nft_token.address
    assert token_address

    # Prepare data for ERC20 Enterprise token
    cap = ocean.to_wei(200)
    erc20_data = CreateErc20Data(
        template_index=2,  # default value
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
    erc20_enterprise_token = nft_token.create_datatoken(
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
    provider_fee_address = alice_wallet.address
    provider_fee_token = OCEAN_token.address
    provider_fee_amount = 0
    provider_data = json.dumps({"timeout": 0}, separators=(",", ":"))
    valid_until = 1958133628  # 2032
    provider_fees = ocean.build_compute_provider_fees(
        provider_data=provider_data,
        provider_fee_address=provider_fee_address,
        provider_fee_token=provider_fee_token,
        provider_fee_amount=provider_fee_amount,
        valid_until=valid_until,
    )

    # TODO: this will be handled in web3 py
    if isinstance(provider_fees, ProviderFees):
        provider_fees = tuple(provider_fees)

    initial_bob_balance = OCEAN_token.balanceOf(bob_wallet.address)
    order_params = OrderParams(
        bob_wallet.address,
        1,
        provider_fees,
    )

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
    nft_token = ocean.create_nft_token("NFTToken1", "NFT1", alice_wallet)
    token_address = nft_token.address
    assert token_address

    # Prepare data for ERC20 Enterprise token
    cap = ocean.to_wei(200)
    erc20_data = CreateErc20Data(
        template_index=2,  # default value
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
    erc20_enterprise_token = nft_token.create_datatoken(
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
    consume_fee_amount = ocean.to_wei(2)
    provider_fee_address = alice_wallet.address
    provider_fee_token = OCEAN_token.address
    provider_fee_amount = 0
    provider_data = json.dumps({"timeout": 0}, separators=(",", ":"))
    valid_until = 1958133628  # 2032
    provider_fees = ocean.build_compute_provider_fees(
        provider_data=provider_data,
        provider_fee_address=provider_fee_address,
        provider_fee_token=provider_fee_token,
        provider_fee_amount=provider_fee_amount,
        valid_until=valid_until,
    )

    # TODO: this will be handled in web3 py
    if isinstance(provider_fees, ProviderFees):
        provider_fees = tuple(provider_fees)

    order_params = OrderParams(
        bob_wallet.address,
        1,
        provider_fees,
    )

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
        amount=consume_fee_amount,
        from_wallet=alice_wallet,
    )
    erc20_enterprise_token.approve(
        spender=alice_wallet.address, amount=ocean.to_wei(20), from_wallet=alice_wallet
    )

    tx_id = erc20_enterprise_token.buy_from_fre_and_order(
        order_params=order_params, fre_params=fre_params, from_wallet=alice_wallet
    )
    tx_receipt = ocean.web3.eth.wait_for_transaction_receipt(tx_id)
    assert tx_receipt.status == 1, "failed buying data tokens from FRE."
