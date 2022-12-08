#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
import pytest


from ocean_lib.models.fixed_rate_exchange import \
    ExchangeDetails, Fees, BtNeeded, BtReceived, FixedRateExchange, OneExchange

from ocean_lib.models.test.test_factory_router import OPC_SWAP_FEE_APPROVED
from ocean_lib.ocean.util import get_address_of_type, to_wei, from_wei
from ocean_lib.web3_internal.constants import ZERO_ADDRESS


    
@pytest.mark.unit
def test_simple_with_defaults(ocean, OCEAN, DT, alice, bob):    
    # Create exchange
    (exchange, tx) = DT.create_exchange(
        price = to_wei(3),
        base_token_addr = OCEAN.address,
        tx_dict = {"from":alice}
    )

    # Alice makes 100 datatokens available on the exchange
    DT.mint(alice.address, to_wei(100), {"from": alice})
    DT.approve(exchange.address, to_wei(100), {"from": alice})

    # Bob buys 2 datatokens
    OCEAN.approve(exchange.address, exchange.BT_needed(to_wei(2)), {"from":bob})
    tx = exchange.buy_DT(to_wei(2), {"from": bob})

    # That's it! To wrap up, let's check Bob's balance
    bal = DT.balanceOf(bob.address)
    assert from_wei(bal) == 2

    # =========================================================================
    # Test details...
    
    # all exchanges for this DT
    exchanges = DT.get_exchanges()
    assert len(exchanges) == 1
    assert exchanges[0].exchange_id ==  exchange.exchange_id

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

    # Test fees
    fees = exchange.fees
    assert from_wei(fees.market_fee) == 0
    assert fees.market_fee_collector == alice.address
    assert from_wei(fees.opc_fee) == 0.001 \
        == from_wei(OPC_SWAP_FEE_APPROVED) # 0.1% *if* BT approved
    assert from_wei(fees.market_fee_available) == 0
    assert from_wei(fees.ocean_fee_available) == 2 * 3 * 0.001
    
    assert from_wei(exchange.FRE.getOPCFee(ZERO_ADDRESS)) == 0.002 # 0.2% bc BT not approved

    # Test other attributes
    assert exchange.BT_needed(to_wei(1.0)) >= to_wei(3) 
    assert exchange.BT_received(to_wei(1.0)) >= to_wei(2) 
    assert from_wei(exchange.get_rate()) == 3
    assert exchange.get_allowed_swapper() == ZERO_ADDRESS
    assert exchange.is_active()
        
    # Bob can't change market fee collector, he's not the owner
    with pytest.raises(Exception, match="not marketFeeCollector"):
        exchange.update_market_fee_collector(bob.address, {"from": bob})

    # Alice can change the market fee collector
    exchange.update_market_fee_collector(bob.address, {"from": alice})

    # Test deactivating exchange
    assert exchange.details.owner == alice.address
    assert exchange.is_active()
    
    exchange.toggle_active({"from": alice})
    assert not exchange.is_active()
    
    exchange.toggle_active({"from": alice})
    assert exchange.is_active()

    # Test setting price (rate)
    exchange.set_rate(to_wei(1.1), {"from": alice})
    assert from_wei(exchange.get_rate()) == 1.1


@pytest.mark.unit
def test_simple_with_nondefaults(ocean, OCEAN, DT, alice, bob, carlos):    
    # Create exchange, having many non-default params
    exchange, tx = DT.create_exchange(
        price = to_wei(2),
        base_token_addr = OCEAN.address,
        owner_addr = bob.address,
        market_fee_collector_addr = carlos.address,
        market_fee = to_wei(0.09),
        with_mint = True,
        allowed_swapper = bob.address,
        tx_dict = {"from":alice}
    )

    # Alice makes 100 datatokens available on the exchange
    DT.mint(alice.address, to_wei(100), {"from": alice})
    DT.approve(exchange.address, to_wei(100), {"from": alice})

    # Bob buys 2 datatokens
    OCEAN.approve(exchange.address, exchange.BT_needed(to_wei(2)), {"from":bob})
    tx = exchange.buy_DT(to_wei(2), {"from": bob})

    # ==============================================================
    # Test, focusing on difference from default

    # Test details
    details = exchange.details
    assert details.owner == bob.address
    assert details.with_mint

    # Test fees. Focus on difference from default
    fees = exchange.fees
    assert from_wei(fees.market_fee) == 0.09
    assert fees.market_fee_collector == carlos.address

    # Test allowed swapper
    assert exchange.get_allowed_swapper() == bob.address



