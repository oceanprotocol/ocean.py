#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
import pytest


from ocean_lib.models.fixed_rate_exchange import (
    ExchangeDetails,
    FeesInfo,
    BtNeeded,
    BtReceived,
    FixedRateExchange,
    OneExchange,
)
from ocean_lib.models.test.test_factory_router import OPC_SWAP_FEE_APPROVED
from ocean_lib.ocean.util import to_wei, from_wei
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS

from tests.resources.helper_functions import get_wallet


@pytest.mark.unit
def test_with_defaults(OCEAN, DT, alice, bob):

    # =========================================================================
    # Create exchange
    exchange = DT.create_exchange(
        rate=to_wei(3), base_token_addr=OCEAN.address, tx_dict={"from": alice}
    )

    # Alice makes 100 datatokens available on the exchange
    DT.mint(alice.address, to_wei(100), {"from": alice})
    DT.approve(exchange.address, to_wei(100), {"from": alice})

    # Bob lets exchange pull the OCEAN needed
    consume_market_fee = 0
    OCEAN.approve(exchange.address, MAX_UINT256, {"from": bob})

    # Bob buys 2 datatokens
    DT_bob1 = DT.balanceOf(bob)
    tx = exchange.buy_DT(datatoken_amt=to_wei(2), tx_dict={"from": bob})
    assert from_wei(DT.balanceOf(bob)) == from_wei(DT_bob1) + 2

    # all exchanges for this DT
    exchanges = DT.get_exchanges()
    assert len(exchanges) == 1
    assert exchanges[0].exchange_id == exchange.exchange_id

    # Test details
    details = exchange.details
    assert details.owner == alice.address
    assert details.datatoken == DT.address
    assert details.dt_decimals == DT.decimals()
    assert from_wei(details.fixed_rate) == 3
    assert details.active
    assert from_wei(details.dt_supply) == (100 - 2)
    assert from_wei(details.bt_supply) == 2 * 3
    assert from_wei(details.dt_balance) == 0
    assert from_wei(details.bt_balance) == 2 * 3
    assert not details.with_mint

    # Fees tests
    fees = exchange.fees_info
    assert from_wei(fees.publish_market_fee) == 0  # publish mkt swap fee
    assert fees.publish_market_fee_collector == alice.address  # for publish mkt swaps
    assert (
        from_wei(fees.opc_fee) == 0.001 == from_wei(OPC_SWAP_FEE_APPROVED)
    )  # 0.1% *if* BT approved
    assert from_wei(fees.publish_market_fee_available) == 0  # for publish mkt swaps
    assert from_wei(fees.ocean_fee_available) == 2 * 3 * 0.001

    FRE = exchange.FRE
    assert FRE.get_opc_collector()[:2] == "0x", FRE.get_opc_collector()
    assert from_wei(FRE.getOPCFee(ZERO_ADDRESS)) == 0.002  # 0.2% bc BT not approved

    # Test other attributes
    assert exchange.BT_needed(to_wei(1.0), 0) >= to_wei(3)
    assert exchange.BT_received(to_wei(1.0), 0) >= to_wei(2)
    assert from_wei(exchange.get_rate()) == 3
    assert exchange.get_allowed_swapper() == ZERO_ADDRESS
    assert exchange.is_active()

    # ==========================================================================
    # Bob sells DT to the exchange
    DT_sell = to_wei(1.5)

    DT_bob1 = DT.balanceOf(bob)
    OCEAN_bob1 = OCEAN.balanceOf(bob)

    DT.approve(exchange.address, DT_sell, {"from": bob})
    exchange.sell_DT(DT_sell, tx_dict={"from": bob})

    assert DT.balanceOf(bob) < DT_bob1
    assert OCEAN.balanceOf(bob) > OCEAN_bob1

    # ==========================================================================
    # Change other stuff

    # Alice changes market fee collector
    exchange.update_publish_market_fee_collector(bob.address, {"from": alice})

    # Test deactivating exchange
    assert exchange.details.owner == alice.address
    assert exchange.is_active()

    exchange.toggle_active({"from": alice})
    assert not exchange.is_active()

    exchange.toggle_active({"from": alice})
    assert exchange.is_active()

    # Test setting rate
    exchange.set_rate(to_wei(1.1), {"from": alice})
    assert from_wei(exchange.get_rate()) == 1.1


