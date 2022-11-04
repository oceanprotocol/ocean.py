#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from decimal import Decimal

import pytest

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
    config: dict,
    factory_deployer_wallet,
    consumer_wallet,
    another_consumer_wallet,
    publisher_wallet,
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
    config: dict,
    base_token_deployer_wallet,
    consumer_wallet,
    consume_market_swap_fee_collector,
    publisher_wallet,
    base_token_name: str,
    datatoken: Datatoken,
    publish_market_swap_fee: str,
    consume_market_swap_fee: str,
    bt_per_dt: str,
    with_mint: int,
):
    bt = Datatoken(config, get_address_of_type(config, base_token_name))
    dt = datatoken

    transfer_base_token_if_balance_lte(
        config=config,
        base_token_address=bt.address,
        from_wallet=base_token_deployer_wallet,
        recipient=publisher_wallet.address,
        min_balance=parse_units("1500", bt.decimals()),
        amount_to_transfer=parse_units("1500", bt.decimals()),
    )

    transfer_base_token_if_balance_lte(
        config=config,
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
    receipt = dt.create_fixed_rate(
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
        transaction_parameters={"from": publisher_wallet},
    )
    assert fixed_price_address == receipt.events["NewFixedRate"]["exchangeContract"]

    exchange = FixedRateExchange(config, fixed_price_address)

    exchange_id = receipt.events["NewFixedRate"]["exchangeId"]
    assert exchange_id == exchange.generateExchangeId(bt.address, dt.address)

    assert exchange.isActive(exchange_id)

    (
        market_fee,
        market_fee_collector,
        opc_fee,
        market_fee_available,
        ocean_fee_available,
    ) = exchange.getFeesInfo(exchange_id)

    # Verify fee collectors are configured correctly
    factory_router = FactoryRouter(config, get_address_of_type(config, "Router"))
    assert market_fee_collector == publisher_wallet.address

    # Verify fees are configured correctly
    if factory_router.isApprovedToken(bt.address):
        assert opc_fee == OPC_SWAP_FEE_APPROVED
    else:
        assert opc_fee == OPC_SWAP_FEE_NOT_APPROVED
    assert exchange.getOPCFee(bt.address) == opc_fee
    assert exchange.getOPCFee(bt.address) == factory_router.getOPCFee(bt.address)
    assert exchange.getMarketFee(exchange_id) == publish_market_swap_fee
    assert market_fee == publish_market_swap_fee

    # Verify 0 fees have been collected so far
    assert market_fee_available == 0
    assert ocean_fee_available == 0

    # Verify that rate is configured correctly
    assert exchange.getRate(exchange_id) == bt_per_dt_in_wei

    details = exchange.getExchange(exchange_id)

    # Verify exchange starting balance and supply.
    assert details[FixedRateExchangeDetails.BT_BALANCE] == 0
    assert details[FixedRateExchangeDetails.DT_BALANCE] == 0
    assert details[FixedRateExchangeDetails.BT_SUPPLY] == 0
    if with_mint == 1:
        assert details[FixedRateExchangeDetails.DT_SUPPLY] == dt.cap()
    else:
        assert details[FixedRateExchangeDetails.DT_SUPPLY] == 0

    # Grant infinite approvals for exchange to spend consumer's BT and DT
    dt.approve(exchange.address, MAX_WEI, {"from": consumer_wallet})
    bt.approve(exchange.address, MAX_WEI, {"from": consumer_wallet})

    # if the exchange cannot mint it's own datatokens,
    # Mint datatokens to publisher and
    # Grant infinite approval for exchange to spend publisher's datatokens
    if with_mint != 1:
        dt.mint(publisher_wallet.address, MAX_WEI, {"from": publisher_wallet})
        dt.approve(exchange.address, MAX_WEI, {"from": publisher_wallet})

    one_base_token = parse_units("1", bt.decimals())
    dt_per_bt_in_wei = to_wei(Decimal(1) / Decimal(bt_per_dt))

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "buy",
        base_token_to_datatoken(one_base_token, bt.decimals(), dt_per_bt_in_wei),
        config,
        exchange,
        exchange_id,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
    )

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "sell",
        base_token_to_datatoken(one_base_token, bt.decimals(), dt_per_bt_in_wei),
        config,
        exchange,
        exchange_id,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
    )

    # Collect BT
    collect_bt_or_dt_and_verify_balances(
        bt.address,
        config,
        exchange,
        exchange_id,
        consumer_wallet,
    )

    # Collect DT
    collect_bt_or_dt_and_verify_balances(
        dt.address,
        config,
        exchange,
        exchange_id,
        consumer_wallet,
    )

    # Update publish market swap fee
    new_publish_market_swap_fee = to_wei("0.09")
    exchange.updateMarketFee(
        exchange_id, new_publish_market_swap_fee, {"from": publisher_wallet}
    )
    fees_info = exchange.getFeesInfo(exchange_id)
    assert (
        fees_info[FixedRateExchangeFeesInfo.MARKET_FEE] == new_publish_market_swap_fee
    )

    # Increase rate (base tokens per datatoken) by 1
    new_bt_per_dt_in_wei = bt_per_dt_in_wei + to_wei("1")
    exchange.setRate(exchange_id, new_bt_per_dt_in_wei, {"from": publisher_wallet})
    assert exchange.getRate(exchange_id) == new_bt_per_dt_in_wei

    new_dt_per_bt_in_wei = to_wei(Decimal(1) / from_wei(new_bt_per_dt_in_wei))
    buy_or_sell_dt_and_verify_balances_swap_fees(
        "buy",
        base_token_to_datatoken(one_base_token, bt.decimals(), new_dt_per_bt_in_wei),
        config,
        exchange,
        exchange_id,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
    )

    # Update market fee collector to be the consumer
    new_market_fee_collector = consumer_wallet.address
    exchange.updateMarketFeeCollector(
        exchange_id, new_market_fee_collector, {"from": publisher_wallet}
    )
    assert (
        exchange.getFeesInfo(exchange_id)[
            FixedRateExchangeFeesInfo.MARKET_FEE_COLLECTOR
        ]
        == new_market_fee_collector
    )

    # Collect market fee
    collect_fee_and_verify_balances(
        FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE,
        config,
        exchange,
        exchange_id,
        consumer_wallet,
    )

    # Collect ocean fee
    collect_fee_and_verify_balances(
        FixedRateExchangeFeesInfo.OCEAN_FEE_AVAILABLE,
        config,
        exchange,
        exchange_id,
        consumer_wallet,
    )


