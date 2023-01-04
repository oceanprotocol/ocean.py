#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from decimal import Decimal

import pytest

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange, OneExchange
from ocean_lib.models.test.test_factory_router import (
    OPC_SWAP_FEE_APPROVED,
    OPC_SWAP_FEE_NOT_APPROVED,
)
from ocean_lib.ocean.util import from_wei, get_address_of_type, to_wei
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from tests.resources.helper_functions import (
    convert_bt_amt_to_dt,
    get_wallet,
    int_units,
    transfer_bt_if_balance_lte,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "bt_name, publish_market_swap_fee, consume_market_swap_fee, bt_per_dt, with_mint",
    [
        # Min fees
        ("Ocean", 0, 0, 1, True),
        ("MockUSDC", 0, 0, 1, True),
        # Happy path
        ("Ocean", 0.003, 0.005, 1, True),
        ("MockDAI", 0.003, 0.005, 1, True),
        ("MockUSDC", 0.003, 0.005, 1, True),
        # Max fees
        ("Ocean", 0.1, 0.1, 1, True),
        ("MockUSDC", 0.1, 0.1, 1, True),
        # Min rate. Rate must be => 1e10 wei
        ("Ocean", 0.003, 0.005, 0.000000010000000000, True),
        ("MockUSDC", 0.003, 0.005, 0.000000010000000000, True),
        # High rate. There is no maximum
        ("Ocean", 0.003, 0.005, 1000, True),
        ("MockUSDC", 0.003, 0.005, 1000, True),
        # with_mint = 0
        ("Ocean", 0.003, 0.005, 1, False),
        ("MockUSDC", 0.003, 0.005, 1, False),
    ],
)
def test_exchange_swap_fees(
    config: dict,
    factory_deployer_wallet,
    bob,
    alice,
    DT,
    bt_name: str,
    publish_market_swap_fee: str,
    consume_market_swap_fee: str,
    bt_per_dt: str,
    with_mint: bool,
):
    """
    Tests fixed rate exchange swap fees with OCEAN, DAI, and USDC as base token

    OCEAN is an approved base token with 18 decimals (OPC Fee = 0.1%)
    DAI is a non-approved base token with 18 decimals (OPC Fee = 0.2%)
    USDC is a non-approved base token with 6 decimals (OPC Fee = 0.2%)
    """
    bt_deployer_wallet = factory_deployer_wallet
    consume_market_swap_fee_collector = get_wallet(9)

    router = FactoryRouter(config, get_address_of_type(config, "Router"))
    FRE = FixedRateExchange(config, get_address_of_type(config, "FixedPrice"))

    bt = Datatoken(config, get_address_of_type(config, bt_name))
    dt = DT

    transfer_bt_if_balance_lte(
        config=config,
        bt_address=bt.address,
        from_wallet=bt_deployer_wallet,
        recipient=alice.address,
        min_balance=int_units("1500", bt.decimals()),
        amount_to_transfer=int_units("1500", bt.decimals()),
    )

    transfer_bt_if_balance_lte(
        config=config,
        bt_address=bt.address,
        from_wallet=bt_deployer_wallet,
        recipient=bob.address,
        min_balance=int_units("1500", bt.decimals()),
        amount_to_transfer=int_units("1500", bt.decimals()),
    )

    publish_market_swap_fee = to_wei(publish_market_swap_fee)
    consume_market_swap_fee = to_wei(consume_market_swap_fee)

    bt_per_dt_in_wei = to_wei(bt_per_dt)
    exchange = dt.create_exchange(
        rate=bt_per_dt_in_wei,
        base_token_addr=bt.address,
        tx_dict={"from": alice},
        owner_addr=alice.address,
        publish_market_fee_collector=alice.address,
        publish_market_fee=publish_market_swap_fee,
        with_mint=with_mint,
        allowed_swapper=ZERO_ADDRESS,
    )

    fees = exchange.exchange_fees_info

    # Verify fee collectors are configured correctly
    assert fees.publish_market_fee_collector == alice.address

    # Verify fees are configured correctly
    if router.isApprovedToken(bt.address):
        assert fees.opc_fee == OPC_SWAP_FEE_APPROVED
    else:
        assert fees.opc_fee == OPC_SWAP_FEE_NOT_APPROVED
    assert FRE.getOPCFee(bt.address) == fees.opc_fee == router.getOPCFee(bt.address)
    assert (
        exchange.get_publish_market_fee()
        == publish_market_swap_fee
        == fees.publish_market_fee
    )

    # Verify 0 fees have been collected so far
    assert fees.publish_market_fee_available == 0
    assert fees.ocean_fee_available == 0

    # Verify that rate is configured correctly
    assert exchange.get_rate() == bt_per_dt_in_wei

    # Verify exchange starting balance and supply
    details = exchange.details
    assert details.bt_balance == 0
    assert details.dt_balance == 0
    assert details.bt_supply == 0
    if with_mint:
        assert details.dt_supply == dt.cap()
    else:
        assert details.dt_supply == 0

    # Grant infinite approvals for exchange to spend bob's BT and DT
    dt.approve(exchange.address, MAX_UINT256, {"from": bob})
    bt.approve(exchange.address, MAX_UINT256, {"from": bob})

    # if the exchange cannot mint its own datatokens,
    # -mint datatokens to alice, and
    # -grant infinite approval for exchange to spend alice's datatokens
    if not with_mint:
        dt.mint(alice.address, MAX_UINT256, {"from": alice})
        dt.approve(exchange.address, MAX_UINT256, {"from": alice})

    one_base_token = int_units("1", bt.decimals())
    dt_per_bt_in_wei = to_wei(Decimal(1) / Decimal(bt_per_dt))

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "buy",
        convert_bt_amt_to_dt(one_base_token, bt.decimals(), dt_per_bt_in_wei),
        config,
        exchange,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        bob,
    )

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "sell",
        convert_bt_amt_to_dt(one_base_token, bt.decimals(), dt_per_bt_in_wei),
        config,
        exchange,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        bob,
    )

    # Collect BT
    collect_bt_or_dt_and_verify_balances(
        bt.address,
        config,
        exchange,
        bob,
    )

    # Collect DT
    collect_bt_or_dt_and_verify_balances(
        dt.address,
        config,
        exchange,
        bob,
    )

    # Update publish market swap fee
    new_publish_market_swap_fee = to_wei(0.09)
    exchange.update_publish_market_fee(new_publish_market_swap_fee, {"from": alice})
    assert exchange.exchange_fees_info.publish_market_fee == new_publish_market_swap_fee

    # Increase rate (base tokens per datatoken) by 1
    new_bt_per_dt_in_wei = bt_per_dt_in_wei + to_wei(1)
    exchange.set_rate(new_bt_per_dt_in_wei, {"from": alice})
    assert exchange.get_rate() == new_bt_per_dt_in_wei
    new_dt_per_bt_in_wei = to_wei(Decimal(1) / from_wei(new_bt_per_dt_in_wei))

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "buy",
        convert_bt_amt_to_dt(one_base_token, bt.decimals(), new_dt_per_bt_in_wei),
        config,
        exchange,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        bob,
    )

    # Make Bob the new market fee collector
    exchange.update_publish_market_fee_collector(bob.address, {"from": alice})

    # Collect publish market fee
    collect_fee_and_verify_balances(
        "publish_market_fee",
        config,
        exchange,
        bob,
    )

    # Collect ocean fee
    collect_fee_and_verify_balances(
        "ocean_fee",
        config,
        exchange,
        bob,
    )


