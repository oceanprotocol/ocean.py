#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from decimal import Decimal

import pytest
from web3 import Web3

from ocean_lib.config import Config
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.fixed_rate_exchange import (
    FixedRateExchange,
    FixedRateExchangeDetails,
    FixedRateExchangeFeesInfo,
)
from ocean_lib.models.test.test_factory_router import (
    OPC_SWAP_FEE_APPROVED,
    OPC_SWAP_FEE_NOT_APPROVED,
)
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import MAX_WEI, from_wei, parse_units, to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import get_opc_collector_address_from_exchange
from tests.resources.helper_functions import (
    base_token_to_datatoken,
    transfer_base_token_if_balance_lte,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "base_token_name, publish_market_swap_fee, consume_market_swap_fee, bt_per_dt, with_mint",
    [
        # Min fees
        ("Ocean", "0", "0", "1", 1),
        ("MockUSDC", "0", "0", "1", 1),
        # Happy path
        ("Ocean", "0.003", "0.005", "1", 1),
        ("MockDAI", "0.003", "0.005", "1", 1),
        ("MockUSDC", "0.003", "0.005", "1", 1),
        # Max fees
        ("Ocean", "0.1", "0.1", "1", 1),
        ("MockUSDC", "0.1", "0.1", "1", 1),
        # Min rate. Rate must be => 1e10 wei
        ("Ocean", "0.003", "0.005", "0.000000010000000000", 1),
        ("MockUSDC", "0.003", "0.005", "0.000000010000000000", 1),
        # High rate. There is no maximum
        ("Ocean", "0.003", "0.005", "1000", 1),
        ("MockUSDC", "0.003", "0.005", "1000", 1),
        # with_mint = 0
        ("Ocean", "0.003", "0.005", "1", 0),
        ("MockUSDC", "0.003", "0.005", "1", 0),
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
    datatoken: Datatoken,
    publish_market_swap_fee: str,
    consume_market_swap_fee: str,
    bt_per_dt: str,
    with_mint: int,
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
        datatoken=datatoken,
        publish_market_swap_fee=publish_market_swap_fee,
        consume_market_swap_fee=consume_market_swap_fee,
        bt_per_dt=bt_per_dt,
        with_mint=with_mint,
    )


def exchange_swap_fees(
    web3: Web3,
    config: Config,
    base_token_deployer_wallet: Wallet,
    consumer_wallet: Wallet,
    consume_market_swap_fee_collector: Wallet,
    publisher_wallet: Wallet,
    base_token_name: str,
    datatoken: Datatoken,
    publish_market_swap_fee: str,
    consume_market_swap_fee: str,
    bt_per_dt: str,
    with_mint: int,
):
    bt = Datatoken(web3, get_address_of_type(config, base_token_name))
    dt = datatoken

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
        min_balance=parse_units("1500", bt.decimals()),
        amount_to_transfer=parse_units("1500", bt.decimals()),
    )

    publish_market_swap_fee = to_wei(publish_market_swap_fee)
    consume_market_swap_fee = to_wei(consume_market_swap_fee)

    fixed_price_address = get_address_of_type(config, "FixedPrice")
    bt_per_dt_in_wei = to_wei(bt_per_dt)
    tx = dt.create_fixed_rate(
        fixed_price_address=fixed_price_address,
        base_token_address=bt.address,
        owner=publisher_wallet.address,
        publish_market_swap_fee_collector=publisher_wallet.address,
        allowed_swapper=ZERO_ADDRESS,
        base_token_decimals=bt.decimals(),
        datatoken_decimals=dt.decimals(),
        fixed_rate=bt_per_dt_in_wei,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        with_mint=with_mint,
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exchange_event = dt.get_event_log(
        dt.EVENT_NEW_FIXED_RATE,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert fixed_price_address == exchange_event[0].args.exchangeContract

    exchange = FixedRateExchange(web3, fixed_price_address)

    exchange_id = exchange_event[0].args.exchangeId
    assert exchange_id == exchange.generate_exchange_id(bt.address, dt.address)

    assert exchange.is_active(exchange_id)

    (
        market_fee,
        market_fee_collector,
        opc_fee,
        market_fee_available,
        ocean_fee_available,
    ) = exchange.get_fees_info(exchange_id)

    # Verify fee collectors are configured correctly
    factory_router = FactoryRouter(web3, get_address_of_type(config, "Router"))
    assert market_fee_collector == publisher_wallet.address

    # Verify fees are configured correctly
    if factory_router.is_approved_token(bt.address):
        assert opc_fee == OPC_SWAP_FEE_APPROVED
    else:
        assert opc_fee == OPC_SWAP_FEE_NOT_APPROVED
    assert exchange.get_opc_fee(bt.address) == opc_fee
    assert exchange.get_opc_fee(bt.address) == factory_router.get_opc_fee(bt.address)
    assert exchange.get_market_fee(exchange_id) == publish_market_swap_fee
    assert market_fee == publish_market_swap_fee

    # Verify 0 fees have been collected so far
    assert market_fee_available == 0
    assert ocean_fee_available == 0

    # Verify that rate is configured correctly
    assert exchange.get_rate(exchange_id) == bt_per_dt_in_wei

    details = exchange.get_exchange(exchange_id)

    # Verify exchange starting balance and supply.
    assert details[FixedRateExchangeDetails.BT_BALANCE] == 0
    assert details[FixedRateExchangeDetails.DT_BALANCE] == 0
    assert details[FixedRateExchangeDetails.BT_SUPPLY] == 0
    if with_mint == 1:
        assert details[FixedRateExchangeDetails.DT_SUPPLY] == dt.cap()
    else:
        assert details[FixedRateExchangeDetails.DT_SUPPLY] == 0

    # Grant infinite approvals for exchange to spend consumer's BT and DT
    dt.approve(exchange.address, MAX_WEI, consumer_wallet)
    bt.approve(exchange.address, MAX_WEI, consumer_wallet)

    # if the exchange cannot mint it's own datatokens,
    # Mint datatokens to publisher and
    # Grant infinite approval for exchange to spend publisher's datatokens
    if with_mint != 1:
        dt.mint(publisher_wallet.address, MAX_WEI, publisher_wallet)
        dt.approve(exchange.address, MAX_WEI, publisher_wallet)

    one_base_token = parse_units("1", bt.decimals())
    dt_per_bt_in_wei = to_wei(Decimal(1) / Decimal(bt_per_dt))

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "buy",
        base_token_to_datatoken(one_base_token, bt.decimals(), dt_per_bt_in_wei),
        web3,
        exchange,
        exchange_id,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
    )

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "sell",
        base_token_to_datatoken(one_base_token, bt.decimals(), dt_per_bt_in_wei),
        web3,
        exchange,
        exchange_id,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
    )

    # Collect BT
    collect_bt_or_dt_and_verify_balances(
        bt.address,
        web3,
        exchange,
        exchange_id,
        consumer_wallet,
    )

    # Collect DT
    collect_bt_or_dt_and_verify_balances(
        dt.address,
        web3,
        exchange,
        exchange_id,
        consumer_wallet,
    )

    # Update publish market swap fee
    new_publish_market_swap_fee = to_wei("0.09")
    exchange.update_market_fee(
        exchange_id, new_publish_market_swap_fee, publisher_wallet
    )
    fees_info = exchange.get_fees_info(exchange_id)
    assert (
        fees_info[FixedRateExchangeFeesInfo.MARKET_FEE] == new_publish_market_swap_fee
    )

    # Increase rate (base tokens per datatoken) by 1
    new_bt_per_dt_in_wei = bt_per_dt_in_wei + to_wei("1")
    exchange.set_rate(exchange_id, new_bt_per_dt_in_wei, publisher_wallet)
    assert exchange.get_rate(exchange_id) == new_bt_per_dt_in_wei

    new_dt_per_bt_in_wei = to_wei(Decimal(1) / from_wei(new_bt_per_dt_in_wei))
    buy_or_sell_dt_and_verify_balances_swap_fees(
        "buy",
        base_token_to_datatoken(one_base_token, bt.decimals(), new_dt_per_bt_in_wei),
        web3,
        exchange,
        exchange_id,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
    )

    # Update market fee collector to be the consumer
    new_market_fee_collector = consumer_wallet.address
    exchange.update_market_fee_collector(
        exchange_id, new_market_fee_collector, publisher_wallet
    )
    assert (
        exchange.get_fees_info(exchange_id)[
            FixedRateExchangeFeesInfo.MARKET_FEE_COLLECTOR
        ]
        == new_market_fee_collector
    )

    # Collect market fee
    collect_fee_and_verify_balances(
        FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE,
        web3,
        exchange,
        exchange_id,
        consumer_wallet,
    )

    # Collect ocean fee
    collect_fee_and_verify_balances(
        FixedRateExchangeFeesInfo.OCEAN_FEE_AVAILABLE,
        web3,
        exchange,
        exchange_id,
        consumer_wallet,
    )