@pytest.mark.unit
def test_buy_sell_and_claim(config, ocean, OCEAN, DT, alice, bob, carlos):    
    FRE = ocean.fixed_rate_exchange
    n_exchanges1 = FRE.getNumberOfExchanges()
    
    # Alice creates exchange. Bob's the owner, and carlos gets fees!
    price = to_wei(1)
    market_fee = to_wei(0.001)
    exchange, tx = DT.create_exchange(
        price = price,
        base_token_addr = OCEAN.address,
        tx_dict = {"from": alice},
        owner_addr = bob.address,
        market_fee_collector_addr = carlos.address,
        market_fee = market_fee,
    )

    # Test exchange count
    assert FRE.getNumberOfExchanges() == (n_exchanges1 + 1)
    assert len(FRE.getExchanges()) == (n_exchanges1 + 1)

    # Bob (the owner) makes 100K datatokens available on the exchange
    DT_amt = to_wei(100000)
    DT.mint(bob.address, DT_amt, {"from": alice})
    DT.approve(exchange.address, DT_amt, {"from": bob})

    # ==========================================================================
    # Carlos buys DT. (Carlos spends OCEAN, Bob spends DT)
    DT_buy = to_wei(11)
    OCEAN_needed = exchange.BT_needed(DT_buy)

    OCEAN.transfer(carlos.address, OCEAN_needed, {"from": bob})#give carlos OCN

    DT_bob1 = DT.balanceOf(bob.address)
    DT_carlos1 = DT.balanceOf(carlos.address)
    OCEAN_carlos1 = OCEAN.balanceOf(carlos.address)

    OCEAN.approve(exchange.address, OCEAN_needed, {"from": carlos})
    tx = exchange.buy_DT(DT_buy, {"from": carlos})

    assert DT.balanceOf(bob.address) == (DT_bob1 - DT_buy)
    assert DT.balanceOf(carlos.address) == (DT_carlos1 + DT_buy)
    assert OCEAN.balanceOf(carlos.address) >= (OCEAN_carlos1-OCEAN_needed)

    # Check logs outputs. Price = Rate = 1
    event_log = tx.events["Swapped"]
    assert (
        event_log["baseTokenSwappedAmount"]
        - event_log["marketFeeAmount"]
        - event_log["oceanFeeAmount"]
        - event_log["consumeMarketFeeAmount"]
        == event_log["datatokenSwappedAmount"]
    )

    # ==========================================================================
    # Bob sells DT to the exchange
    DT_sell = to_wei(10)
    
    DT_bob1 = DT.balanceOf(bob.address)
    OCEAN_bob1 = OCEAN.balanceOf(bob.address)
    
    DT.approve(exchange.address, DT_sell, {"from": bob})
    exchange.sell_DT(DT_sell, {"from": bob})
    
    # Bob should now have more OCEAN, and fewer DT
    OCEAN_received = exchange.BT_received(DT_sell)
    OCEAN_bob2 = OCEAN.balanceOf(bob.address)
    DT_bob2 = DT.balanceOf(bob.address)
    assert pytest.approx(from_wei(OCEAN_bob2), 0.01) \
        == (from_wei(OCEAN_bob1) + from_wei(OCEAN_received))
    assert from_wei(DT_bob2) == (from_wei(DT_bob1) - from_wei(DT_sell))

    # Test exchange's DT & OCEAN supply
    OCEAN_for_exchange = OCEAN.allowance(bob.address, exchange.address)
    details = exchange.details
    assert details.dt_supply == DT_sell
    assert OCEAN_bob2 > OCEAN_for_exchange
    assert details.bt_supply == OCEAN_for_exchange + details.bt_balance

    # ==========================================================================
    # As payment collector, Alice collects DT payments & BT (OCEAN) payments
    assert DT.getPaymentCollector() == alice.address

    DT_alice1 = DT.balanceOf(alice.address)
    receipt = exchange.collect_DT(details.dt_balance, {"from": alice})
    DT_received = receipt.events["TokenCollected"]["amount"]
    assert receipt.events["TokenCollected"]["to"] == alice.address
    DT_expected = DT_alice1 + DT_received

    OCEAN_alice1 = OCEAN.balanceOf(alice.address)
    receipt = exchange.collect_BT(details.bt_balance, {"from": alice})
    OCEAN_received = receipt.events["TokenCollected"]["amount"]
    assert receipt.events["TokenCollected"]["to"] == alice.address
    OCEAN_expected = OCEAN_alice1 + OCEAN_received

    st_time = time.time() # loop to avoid failure if chain didn't update yet
    while (time.time() - st_time) < 5:
        if DT.balanceOf(alice.address) == DT_expected \
           and OCEAN.balanceOf(alice.address) == OCEAN_expected:
            break
        time.sleep(0.2)
    assert from_wei(DT.balanceOf(alice.address)) == from_wei(DT_expected)
    assert from_wei(OCEAN.balanceOf(alice.address)) == from_wei(OCEAN_expected)

    # ==========================================================================
    # As market fee collector, Carlos collects fees
    fees = exchange.fees
    assert fees.market_fee_collector == carlos.address
    assert fees.market_fee > 0
    assert fees.market_fee_available > 0

    OCEAN_carlos1 = OCEAN.balanceOf(carlos.address)
    exchange.collect_market_fee({"from": carlos})
    OCEAN_expected = OCEAN_carlos1 + fees.market_fee_available

    st_time = time.time() # loop to avoid failure if chain didn't update yet
    while (time.time() - st_time) < 5:
        if OCEAN.balanceOf(carlos.address) == OCEAN_expected:
            break
        time.sleep(0.2)
    assert from_wei(OCEAN.balanceOf(carlos.address)) == from_wei(OCEAN_expected)
    