def buy_or_sell_dt_and_verify_balances_swap_fees(
    action: str,  # "buy" or "sell"
    dt_amount: int,
    config: dict,
    exchange: OneExchange,
    consume_market_swap_fee_address: str,
    consume_market_swap_fee: int,
    bob,
):
    details = exchange.details
    bt = Datatoken(config, details.base_token)
    dt = Datatoken(config, details.datatoken)

    # Get balances before swap
    BT_bob1 = bt.balanceOf(bob)
    DT_bob1 = dt.balanceOf(bob)
    BT_exchange1 = details.bt_balance
    DT_exchange1 = details.dt_balance

    BT_publish_market_fee_avail1 = (
        exchange.exchange_fees_info.publish_market_fee_available
    )
    BT_opc_fee_avail1 = exchange.exchange_fees_info.ocean_fee_available
    BT_consume_market_fee_avail1 = bt.balanceOf(consume_market_swap_fee_address)

    if action == "buy":
        method = exchange.buy_DT
        min_or_max_bt = MAX_UINT256
    elif action == "sell":
        method = exchange.sell_DT
        min_or_max_bt = 0
    else:
        raise ValueError(action)

    # buy_DT() or sell_DT()
    tx = method(
        dt_amount,
        {"from": bob},
        min_or_max_bt,
        consume_market_swap_fee_address,
        consume_market_swap_fee,
    )

    # Get balances after swap
    details = exchange.details
    BT_bob2 = bt.balanceOf(bob)
    DT_bob2 = dt.balanceOf(bob)
    BT_exchange2 = details.bt_balance
    DT_exchange2 = details.dt_balance

    # Get Swapped event
    swapped_event = tx.events["Swapped"]
    BT_publish_market_fee_amt = swapped_event["marketFeeAmount"]
    BT_consume_market_fee_amt = swapped_event["consumeMarketFeeAmount"]
    BT_opc_fee_amt = swapped_event["oceanFeeAmount"]

    if swapped_event["tokenOutAddress"] == dt.address:
        BT_amt_swapped = swapped_event["baseTokenSwappedAmount"]
        DT_amt_swapped = swapped_event["datatokenSwappedAmount"]
        assert (BT_bob1 - BT_amt_swapped) == BT_bob2
        assert (DT_bob1 + DT_amt_swapped) == DT_bob2

        assert (
            BT_exchange1
            + BT_amt_swapped
            - BT_publish_market_fee_amt
            - BT_opc_fee_amt
            - BT_consume_market_fee_amt
            == BT_exchange2
        )
        # When buying DT, exchange DT bal doesn't change bc exchange *mints* DT
        assert DT_exchange1 == DT_exchange2

    elif swapped_event["tokenOutAddress"] == bt.address:
        DT_amt_swapped = swapped_event["datatokenSwappedAmount"]
        BT_amt_swapped = swapped_event["baseTokenSwappedAmount"]
        assert (DT_bob1 - DT_amt_swapped) == DT_bob2
        assert (BT_bob1 + BT_amt_swapped) == BT_bob2

        assert (
            BT_exchange1
            - BT_amt_swapped
            - BT_publish_market_fee_amt
            - BT_opc_fee_amt
            - BT_consume_market_fee_amt
            == BT_exchange2
        )
        assert DT_exchange1 + DT_amt_swapped == DT_exchange2

    else:
        raise ValueError(swapped_event["tokenOutAddress"])

    # Get current fee balances
    # Exchange fees are always base tokens
    BT_publish_market_fee_avail2 = (
        exchange.exchange_fees_info.publish_market_fee_available
    )
    BT_opc_fee_avail2 = exchange.exchange_fees_info.ocean_fee_available
    BT_consume_market_fee_avail2 = bt.balanceOf(consume_market_swap_fee_address)

    # Check fees
    assert (
        BT_publish_market_fee_avail1 + BT_publish_market_fee_amt
        == BT_publish_market_fee_avail2
    )
    assert (
        BT_consume_market_fee_avail1 + BT_consume_market_fee_amt
        == BT_consume_market_fee_avail2
    )
    assert BT_opc_fee_avail1 + BT_opc_fee_amt == BT_opc_fee_avail2