@pytest.mark.unit
def test_with_nondefaults(OCEAN, DT, alice, bob, carlos, dan, FRE):
    # =================================================================
    # Alice creates exchange. Bob's the owner, and carlos gets fees!
    rate = to_wei(1)
    publish_market_fee = to_wei(0.09)
    publish_market_fee_collector = alice.address
    consume_market_fee = to_wei(0.02)
    consume_market_fee_addr = dan.address

    n_exchanges1 = FRE.getNumberOfExchanges()
    exchange, tx = DT.create_exchange(
        rate=rate,
        base_token_addr=OCEAN.address,
        owner_addr=bob.address,
        publish_market_fee_collector=publish_market_fee_collector,
        publish_market_fee=publish_market_fee,
        with_mint=True,
        allowed_swapper=carlos.address,
        full_info=True,
        tx_dict={"from": alice},
    )
    assert tx is not None
    assert FRE.getNumberOfExchanges() == (n_exchanges1 + 1)
    assert len(FRE.getExchanges()) == (n_exchanges1 + 1)

    # Test, focusing on difference from default
    assert exchange.details.owner == bob.address
    assert exchange.details.with_mint

    assert exchange.fees_info.publish_market_fee == publish_market_fee
    assert exchange.fees_info.publish_market_fee_collector == alice.address

    assert exchange.get_allowed_swapper() == carlos.address

    # =================================================================
    # Alice makes 100 datatokens available on the exchange
    DT.mint(alice.address, to_wei(100), {"from": alice})
    DT.approve(exchange.address, to_wei(100), {"from": alice})

    # ==================================================================
    # Carlos buys DT. (Carlos spends OCEAN, Bob spends DT)
    DT_buy = to_wei(11)
    OCEAN_needed = exchange.BT_needed(DT_buy, consume_market_fee)
    OCEAN.transfer(carlos.address, OCEAN_needed, {"from": bob})  # give carlos OCN

    DT_carlos1 = DT.balanceOf(carlos)
    OCEAN_carlos1 = OCEAN.balanceOf(carlos)

    OCEAN.approve(exchange.address, OCEAN_needed, {"from": carlos})
    tx = exchange.buy_DT(
        datatoken_amt=DT_buy,
        max_basetoken_amt=MAX_UINT256,
        consume_market_fee_addr=consume_market_fee_addr,
        consume_market_fee=consume_market_fee,
        tx_dict={"from": carlos},
    )

    assert DT.balanceOf(carlos) == (DT_carlos1 + DT_buy)
    assert OCEAN.balanceOf(carlos) == (OCEAN_carlos1 - OCEAN_needed)

    # ==========================================================================
    # Carlos sells DT to the exchange
    DT_sell = to_wei(10)

    DT_exchange1 = exchange.details.dt_supply
    OCEAN_exchange1 = exchange.details.bt_supply

    DT_carlos1 = DT.balanceOf(carlos)
    OCEAN_carlos1 = OCEAN.balanceOf(carlos)

    DT.approve(exchange.address, DT_sell, {"from": carlos})
    exchange.sell_DT(
        DT_sell,
        min_basetoken_amt=0,
        consume_market_fee_addr=consume_market_fee_addr,
        consume_market_fee=consume_market_fee,
        tx_dict={"from": carlos},
    )

    # Carlos should now have more OCEAN, and fewer DT
    OCEAN_received = exchange.BT_received(DT_sell, consume_market_fee)
    OCEAN_carlos2 = OCEAN.balanceOf(carlos)
    DT_carlos2 = DT.balanceOf(carlos)
    assert pytest.approx(from_wei(OCEAN_carlos2), 0.01) == (
        from_wei(OCEAN_carlos1) + from_wei(OCEAN_received)
    )
    assert from_wei(DT_carlos2) == (from_wei(DT_carlos1) - from_wei(DT_sell))

    # Test exchange's DT & OCEAN supply
    details = exchange.details
    OCEAN_to_exchange = to_wei(from_wei(details.fixed_rate) * from_wei(DT_sell))
    assert from_wei(details.dt_supply) == from_wei(DT_exchange1) - from_wei(DT_sell)
    assert from_wei(details.bt_supply) == from_wei(OCEAN_exchange1) - from_wei(
        OCEAN_to_exchange
    )

    # ==========================================================================
    # As payment collector, Alice collects DT payments & BT (OCEAN) payments
    assert DT.getPaymentCollector() == alice.address

    DT_alice1 = DT.balanceOf(alice)
    receipt = exchange.collect_DT(details.dt_balance, {"from": alice})
    DT_received = receipt.events["TokenCollected"]["amount"]
    assert receipt.events["TokenCollected"]["to"] == alice.address
    DT_expected = DT_alice1 + DT_received

    OCEAN_alice1 = OCEAN.balanceOf(alice)
    receipt = exchange.collect_BT(details.bt_balance, {"from": alice})
    OCEAN_received = receipt.events["TokenCollected"]["amount"]
    assert receipt.events["TokenCollected"]["to"] == alice.address
    OCEAN_expected = OCEAN_alice1 + OCEAN_received

    st_time = time.time()  # loop to ensure chain's updated (shouldn't need!!)
    while (time.time() - st_time) < 5 and DT.balanceOf(alice) == DT_alice1:
        time.sleep(0.2)
    assert from_wei(DT.balanceOf(alice.address)) == from_wei(DT_expected)
    assert from_wei(OCEAN.balanceOf(alice.address)) == from_wei(OCEAN_expected)

    # ==========================================================================
    # As publish market fee collector, Alice collects fees
    fees = exchange.fees_info
    assert fees.publish_market_fee > 0
    assert fees.publish_market_fee_available > 0

    OCEAN_alice1 = OCEAN.balanceOf(alice.address)
    exchange.collect_publish_market_fee({"from": alice})
    OCEAN_expected = OCEAN_alice1 + fees.publish_market_fee_available

    st_time = time.time()  # loop to ensure chain's updated (shouldn't need!!)
    while (time.time() - st_time) < 5 and OCEAN.balanceOf(alice) == OCEAN_alice1:
        time.sleep(0.2)

    assert from_wei(OCEAN.balanceOf(alice)) == from_wei(OCEAN_expected)