@pytest.mark.unit
def test_ExchangeDetails(alice):
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
    assert f"price " in s


@pytest.mark.unit
def test_Fees():
    mkt_fee = to_wei(0.03)
    mkt_fee_coll = "0xabc"
    opc_fee = to_wei(0.04)
    mkt_avail = to_wei(0.5)
    opc_avail = to_wei(0.6)

    tup = [mkt_fee, mkt_fee_coll, opc_fee, mkt_avail, opc_avail]
    fees = Fees(tup)

    assert fees.market_fee == mkt_fee
    assert fees.market_fee_collector == mkt_fee_coll
    assert fees.opc_fee == opc_fee
    assert fees.market_fee_available == mkt_avail
    assert fees.ocean_fee_available == opc_avail

    # Test str. Don't need to be thorough
    s = str(fees)
    assert "Fees" in s
    assert f"market_fee_collector = {mkt_fee_coll}" in s


@pytest.mark.unit
def test_BtNeeded():
    a, b, c, d = 1, 2, 3, 4 #not realistic values, fyi
    bt_needed = BtNeeded([a, b, c, d])
    assert bt_needed.base_token_amount == a
    assert bt_needed.ocean_fee_amount == b
    assert bt_needed.publish_market_fee_amount == c
    assert bt_needed.consume_market_fee_amount == d


@pytest.mark.unit
def test_BtReceived():
    a, b, c, d = 1, 2, 3, 4 #not realistic values, fyi
    bt_recd = BtReceived([a, b, c, d])
    assert bt_recd.base_token_amount == a
    assert bt_recd.ocean_fee_amount == b
    assert bt_recd.publish_market_fee_amount == c
    assert bt_recd.consume_market_fee_amount == d
    