def buy_or_sell_dt_and_verify_balances_swap_fees(
    buy_or_sell: str,
    dt_amount: int,
    web3: Web3,
    exchange: FixedRateExchange,
    exchange_id: bytes,
    consume_market_swap_fee_address: str,
    consume_market_swap_fee: int,
    consumer_wallet: Wallet,
):
    exchange_info = exchange.get_exchange(exchange_id)
    bt = Datatoken(web3, exchange_info[FixedRateExchangeDetails.BASE_TOKEN])
    dt = Datatoken(web3, exchange_info[FixedRateExchangeDetails.DATATOKEN])

    # Get balances before swap
    consumer_bt_balance_before = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance_before = dt.balanceOf(consumer_wallet.address)
    exchange_bt_balance_before = exchange_info[FixedRateExchangeDetails.BT_BALANCE]
    exchange_dt_balance_before = exchange_info[FixedRateExchangeDetails.DT_BALANCE]

    exchange_fees_info = exchange.get_fees_info(exchange_id)

    publish_market_fee_bt_balance_before = exchange_fees_info[
        FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE
    ]
    opc_fee_bt_balance_before = exchange_fees_info[
        FixedRateExchangeFeesInfo.OCEAN_FEE_AVAILABLE
    ]
    consume_market_fee_bt_balance_before = bt.balanceOf(consume_market_swap_fee_address)

    if buy_or_sell == "buy":
        method = exchange.buy_dt
        min_or_max_base_token = MAX_WEI
    else:
        method = exchange.sell_dt
        min_or_max_base_token = 0

    # Buy or Sell DT
    tx = method(
        exchange_id,
        dt_amount,
        min_or_max_base_token,
        consume_market_swap_fee_address,
        consume_market_swap_fee,
        consumer_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    # Get exchange info again
    exchange_info = exchange.get_exchange(exchange_id)

    # Get balances after swap
    consumer_bt_balance_after = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance_after = dt.balanceOf(consumer_wallet.address)
    exchange_bt_balance_after = exchange_info[FixedRateExchangeDetails.BT_BALANCE]
    exchange_dt_balance_after = exchange_info[FixedRateExchangeDetails.DT_BALANCE]

    # Get Swapped event
    swapped_event = exchange.get_event_log(
        exchange.EVENT_SWAPPED, tx_receipt.blockNumber, web3.eth.block_number, None
    )
    swapped_event_args = swapped_event[0].args

    # Assign "in" token and "out" token
    if swapped_event_args.tokenOutAddress == dt.address:
        in_token_amount = swapped_event_args.baseTokenSwappedAmount
        out_token_amount = swapped_event_args.datatokenSwappedAmount
        consumer_in_token_balance_before = consumer_bt_balance_before
        consumer_out_token_balance_before = consumer_dt_balance_before
        consumer_in_token_balance_after = consumer_bt_balance_after
        consumer_out_token_balance_after = consumer_dt_balance_after
    else:
        in_token_amount = swapped_event_args.datatokenSwappedAmount
        out_token_amount = swapped_event_args.baseTokenSwappedAmount
        consumer_in_token_balance_before = consumer_dt_balance_before
        consumer_out_token_balance_before = consumer_bt_balance_before
        consumer_in_token_balance_after = consumer_dt_balance_after
        consumer_out_token_balance_after = consumer_bt_balance_after

    # Check consumer balances
    assert (
        consumer_in_token_balance_before - in_token_amount
        == consumer_in_token_balance_after
    )
    assert (
        consumer_out_token_balance_before + out_token_amount
        == consumer_out_token_balance_after
    )

    # Check exchange balances
    if swapped_event_args.tokenOutAddress == dt.address:
        assert (
            exchange_bt_balance_before
            + swapped_event_args.baseTokenSwappedAmount
            - swapped_event_args.marketFeeAmount
            - swapped_event_args.oceanFeeAmount
            - swapped_event_args.consumeMarketFeeAmount
            == exchange_bt_balance_after
        )
        # When buying DT, exchange DT balance doesn't change because exchange mints DT
        assert exchange_dt_balance_before == exchange_dt_balance_after
    else:
        assert (
            exchange_bt_balance_before
            - swapped_event_args.baseTokenSwappedAmount
            - swapped_event_args.marketFeeAmount
            - swapped_event_args.oceanFeeAmount
            - swapped_event_args.consumeMarketFeeAmount
            == exchange_bt_balance_after
        )
        assert (
            exchange_dt_balance_before + swapped_event_args.datatokenSwappedAmount
            == exchange_dt_balance_after
        )

    # Get current fee balances
    # Exchange fees are always base tokens
    exchange_fees_info = exchange.get_fees_info(exchange_id)
    publish_market_fee_bt_balance_after = exchange_fees_info[
        FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE
    ]
    opc_fee_bt_balance_after = exchange_fees_info[
        FixedRateExchangeFeesInfo.OCEAN_FEE_AVAILABLE
    ]
    consume_market_fee_bt_balance_after = bt.balanceOf(consume_market_swap_fee_address)

    # Check fees
    assert (
        publish_market_fee_bt_balance_before + swapped_event_args.marketFeeAmount
        == publish_market_fee_bt_balance_after
    )
    assert (
        opc_fee_bt_balance_before + swapped_event_args.oceanFeeAmount
        == opc_fee_bt_balance_after
    )
    assert (
        consume_market_fee_bt_balance_before + swapped_event_args.consumeMarketFeeAmount
        == consume_market_fee_bt_balance_after
    )


def collect_bt_or_dt_and_verify_balances(
    token_address: str,
    web3: Web3,
    exchange: FixedRateExchange,
    exchange_id: bytes,
    from_wallet: Wallet,
):
    """Collet BT or Collect DT and verify balances"""
    exchange_info = exchange.get_exchange(exchange_id)
    dt = Datatoken(web3, exchange_info[FixedRateExchangeDetails.DATATOKEN])
    publish_market = dt.get_payment_collector()

    if token_address == dt.address:
        token = dt
        balance_index = FixedRateExchangeDetails.DT_BALANCE
        method = exchange.collect_dt
    else:
        token = Datatoken(web3, exchange_info[FixedRateExchangeDetails.BASE_TOKEN])
        balance_index = FixedRateExchangeDetails.BT_BALANCE
        method = exchange.collect_bt

    exchange_token_balance_before = exchange_info[balance_index]

    publish_market_token_balance_before = token.balanceOf(publish_market)

    method(exchange_id, exchange_token_balance_before, from_wallet)

    exchange_info = exchange.get_exchange(exchange_id)
    exchange_token_balance_after = exchange_info[balance_index]

    publish_market_token_balance_after = token.balanceOf(publish_market)

    assert exchange_token_balance_after == 0
    assert (
        publish_market_token_balance_before + exchange_token_balance_before
        == publish_market_token_balance_after
    )


def collect_fee_and_verify_balances(
    balance_index: int,
    web3: Web3,
    exchange: FixedRateExchange,
    exchange_id: bytes,
    from_wallet: Wallet,
):
    """Collet publish market swap fees or ocean community swap fees and verify balances"""
    exchange_info = exchange.get_exchange(exchange_id)
    bt = Datatoken(web3, exchange_info[FixedRateExchangeDetails.BASE_TOKEN])

    fees_info = exchange.get_fees_info(exchange_id)
    exchange_fee_balance_before = fees_info[balance_index]

    if balance_index == FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE:
        method = exchange.collect_market_fee
        fee_collector = fees_info[FixedRateExchangeFeesInfo.MARKET_FEE_COLLECTOR]
    else:
        method = exchange.collect_ocean_fee
        fee_collector = get_opc_collector_address_from_exchange(exchange)

    fee_collector_bt_balance_before = bt.balanceOf(fee_collector)

    method(exchange_id, from_wallet)

    fees_info = exchange.get_fees_info(exchange_id)
    exchange_fee_balance_after = fees_info[balance_index]

    fee_collector_bt_balance_after = bt.balanceOf(fee_collector)

    assert exchange_fee_balance_after == 0
    assert (
        fee_collector_bt_balance_before + exchange_fee_balance_before
        == fee_collector_bt_balance_after
    )
