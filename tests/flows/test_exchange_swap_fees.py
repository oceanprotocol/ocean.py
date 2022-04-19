#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import Web3

from ocean_lib.config import Config
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import parse_units, to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import (
    deploy_erc721_erc20,
    transfer_base_token_if_balance_lte,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "base_token_name, publish_market_swap_fee, consume_market_swap_fee",
    [
        # Min fees
        ("Ocean", "0", "0"),
        ("MockDAI", "0", "0"),
        ("MockUSDC", "0", "0"),
        # Happy path
        ("Ocean", "0.003", "0.005"),
        ("MockDAI", "0.003", "0.005"),
        ("MockUSDC", "0.003", "0.005"),
        # Max fees
        ("Ocean", "0.1", "0.1"),
        ("MockDAI", "0.1", "0.1"),
        ("MockUSDC", "0.1", "0.1"),
    ],
)
def test_exchange_swap_fees(
    web3: Web3,
    config: Config,
    factory_deployer_wallet: Wallet,
    consumer_wallet: Wallet,
    another_consumer_wallet: Wallet,
    publisher_wallet: Wallet,
    base_token_name: str,
    publish_market_swap_fee: str,
    consume_market_swap_fee: str,
):
    """
    Tests fixed rate exchange swap fees with OCEAN, DAI, and USDC as base token

    OCEAN is an approved base token with 18 decimals (OPC Fee = 0.1%)
    DAI is a non-approved base token with 18 decimals (OPC Fee = 0.2%)
    USDC is a non-approved base token with 6 decimals (OPC Fee = 0.2%)
    """
    exchange_swap_fees(
        web3=web3,
        config=config,
        base_token_deployer_wallet=factory_deployer_wallet,
        consumer_wallet=consumer_wallet,
        consume_market_swap_fee_collector=another_consumer_wallet,
        publisher_wallet=publisher_wallet,
        base_token_name=base_token_name,
        publish_market_swap_fee=publish_market_swap_fee,
        consume_market_swap_fee=consume_market_swap_fee,
    )


def exchange_swap_fees(
    web3: Web3,
    config: Config,
    base_token_deployer_wallet: Wallet,
    consumer_wallet: Wallet,
    consume_market_swap_fee_collector: Wallet,
    publisher_wallet: Wallet,
    base_token_name: str,
    publish_market_swap_fee: str,
    consume_market_swap_fee: str,
):
    bt = ERC20Token(web3, get_address_of_type(config, base_token_name))

    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=base_token_deployer_wallet,
        recipient=publisher_wallet.address,
        min_balance=parse_units("1500", bt.decimals()),
        amount_to_transfer=parse_units("1500", bt.decimals()),
    )

    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=base_token_deployer_wallet,
        recipient=consumer_wallet.address,
        min_balance=parse_units("500", bt.decimals()),
        amount_to_transfer=parse_units("500", bt.decimals()),
    )

    _, dt = deploy_erc721_erc20(web3, config, publisher_wallet, publisher_wallet)

    publish_market_swap_fee = to_wei(publish_market_swap_fee)
    consume_market_swap_fee = to_wei(consume_market_swap_fee)

    tx = dt.create_fixed_rate(
        fixed_price_address=get_address_of_type(config, "FixedPrice"),
        base_token_address=bt.address,
        owner=publisher_wallet.address,
        publish_market_swap_fee_collector=publisher_wallet.address,
        allowed_swapper=ZERO_ADDRESS,
        base_token_decimals=bt.decimals(),
        datatoken_decimals=dt.decimals(),
        fixed_rate=to_wei(1),
        publish_market_swap_fee_amount=publish_market_swap_fee,
        with_mint=1,
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exchange_event = dt.get_event_log(
        dt.EVENT_NEW_FIXED_RATE,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    exchange_address = exchange_event[0].args.exchangeContract
    exchange = FixedRateExchange(web3, exchange_address)
