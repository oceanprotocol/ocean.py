#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.models.models_structures import ErcCreateData, FixedData
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet


def test_fre_flow():
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
    nft_token = ocean.create_nft_token(
        "NFTToken1", "NFT1", alice_wallet, "https://oceanprotocol.com/nft/"
    )
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
        uints=[ocean.web3.toWei(200, "ether"), 0],
        bytess=[b""],
    )

    tx_id = nft_token.create_erc20(erc20_data, alice_wallet)
    tx_receipt = ocean.web3.eth.wait_for_transaction_receipt(tx_id)

    erc721_factory = ERC721FactoryContract(
        ocean.web3, get_address_of_type(config, "ERC721Factory")
    )

    registered_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        ocean.web3.eth.block_number,
        None,
    )

    erc20_address = registered_event[0].args.newTokenAddress
    print(f"token_address = '{erc20_address}'")

    # Mint the datatokens
    fixed_price_address = get_address_of_type(config, "FixedPrice")
    erc20_token = ERC20Token(ocean.web3, erc20_address)
    erc20_token.mint(alice_wallet.address, to_wei(100), alice_wallet)
    erc20_token.approve(fixed_price_address, to_wei(100), alice_wallet)

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

    OCEAN_token = ERC20Token(ocean.web3, ocean.OCEAN_address)

    # Create exchange_id for a new exchange
    fixed_rate_data = FixedData(
        fixed_price_address=fixed_price_address,
        addresses=[
            ocean.OCEAN_address,
            alice_wallet.address,
            alice_wallet.address,
            ZERO_ADDRESS,
        ],
        uints=[erc20_token.decimals(), OCEAN_token.decimals(), to_wei(1), int(1e15), 0],
    )
    tx_id = erc20_token.create_fixed_rate(
        fixed_data=fixed_rate_data, from_wallet=alice_wallet
    )
    tx_receipt = ocean.web3.eth.wait_for_transaction_receipt(tx_id)
    fixed_rate_event = erc20_token.get_event_log(
        ERC721FactoryContract.EVENT_NEW_FIXED_RATE,
        tx_receipt.blockNumber,
        ocean.web3.eth.block_number,
        None,
    )
    exchange_id = fixed_rate_event[0].args.exchangeId
    fixed_rate_exchange = FixedRateExchange(ocean.web3, fixed_price_address)

    erc20_token.approve(fixed_price_address, to_wei(100), bob_wallet)
    OCEAN_token.approve(fixed_price_address, to_wei(100), bob_wallet)

    tx_result = fixed_rate_exchange.buy_dt(
        exchange_id=exchange_id,
        data_token_amount=to_wei(20),
        max_base_token_amount=to_wei(50),
        from_wallet=bob_wallet,
    )
    assert tx_result, "failed buying data tokens at fixed rate for Bob"