def buy_or_sell_dt_and_verify_balances_swap_fees(
    buy_or_sell: str,
    dt_amount: int,
    config: dict,
    exchange: FixedRateExchange,
    exchange_id: bytes,
    consume_market_swap_fee_address: str,
    consume_market_swap_fee: int,
    consumer_wallet,
):
    exchange_info = exchange.getExchange(exchange_id)
    bt = Datatoken(config, exchange_info[FixedRateExchangeDetails.BASE_TOKEN])
    dt = Datatoken(config, exchange_info[FixedRateExchangeDetails.DATATOKEN])

    # Get balances before swap
    consumer_bt_balance_before = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance_before = dt.balanceOf(consumer_wallet.address)
    exchange_bt_balance_before = exchange_info[FixedRateExchangeDetails.BT_BALANCE]
    exchange_dt_balance_before = exchange_info[FixedRateExchangeDetails.DT_BALANCE]

    exchange_fees_info = exchange.getFeesInfo(exchange_id)

    publish_market_fee_bt_balance_before = exchange_fees_info[
        FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE
    ]
    opc_fee_bt_balance_before = exchange_fees_info[
        FixedRateExchangeFeesInfo.OCEAN_FEE_AVAILABLE
    ]
    consume_market_fee_bt_balance_before = bt.balanceOf(consume_market_swap_fee_address)

    if buy_or_sell == "buy":
        method = exchange.buyDT
        min_or_max_base_token = MAX_WEI
    else:
        method = exchange.sellDT
        min_or_max_base_token = 0

    # Buy or Sell DT
    receipt = method(
        exchange_id,
        dt_amount,
        min_or_max_base_token,
        consume_market_swap_fee_address,
        consume_market_swap_fee,
        {"from": consumer_wallet},
    )

    # Get exchange info again
    exchange_info = exchange.getExchange(exchange_id)

    # Get balances after swap
    consumer_bt_balance_after = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance_after = dt.balanceOf(consumer_wallet.address)
    exchange_bt_balance_after = exchange_info[FixedRateExchangeDetails.BT_BALANCE]
    exchange_dt_balance_after = exchange_info[FixedRateExchangeDetails.DT_BALANCE]

    # Get Swapped event
    swapped_event = receipt.events["Swapped"]

    # Assign "in" token and "out" token
    if swapped_event["tokenOutAddress"] == dt.address:
        in_token_amount = swapped_event["baseTokenSwappedAmount"]
        out_token_amount = swapped_event["datatokenSwappedAmount"]
        consumer_in_token_balance_before = consumer_bt_balance_before
        consumer_out_token_balance_before = consumer_dt_balance_before
        consumer_in_token_balance_after = consumer_bt_balance_after
        consumer_out_token_balance_after = consumer_dt_balance_after
    else:
        in_token_amount = swapped_event["datatokenSwappedAmount"]
        out_token_amount = swapped_event["baseTokenSwappedAmount"]
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
    if swapped_event["tokenOutAddress"] == dt.address:
        assert (
            exchange_bt_balance_before
            + swapped_event["baseTokenSwappedAmount"]
            - swapped_event["marketFeeAmount"]
            - swapped_event["oceanFeeAmount"]
            - swapped_event["consumeMarketFeeAmount"]
            == exchange_bt_balance_after
        )
        # When buying DT, exchange DT balance doesn't change because exchange mints DT
        assert exchange_dt_balance_before == exchange_dt_balance_after
    else:
        assert (
            exchange_bt_balance_before
            - swapped_event["baseTokenSwappedAmount"]
            - swapped_event["marketFeeAmount"]
            - swapped_event["oceanFeeAmount"]
            - swapped_event["consumeMarketFeeAmount"]
            == exchange_bt_balance_after
        )
        assert (
            exchange_dt_balance_before + swapped_event["datatokenSwappedAmount"]
            == exchange_dt_balance_after
        )

    # Get current fee balances
    # Exchange fees are always base tokens
    exchange_fees_info = exchange.getFeesInfo(exchange_id)
    publish_market_fee_bt_balance_after = exchange_fees_info[
        FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE
    ]
    opc_fee_bt_balance_after = exchange_fees_info[
        FixedRateExchangeFeesInfo.OCEAN_FEE_AVAILABLE
    ]
    consume_market_fee_bt_balance_after = bt.balanceOf(consume_market_swap_fee_address)

    # Check fees
    assert (
        publish_market_fee_bt_balance_before + swapped_event["marketFeeAmount"]
        == publish_market_fee_bt_balance_after
    )
    assert (
        opc_fee_bt_balance_before + swapped_event["oceanFeeAmount"]
        == opc_fee_bt_balance_after
    )
    assert (
        consume_market_fee_bt_balance_before + swapped_event["consumeMarketFeeAmount"]
        == consume_market_fee_bt_balance_after
    )


