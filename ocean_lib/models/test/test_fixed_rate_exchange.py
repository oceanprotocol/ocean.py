#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest


from ocean_lib.models.fixed_rate_exchange import \
    ExchangeDetails, Fees, BtNeeded, BtReceived, FixedRateExchange, OneExchange

from ocean_lib.models.test.test_factory_router import OPC_SWAP_FEE_APPROVED
from ocean_lib.ocean.util import get_address_of_type, to_wei, from_wei
from ocean_lib.web3_internal.constants import ZERO_ADDRESS



@pytest.mark.unit
def test_ExchangeDetails(alice):
    exchange_owner = "0xabc"
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
        exchange_owner,
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
    
    assert details.exchange_owner == exchange_owner
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
    
    
@pytest.mark.unit
def test_simple_with_defaults(ocean, OCEAN, alice, bob, datatoken):
    # =========================================================================
    # Simple flow
    
    # Mint datatokens; create exchange
    DT = datatoken
    DT.mint(alice.address, "100 ether", {"from": alice})
    (exchange, tx) = DT.create_fixed_rate(
        price = "3 ether",
        base_token_addr = OCEAN.address, 
        amount = "100 ether",
        tx_dict = {"from":alice}
    )

    # Bob buys 2 datatokens
    tx = exchange.buy_DT("2 ether", {"from": bob})

    # That's it! To wrap up, let's check Bob's balance
    bal = DT.balanceOf(bob.address)
    assert from_wei(bal) == 2

    # =========================================================================
    # Test details...
    
    # all exchanges for this DT
    exchanges = DT.get_fixed_rate_exchanges()
    assert [e.exchange_id for e in exchanges] == [exchange.exchange_id]

    # Test details
    details = exchange.details(exchange_id)
    assert details.exchange_owner == alice.address
    assert details.datatoken == DT.address
    assert details.dt_decimals == DT.decimals()
    assert from_wei(details.fixed_fate) == 3
    assert details.active == True
    assert from_wei(details.dt_supply) == (100 - 2)
    assert from_wei(details.bt_supply) == 2 * 3
    assert from_wei(details.dt_balance) == 0
    assert from_wei(details.bt_balance) == 2 * 3
    assert details.with_mint == False

    # Test fees
    fees = exchange.fees()
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
    assert from_wei(exchange.getRate()) == 3
    assert exchange.getAllowedSwapper() == ZERO_ADDRESS
    assert exchange.isActive()


@pytest.mark.unit
def test_simple_with_nondefaults(ocean, OCEAN, alice, bob, carlos, datatoken):
    # =========================================================================
    # Simple flow
    
    # Mint datatokens; create exchange
    DT = datatoken
    DT.mint(alice.address, "100 ether", {"from": alice})
    exchange, tx = DT.create_fixed_rate(
        price = "2 ether",
        base_token_addr = OCEAN.address,
        amount = "100 ether",
        owner_addr = bob.address,
        market_fee_collector_addr = carlos.address,
        market_fee = to_wei(0.09),
        with_mint = True,
        allowed_swapper = bob.address,
        tx_dict = {"from":alice}
    )

    # ==============================================================
    # Test details. Focus on difference from default

    # Test details
    details = exchange.details()
    assert details.exchange_owner == bob.address
    assert details.with_mint == True

    # Test fees. Focus on difference from default
    fees = exchange.fees()
    assert from_wei(fees.market_fee) == 0.09
    assert fees.market_fee_collector == carlos.address

    # Test allowedSwapper
    assert exchange.getAllowedSwapper() == bob.address
    
    # ==========================================================================
    # Change market fee collector from Carlos -> Bob
    
    # Only the current collector (Carlos) can update
    with pytest.raises(Exception, match="not marketFeeCollector"):
        exchange.updateMarketFeeCollector(bob.address, {"from": bob})

    exchange.updateMarketFeeCollector(bob.address, {"from": carlos})

    # ==========================================================================
    # Test deactivating exchange
    assert exchange.isActive()
    exchange.toggleExchangeState({"from": alice})
    assert not exchange.isActive()
    exchange.toggleExchangeState({"from": alice})
    assert exchange.isActive()

    # ==========================================================================
    # Test setting price (rate)
    exchange.setRate(to_wei(1.1), {"from": alice})
    assert from_wei(exchange.getRate()) == 1.1

    


