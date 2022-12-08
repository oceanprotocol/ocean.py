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
from ocean_lib.ocean.util import get_address_of_type, to_wei, from_wei
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from tests.resources.ddo_helpers import get_opc_collector_address_from_exchange
from tests.resources.helper_functions import (
    convert_bt_amt_to_dt,
    int_units,
    transfer_bt_if_bal_lte,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "bt_name, pub_mkt_swap_fee, consume_mkt_swap_fee, bt_per_dt, with_mint",
    [
        # Min fees
        ("Ocean", 0, 0, 1, 1),
        ("MockUSDC", 0, 0, 1, 1),
        
        # Happy path
        ("Ocean", 0.003, 0.005, 1, 1),
        ("MockDAI", 0.003, 0.005, 1, 1),
        ("MockUSDC", 0.003, 0.005, 1, 1),
        
        # Max fees
        ("Ocean", 0.1, 0.1, 1, 1),
        ("MockUSDC", 0.1, 0.1, 1, 1),
        
        # Min rate. Rate must be => 1e10 wei
        ("Ocean", 0.003, 0.005, 0.000000010000000000, 1),
        ("MockUSDC", 0.003, 0.005, 0.000000010000000000, 1),
        
        # High rate. There is no maximum
        ("Ocean", 0.003, 0.005, 1000, 1),
        ("MockUSDC", 0.003, 0.005, 1000, 1),
        
        # with_mint = 0
        ("Ocean", 0.003, 0.005, 1, 0),
        ("MockUSDC", 0.003, 0.005, 1, 0),
    ],
)
def test_exchange_swap_fees(
    config: dict,
    factory_deployer_wallet,
    bob,
    carlos,
    alice,
    bt_name: str,
    datatoken: Datatoken,
    pub_mkt_swap_fee: str,
    consume_mkt_swap_fee: str,
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
        bt_deployer_wallet=factory_deployer_wallet,
        bob=bob,
        consume_mkt_swap_fee_collector=carlos,
        alice=alice,
        bt_name=bt_name,
        datatoken=datatoken,
        pub_mkt_swap_fee=pub_mkt_swap_fee,
        consume_mkt_swap_fee=consume_mkt_swap_fee,
        bt_per_dt=bt_per_dt,
        with_mint=with_mint,
    )