def collect_bt_or_dt_and_verify_balances(
    token_address: str,
    config: dict,
    exchange: FixedRateExchange,
    exchange_id: bytes,
    from_wallet,
):
    """Collet BT or Collect DT and verify balances"""
    exchange_info = exchange.getExchange(exchange_id)
    dt = Datatoken(config, exchange_info[FixedRateExchangeDetails.DATATOKEN])
    publish_market = dt.getPaymentCollector()

    if token_address == dt.address:
        token = dt
        balance_index = FixedRateExchangeDetails.DT_BALANCE
        method = exchange.collectDT
    else:
        token = Datatoken(config, exchange_info[FixedRateExchangeDetails.BASE_TOKEN])
        balance_index = FixedRateExchangeDetails.BT_BALANCE
        method = exchange.collectBT

    exchange_token_balance_before = exchange_info[balance_index]

    publish_market_token_balance_before = token.balanceOf(publish_market)

    method(exchange_id, exchange_token_balance_before, {"from": from_wallet})

    exchange_info = exchange.getExchange(exchange_id)
    exchange_token_balance_after = exchange_info[balance_index]

    publish_market_token_balance_after = token.balanceOf(publish_market)

    assert exchange_token_balance_after == 0
    assert (
        publish_market_token_balance_before + exchange_token_balance_before
        == publish_market_token_balance_after
    )


def collect_fee_and_verify_balances(
    balance_index: int,
    config: dict,
    exchange: FixedRateExchange,
    exchange_id: bytes,
    from_wallet,
):
    """Collet publish market swap fees or ocean community swap fees and verify balances"""
    exchange_info = exchange.getExchange(exchange_id)
    bt = Datatoken(config, exchange_info[FixedRateExchangeDetails.BASE_TOKEN])

    fees_info = exchange.getFeesInfo(exchange_id)
    exchange_fee_balance_before = fees_info[balance_index]

    if balance_index == FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE:
        method = exchange.collectMarketFee
        fee_collector = fees_info[FixedRateExchangeFeesInfo.MARKET_FEE_COLLECTOR]
    else:
        method = exchange.collectOceanFee
        fee_collector = get_opc_collector_address_from_exchange(exchange)

    fee_collector_bt_balance_before = bt.balanceOf(fee_collector)

    method(exchange_id, {"from": from_wallet})

    fees_info = exchange.getFeesInfo(exchange_id)
    exchange_fee_balance_after = fees_info[balance_index]

    fee_collector_bt_balance_after = bt.balanceOf(fee_collector)

    assert exchange_fee_balance_after == 0
    assert (
        fee_collector_bt_balance_before + exchange_fee_balance_before
        == fee_collector_bt_balance_after
    )