@pytest.mark.unit
def test_thorough(config, ocean, OCEAN, alice, bob, carlos, datatoken):
    # ==========================================================================
    # Create exchange
    
    # base data
    DT, FRE = datatoken, ocean.fixed_rate_exchange
    
    # Set exchange params
    DT_amt = to_wei(100000)
    huge_num_DT = to_wei(1e20)
    price = to_wei(1)
    market_fee = to_wei(0.001)

    # Bob mints DT
    DT.mint(bob.address, DT_amt, {"from": alice})
    assert DT.balanceOf(bob.address) == DT_amt

    # Alice creates exchange. Bob's the owner, and carlos gets fees!
    num_exchanges_before = FRE.getNumberOfExchanges()
    exchange_id, tx_receipts = DT.create_fixed_rate(
        price = price,
        base_token_addr = OCEAN.address,
        amount = DT_amt,
        tx_dict = {"from": alice},
        owner_addr = bob.address,
        market_fee_collector_addr = carlos.address,
        market_fee = market_fee,
    )
    assert len(tx_receipts) != 2, "shouldn't have done optional approve()"
    DT.approve(FRE.address, DT_amt, {"from": bob})

    # Test exchange count
    assert FRE.getNumberOfExchanges() == (num_exchanges_before + 1)
    assert len(FRE.getExchanges()) == (num_exchanges_before + 1)

    # Test generateExchangeId
    assert FRE.generateExchangeId(OCEAN.address, DT.address) == exchange_id
    
    # Test exchange supply
    details = FRE.details(exchange_id)
    OCEAN_allowance = OCEAN.allowance(bob.address, FRE.address)
    assert from_wei(details.dt_supply) == from_wei(DT_amt)
    assert from_wei(details.bt_supply) == from_wei(OCEAN_allowance)

    # ==========================================================================
    # Carlos buys DT. (Carlos spends OCEAN, Bob spends DT)
    DT_buy = to_wei(11)

    OCEAN_needed = FRE.BT_needed(exchange_id, DT_buy).val
    OCEAN.transfer(carlos.address, OCEAN_needed, {"from": bob})

    DT_bob_before = DT.balanceOf(bob.address)
    DT_carlos_before = DT.balanceOf(carlos.address)
    OCEAN_carlos_before = OCEAN.balanceOf(carlos.address)

    tx = exchange.buy_DT(DT_buy, exchange_id, {"from": carlos})

    assert DT.balanceOf(bob.address) == (DT_bob_before - DT_buy)
    assert DT.balanceOf(carlos.address) == (DT_carlos_before + DT_buy)
    assert OCEAN.balanceOf(carlos.address) >= (OCEAN_carlos_before-OCEAN_needed)

    # Check fixed rate exchange outputs. Price = Rate = 1
    event_log = tx_receipts[-1].events["Swapped"]
    assert (
        event_log["baseTokenSwappedAmount"]
        - event_log["marketFeeAmount"]
        - event_log["oceanFeeAmount"]
        - event_log["consumeMarketFeeAmount"]
        == event_log["datatokenSwappedAmount"]
    )

    # ==========================================================================
    # Bob sells DT to the exchange, getting OCEAN from exchange's reserve
    DT_sell = to_wei(10)
    
    DT_bob1 = DT.balanceOf(bob.address)
    OCEAN_bob1 = OCEAN.balanceOf(bob.address)
    
    exchange.sell_DT(DT_sell, exchange_id, {"from": bob})
    
    # Bob should now have more OCEAN, and fewer DT
    OCEAN_received = FRE.BT_received(exchange_id, DT_sell).val
    OCEAN_bob2 = OCEAN.balanceOf(bob.address)
    DT_bob2 = DT.balanceOf(bob.address)
    assert pytest.approx(OCEAN_bob2, to_wei(0.01)) \
        == (OCEAN_bob1 + OCEAN_received)
    assert DT_bob2 == (DT_bob1 - DT_sell)

    # Test exchange's DT & OCEAN supply
    details = FRE.details(exchange_id)
    assert details.dt_supply == DT_sell
    
    OCEAN_for_FRE = OCEAN.allowance(bob.address, FRE.address)
    assert OCEAN_bob2 > OCEAN_for_FRE
    assert details.bt_supply == OCEAN_for_FRE + details.bt_balance

    # ==========================================================================
    # As payment collector, Alice collects DT payments & BT (OCEAN) payments
    assert DT.getPaymentCollector() == alice.address

    DT_alice_before = DT.balanceOf(alice.address)
    receipt = FRE.collectDT(exchange_id, details.dt_balance, {"from": alice})
    DT_received = receipt.events["TokenCollected"]["amount"]
    assert receipt.events["TokenCollected"]["to"] == alice.address
    DT_expected = DT_alice_before + DT_received

    OCEAN_alice_before = OCEAN.balanceOf(alice.address)
    receipt = FRE.collectBT(exchange_id, details.bt_balance, {"from": alice})
    OCEAN_received = receipt.events["TokenCollected"]["amount"]
    assert receipt.events["TokenCollected"]["to"] == alice.address
    OCEAN_expected = OCEAN_alice_before + OCEAN_received

    st_time = time.time() # loop to avoid failure if chain didn't update yet
    while (time.time() - st_time) < 5:
        if DT.balanceOf(alice.address) == DT_expected \
           and OCEAN.balanceOf(alice.address) == OCEAN_expected:
            break
        time.sleep(0.2)
    assert DT.balanceOf(alice.address) == DT_expected
    assert OCEAN.balanceOf(alice.address) == OCEAN_expected

    # ==========================================================================
    # As market fee collector, Carlos collects fees
    fees = FRE.fees(exchange_id)
    assert fees.market_fee_collector == carlos.address
    assert fees.market_fee > 0
    assert fees.market_Fee_available > 0

    OCEAN_carlos_before = OCEAN.balanceOf(carlos.address)
    FRE.collectMarketFee(exchange_id, {"from": carlos})
    OCEAN_expected = OCEAN_carlos_before + fees.market_fee_available

    st_time = time.time() # loop to avoid failure if chain didn't update yet
    while (time.time() - st_time) < 5:
        if OCEAN.balanceOf(carlos.address) == OCEAN_expected:
            break
        time.sleep(0.2)
    assert OCEAN.balanceOf(carlos.address) == OCEAN_expected