def exchange_swap_fees(
    config: dict,
    bt_deployer_wallet,
    bob,
    consume_mkt_swap_fee_collector,
    alice,
    bt_name: str,
    datatoken: Datatoken,
    pub_mkt_swap_fee: str,
    consume_mkt_swap_fee: str,
    bt_per_dt: str,
    with_mint: int,
):
    router = FactoryRouter(config, get_address_of_type(config, "Router"))
    FRE = FixedRateExchange(config, get_address_of_type(config, "FixedPrice"))
    
    bt = Datatoken(config, get_address_of_type(config, bt_name))
    dt = datatoken

    transfer_bt_if_bal_lte(
        config=config,
        bt_address=bt.address,
        from_wallet=bt_deployer_wallet,
        recipient=alice.address,
        min_balance=int_units("1500", bt.decimals()),
        amount_to_transfer=int_units("1500", bt.decimals()),
    )

    transfer_bt_if_bal_lte(
        config=config,
        bt_address=bt.address,
        from_wallet=bt_deployer_wallet,
        recipient=bob.address,
        min_balance=int_units("1500", bt.decimals()),
        amount_to_transfer=int_units("1500", bt.decimals()),
    )

    pub_mkt_swap_fee = to_wei(pub_mkt_swap_fee)
    consume_mkt_swap_fee = to_wei(consume_mkt_swap_fee)

    bt_per_dt_in_wei = to_wei(bt_per_dt)
    exchange, tx = dt.create_exchange(
        price=bt_per_dt_in_wei,
        base_token_addr=bt.address,
        owner_addr=alice.address,
        market_fee_collector_addr=alice.address,
        market_fee=pub_mkt_swap_fee,
        with_mint=with_mint,
        tx_dict={"from": alice},
    )

    fees = exchange.fees_info
    
    # Verify fee collectors are configured correctly
    assert fees.market_fee_collector == alice.address

    # Verify fees are configured correctly
    if router.isApprovedToken(bt.address):
        assert fees.opc_fee == OPC_SWAP_FEE_APPROVED
    else:
        assert fees.opc_fee == OPC_SWAP_FEE_NOT_APPROVED
    assert FRE.getOPCFee(bt.address) == fees.opc_fee \
        == router.getOPCFee(bt.address)
    assert exchange.getMarketFee(exchange_id) == pub_mkt_swap_fee \
        == fees.market_fee

    # Verify 0 fees have been collected so far
    assert fees.market_fee_available == 0
    assert fees.ocean_fee_available == 0

    # Verify that rate is configured correctly
    assert from_wei(exchange.get_rate()) == bt_per_dt

    details = exchange.details

    # Verify exchange starting balance and supply.
    assert details.bt_balance == 0
    assert details.dt_balance == 0
    assert details.bt_supply == 0
    if with_mint == 1:
        assert details.dt_supply == dt.cap()
    else:
        assert details.dt_supply == 0

    # Grant infinite approvals for exchange to spend bob's BT and DT
    dt.approve(exchange.address, MAX_UINT256, {"from": bob})
    bt.approve(exchange.address, MAX_UINT256, {"from": bob})

    # if the exchange cannot mint its own datatokens,
    # -mint datatokens to alice, and
    # -grant infinite approval for exchange to spend alice's datatokens
    if with_mint != 1:
        dt.mint(alice.address, MAX_UINT256, {"from": alice})
        dt.approve(exchange.address, MAX_UINT256, {"from": alice})

    one_bt_in_wei = int_units("1", bt.decimals())
    dt_per_bt_in_wei = to_wei(Decimal(1) / Decimal(bt_per_dt))

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "buy",
        convert_bt_amt_to_dt(one_bt_in_wei, bt.decimals(), dt_per_bt_in_wei),
        config,
        exchange,
        consume_mkt_swap_fee_collector.address,
        consume_mkt_swap_fee,
        bob,
    )

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "sell",
        convert_bt_amt_to_dt(one_bt_in_wei, bt.decimals(), dt_per_bt_in_wei),
        config,
        exchange,
        consume_mkt_swap_fee_collector.address,
        consume_mkt_swap_fee,
        bob,
    )

    # Collect BT
    collect_bt_or_dt_and_verify_balances(
        bt.address,
        config,
        exchange,
        exchange_id,
        bob,
    )

    # Collect DT
    collect_bt_or_dt_and_verify_balances(
        dt.address,
        config,
        exchange,
        exchange_id,
        bob,
    )

    # Update publish market swap fee
    new_pub_mkt_swap_fee = to_wei(0.09)
    exchange.update_market_fee(new_pub_mkt_swap_fee, {"from": alice})
    assert exchange.fees_info.market_fee == new_pub_mkt_swap_fee

    # Increase rate (base tokens per datatoken) by 1
    new_bt_per_dt = bt_per_dt + 1.0
    new_dt_per_bt = 1.0 / new_bt_per_dt
    
    exchange.set_rate(to_wei(new_bt_per_dt), {"from": alice})

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "buy",
        convert_bt_amt_to_dt(one_bt_in_wei, bt.decimals(), to_wei(new_dt_per_bt)),
        config,
        exchange,
        consume_mkt_swap_fee_collector.address,
        consume_mkt_swap_fee,
        bob,
    )

    # Make Bob the new market fee collector
    exchange.update_market_fee_collector(bob.address, {"from": alice})

    # Collect market fee
    collect_fee_and_verify_balances(
        "market_fee",
        config,
        exchange,
        exchange_id,
        bob,
    )

    # Collect ocean fee
    collect_fee_and_verify_balances(
        "ocean_fee",
        config,
        exchange,
        exchange_id,
        bob,
    )