def collect_bt_or_dt_and_verify_balances(
    token_address: str,
    config: dict,
    exchange: OneExchange,
    from_wallet,
):
    """Collet BT or Collect DT and verify balances"""
    details = exchange.details
    dt = Datatoken(config, details.datatoken)
    bt = Datatoken(config, details.base_token)
    publish_market = dt.getPaymentCollector()

    if token_address == dt.address:
        exchange_token_bal1 = details.dt_balance
        token = dt
        balance_index = "dt_balance"
        method = exchange.collect_DT
    else:
        exchange_token_bal1 = details.bt_balance
        token = bt
        balance_index = "bt_balance"
        method = exchange.collect_BT

    publish_market_token_bal1 = token.balanceOf(publish_market)

    method(exchange_token_bal1, {"from": from_wallet})

    details = exchange.details
    if balance_index == "dt_balance":
        exchange_token_bal2 = details.dt_balance
    else:
        exchange_token_bal2 = details.bt_balance

    publish_market_token_bal2 = token.balanceOf(publish_market)

    assert exchange_token_bal2 == 0
    assert publish_market_token_bal1 + exchange_token_bal1 == publish_market_token_bal2


def collect_fee_and_verify_balances(
    fee_type: str,
    config: dict,
    exchange: OneExchange,
    from_wallet,
):
    """Collect publish_market  or opc fees, and verify balances"""
    FRE = FixedRateExchange(config, get_address_of_type(config, "FixedPrice"))
    bt = Datatoken(config, exchange.details.base_token)

    if fee_type == "publish_market_fee":
        BT_exchange_fee_avail1 = (
            exchange.exchange_fees_info.publish_market_fee_available
        )
        method = exchange.collect_publish_market_fee
        fee_collector = exchange.exchange_fees_info.publish_market_fee_collector
    elif fee_type == "ocean_fee":
        BT_exchange_fee_avail1 = exchange.fees_info.ocean_fee_available
        method = exchange.collect_opc_fee
        fee_collector = FRE.get_opc_collector()
    else:
        raise ValueError(fee_type)

    BT_fee_collector1 = bt.balanceOf(fee_collector)

    method({"from": from_wallet})

    if fee_type == "publish_market_fee":
        BT_exchange_fee_avail2 = (
            exchange.exchange_fees_info.publish_market_fee_available
        )
    else:
        BT_exchange_fee_avail2 = exchange.fees_info.ocean_fee_available

    BT_fee_collector2 = bt.balanceOf(fee_collector)

    assert BT_exchange_fee_avail2 == 0
    assert (BT_fee_collector1 + BT_exchange_fee_avail1) == BT_fee_collector2