@pytest.mark.unit
def test_ExchangeDetails():
    owner = "0xabc"
    datatoken = "0xdef"
    dt_decimals = 18
    base_token = "0x123"
    bt_decimals = 10
    fixed_rate = to_wei(0.01)
    active = False
    dt_supply = to_wei(100)
    bt_supply = to_wei(101)
    dt_balance = to_wei(10)
    bt_balance = to_wei(11)
    with_mint = True

    tup = [
        owner,
        datatoken,
        dt_decimals,
        base_token,
        bt_decimals,
        fixed_rate,
        active,
        dt_supply,
        bt_supply,
        dt_balance,
        bt_balance,
        with_mint,
    ]

    details = ExchangeDetails(tup)

    assert details.owner == owner
    assert details.datatoken == datatoken
    assert details.dt_decimals == dt_decimals
    assert details.base_token == base_token
    assert details.bt_decimals == bt_decimals
    assert details.fixed_rate == fixed_rate
    assert details.active == active
    assert details.dt_supply == dt_supply
    assert details.bt_supply == bt_supply
    assert details.dt_balance == dt_balance
    assert details.bt_balance == bt_balance
    assert details.with_mint == with_mint

    # Test str. Don't need to be thorough
    s = str(details)
    assert "ExchangeDetails" in s
    assert f"datatoken = {datatoken}" in s
    assert f"rate " in s


@pytest.mark.unit
def test_FeesInfo():
    mkt_fee = to_wei(0.03)
    mkt_fee_coll = "0xabc"
    opc_fee = to_wei(0.04)
    mkt_avail = to_wei(0.5)
    opc_avail = to_wei(0.6)

    tup = [mkt_fee, mkt_fee_coll, opc_fee, mkt_avail, opc_avail]
    fees = FeesInfo(tup)

    assert fees.publish_market_fee == mkt_fee
    assert fees.publish_market_fee_collector == mkt_fee_coll
    assert fees.opc_fee == opc_fee
    assert fees.publish_market_fee_available == mkt_avail
    assert fees.ocean_fee_available == opc_avail

    # Test str. Don't need to be thorough
    s = str(fees)
    assert "FeesInfo" in s
    assert f"publish_market_fee_collector = {mkt_fee_coll}" in s


@pytest.mark.unit
def test_BtNeeded():
    a, b, c, d = 1, 2, 3, 4  # not realistic values, fyi
    bt_needed = BtNeeded([a, b, c, d])
    assert bt_needed.base_token_amount == a
    assert bt_needed.ocean_fee_amount == b
    assert bt_needed.publish_market_fee_amount == c
    assert bt_needed.consume_market_fee_amount == d


@pytest.mark.unit
def test_BtReceived():
    a, b, c, d = 1, 2, 3, 4  # not realistic values, fyi
    bt_recd = BtReceived([a, b, c, d])
    assert bt_recd.base_token_amount == a
    assert bt_recd.ocean_fee_amount == b
    assert bt_recd.publish_market_fee_amount == c
    assert bt_recd.consume_market_fee_amount == d