def buy_or_sell_dt_and_verify_balances_swap_fees(
    action: str,
    dt_amount: int,
    config: dict,
    exchange: OneExchange,
    consume_mkt_swap_fee_address: str,
    consume_mkt_swap_fee: int,
    bob,
):
    details = exchange.details
    bt = Datatoken(config, details.base_token)
    dt = Datatoken(config, details.datatoken)
    
    # Get balances before swap
    bob_bt_bal1 = bt.balanceOf(bob.address)
    bob_dt_bal1 = dt.balanceOf(bob.address)
    exchange_bt_bal1 = details.bt_balance
    exchange_dt_bal1 = details.dt_balance

    fees = exchange.fees_info

    pub_mkt_fee_bt_bal1 = fees.market_fee_available
    opc_fee_bt_bal1 = fees.ocean_fee_available
    consume_mkt_fee_bt_bal1 = bt.balanceOf(consume_mkt_swap_fee_address)

    if action == "buy":
        method = exchange.buy_DT
        min_or_max_base_token = MAX_UINT256
    elif action == "sell":
        method = exchange.sell_DT
        min_or_max_base_token = 0
    else:
        raise ValueError(action)    

    # Buy or Sell DT
    tx = method(
        dt_amount,
        min_or_max_base_token,
        consume_mkt_swap_fee_address,
        consume_mkt_swap_fee,
        {"from": bob},
    )

    # Get balances after swap
    details = exchange.details
    bob_bt_bal2 = bt.balanceOf(bob.address)
    bob_dt_bal2 = dt.balanceOf(bob.address)
    exchange_bt_bal2 = details.bt_balance
    exchange_dt_bal2 = details.dt_balance

    # Get Swapped event
    swapped_event = tx.events["Swapped"]

    # Assign "in" token and "out" token
    if swapped_event["tokenOutAddress"] == dt.address:
        in_token_amount = swapped_event["baseTokenSwappedAmount"]
        out_token_amount = swapped_event["datatokenSwappedAmount"]
        bob_in_token_bal1 = bob_bt_bal1
        bob_out_token_bal1 = bob_dt_bal1
        bob_in_token_bal2 = bob_bt_bal2
        bob_out_token_bal2 = bob_dt_bal2
    else:
        in_token_amount = swapped_event["datatokenSwappedAmount"]
        out_token_amount = swapped_event["baseTokenSwappedAmount"]
        bob_in_token_bal1 = bob_dt_bal1
        bob_out_token_bal1 = bob_bt_bal1
        bob_in_token_bal2 = bob_dt_bal2
        bob_out_token_bal2 = bob_bt_bal2

    # Check bob balances
    assert (bob_in_token_bal1 - in_token_amount) == bob_in_token_bal2
    assert (bob_out_token_bal1 + out_token_amount) == bob_out_token_bal2

    # Check exchange balances
    if swapped_event["tokenOutAddress"] == dt.address:
        assert (
            exchange_bt_bal1
            + swapped_event["baseTokenSwappedAmount"]
            - swapped_event["marketFeeAmount"]
            - swapped_event["oceanFeeAmount"]
            - swapped_event["consumeMarketFeeAmount"]
            == exchange_bt_bal2
        )
        # When buying DT, exchange DT bal doesn't change bc exchange *mints* DT
        assert exchange_dt_bal1 == exchange_dt_bal2
    else:
        assert (
            exchange_bt_bal1
            - swapped_event["baseTokenSwappedAmount"]
            - swapped_event["marketFeeAmount"]
            - swapped_event["oceanFeeAmount"]
            - swapped_event["consumeMarketFeeAmount"]
            == exchange_bt_bal2
        )
        assert (
            exchange_dt_bal1 + swapped_event["datatokenSwappedAmount"]
            == exchange_dt_bal2
        )

    # Get current fee balances
    # Exchange fees are always base tokens
    fees = exchange.fees_info
    pub_mkt_fee_bt_bal2 = fees.market_fee_available
    opc_fee_bt_bal2 = fees.ocean_fee_available
    consume_mkt_fee_bt_bal2 = bt.balanceOf(consume_mkt_swap_fee_address)

    # Check fees
    assert (
        pub_mkt_fee_bt_bal1 + swapped_event["marketFeeAmount"]
        == pub_mkt_fee_bt_bal2
    )
    assert (
        opc_fee_bt_bal1 + swapped_event["oceanFeeAmount"]
        == opc_fee_bt_bal2
    )
    assert (
        consume_mkt_fee_bt_bal1 + swapped_event["consumeMarketFeeAmount"]
        == consume_mkt_fee_bt_bal2
    )


def collect_bt_or_dt_and_verify_balances(
    token_address: str,
    config: dict,
    exchange: FixedRateExchange,
    exchange_id: bytes,
    from_wallet,
):
    """Collet BT or Collect DT and verify balances"""
    details = exchange.details
    dt = Datatoken(config, details.datatoken)
    bt = Datatoken(config, details.base_token)
    pub_mkt = dt.getPaymentCollector()

    if token_address == dt.address:
        exchange_token_bal1 = exchange_info.dt_balance
        token = dt
        balance_index = "dt_balance"
        method = exchange.collect_DT
    else:
        exchange_token_bal1 = exchange_info.bt_balance
        token = bt
        balance_index = "bt_balance"
        method = exchange.collect_BT

    pub_mkt_token_bal1 = token.balanceOf(pub_mkt)

    method(exchange_token_bal1, {"from": from_wallet})

    details = exchange.details
    if balance_index === "dt_balance":
        exchange_token_bal2 = details.dt_balance
    else:
        exchange_token_bal2 = details.bt_balance

    pub_mkt_token_bal2 = token.balanceOf(pub_mkt)

    assert exchange_token_bal2 == 0
    assert (
        pub_mkt_token_bal1 + exchange_token_bal1
        == pub_mkt_token_bal2
    )


def collect_fee_and_verify_balances(
    fee_type: str,
    config: dict,
    exchange: FixedRateExchange,
    exchange_id: bytes,
    from_wallet,
):
    """Collet publish market swap fees or ocean community swap fees and verify balances"""
    FRE = FixedRateExchange(config, get_address_of_type(config, "FixedPrice"))
    details = exchange.details
    bt = Datatoken(config, details.base_token)

    fees = exchange.fees_info
    if fee_type == "market_fee":
        exchange_fee_bal1 = fees.market_fee
        method = exchange.collect_market_fee
        fee_collector = fees_info.market_fee_collector
    elif fee_type == "ocean_fee":
        exchange_fee_bal1 = fees.opc_fee
        method = exchange.collect_ocean_fee
        fee_collector = get_opc_collector_address_from_exchange(FRE)
    else:
        raise ValueError(fee_type)

    fee_collector_bt_bal1 = bt.balanceOf(fee_collector)

    method(exchange_id, {"from": from_wallet})

    fees = exchange.fees_info
    if fee_type == "market_fee":
        exchange_fee_bal2 = fees.market_fee
    else:
        exchange_fee_bal2 = fees.opc_fee   

    fee_collector_bt_bal2 = bt.balanceOf(fee_collector)

    assert exchange_fee_bal2 == 0
    assert (fee_collector_bt_bal1 + exchange_fee_bal1) \
        == fee_collector_bt_bal2
