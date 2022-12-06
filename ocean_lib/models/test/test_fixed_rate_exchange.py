#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.models.fixed_rate_exchange import \
    FreStatus, FreFees, BtNeeded, BtReceived, FixedRateExchange
from ocean_lib.models.test.test_factory_router import OPC_SWAP_FEE_APPROVED
from ocean_lib.ocean.util import get_address_of_type, to_wei, from_wei
from ocean_lib.web3_internal.constants import ZERO_ADDRESS


@pytest.mark.unit
def test_FreStatus(alice):
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
    
    status = FreStatus(tup)
    
    assert status.exchangeOwner == exchange_owner
    assert status.datatoken == datatoken
    assert status.dtDecimals == dt_decimals
    assert status.baseToken == base_token
    assert status.btDecimals == bt_decimals
    assert status.fixedRate == fixed_rate
    assert status.active == active
    assert status.dtSupply == dt_supply
    assert status.btSupply == bt_supply
    assert status.dtBalance == dt_balance
    assert status.btBalance == bt_balance
    assert status.withMint == with_mint

    # Test str. Don't need to be thorough
    s = str(status)
    assert "FreStatus" in s
    assert f"datatoken = {datatoken}" in s
    assert f"price in baseToken" in s


@pytest.mark.unit
def test_FreFees():
    mkt_fee = to_wei(0.03)
    mkt_fee_coll = "0xabc"
    opc_fee = to_wei(0.04)
    mkt_avail = to_wei(0.5)
    opc_avail = to_wei(0.6)

    tup = [mkt_fee, mkt_fee_coll, opc_fee, mkt_avail, opc_avail]
    fees = FreFees(tup)

    assert fees.marketFee == mkt_fee
    assert fees.marketFeeCollector == mkt_fee_coll
    assert fees.opcFee == opc_fee
    assert fees.marketFeeAvailable == mkt_avail
    assert fees.oceanFeeAvailable == opc_avail

    # Test str. Don't need to be thorough
    s = str(fees)
    assert "FreFees" in s
    assert f"marketFeeCollector = {mkt_fee_coll}" in s


@pytest.mark.unit
def test_BtNeeded():
    a, b, c, d = 1, 2, 3, 4 #not realistic values, fyi
    bt_needed = BtNeeded(a, b, c, d)
    assert bt_needed.val == a
    assert bt_needed.oceanFeeAmount == b
    assert bt_needed.publishMarketFeeAmount == c
    assert bt_needed.consumeMarketFeeAmount == d


@pytest.mark.unit
def test_BtReceived():
    a, b, c, d = 1, 2, 3, 4 #not realistic values, fyi
    bt_recd = BtReceived(a, b, c, d)
    assert bt_recd.val == a
    assert bt_recd.oceanFeeAmount == b
    assert bt_recd.publishMarketFeeAmount == c
    assert bt_recd.consumeMarketFeeAmount == d
    
    
@pytest.mark.unit
def test_simple_with_defaults(ocean, OCEAN, alice, bob, datatoken):
    # =========================================================================
    # Simple flow
    
    # Mint datatokens; create exchange
    DT = datatoken
    DT.mint(alice.address, "100 ether", {"from": alice})
    exchange_id, _ = DT.create_fixed_rate(
        price = "3 ether",
        base_token_addr = OCEAN.address, 
        amount = "100 ether",
        tx_dict = {"from":alice}
    )

    # Bob buys 2 datatokens
    DT.buy("2 ether", exchange_id, {"from": bob})

    # That's it! To wrap up, let's check Bob's balance
    bal = DT.balanceOf(bob.address)
    assert from_wei(bal) == 2

    # =========================================================================
    # Test details...
    
    # all exchanges for this DT
    exchange_ids = DT.get_fixed_rate_exchanges()
    assert exchange_ids == [exchange_id]

    # Test status
    FRE = ocean.fixed_rate_exchange
    status = FRE.status(exchange_id)
    assert status.exchangeOwner == alice.address
    assert status.datatoken == DT.address
    assert status.dtDecimals == DT.decimals()
    assert from_wei(status.fixedRate) == 3
    assert status.active == True
    assert from_wei(status.dtSupply) == (100 - 2)
    assert from_wei(status.btSupply) == 2 * 3
    assert from_wei(status.dtBalance) == 0
    assert from_wei(status.btBalance) == 2 * 3
    assert status.withMint == False

    # Test fees
    fees = FRE.fees(exchange_id)
    assert from_wei(fees.marketFee) == 0
    assert fees.marketFeeCollector == alice.address
    assert from_wei(fees.opcFee) == 0.001 \
        == from_wei(OPC_SWAP_FEE_APPROVED) # 0.1% *if* BT approved
    assert from_wei(fees.marketFeeAvailable) == 0
    assert from_wei(fees.oceanFeeAvailable) == 2 * 3 * 0.001
    
    assert from_wei(FRE.getOPCFee(ZERO_ADDRESS)) == 0.002 # 0.2% bc BT not approved

    # Test other attributes
    assert FRE.BT_needed(exchange_id, to_wei(1.0)).val >= to_wei(3) 
    assert FRE.BT_received(exchange_id, to_wei(1.0)).val >= to_wei(2) 
    assert from_wei(FRE.getRate(exchange_id)) == 3
    assert FRE.getAllowedSwapper(exchange_id) == ZERO_ADDRESS
    assert FRE.isActive(exchange_id)


@pytest.mark.unit
def test_simple_with_nondefaults(ocean, OCEAN, alice, bob, carlos, datatoken):
    # =========================================================================
    # Simple flow
    
    # Mint datatokens; create exchange
    DT = datatoken
    DT.mint(alice.address, "100 ether", {"from": alice})
    exchange_id, _ = DT.create_fixed_rate(
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

    # Test status
    FRE = ocean.fixed_rate_exchange
    status = FRE.status(exchange_id)
    assert status.exchangeOwner == bob.address
    assert status.withMint == True

    # Test fees. Focus on difference from default
    fees = FRE.fees(exchange_id)
    assert from_wei(fees.marketFee) == 0.09
    assert fees.marketFeeCollector == carlos.address

    # Test allowedSwapper
    assert FRE.getAllowedSwapper(exchange_id) == bob.address
    

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
    exchange_id, _ = DT.create_fixed_rate(
        price = price,
        base_token_addr = OCEAN.address,
        amount = DT_amt,
        tx_dict = {"from": alice},
        owner_addr = bob.address,
        market_fee_collector_addr = carlos.address,
        market_fee = market_fee,
    )
    DT.approve(FRE.address, DT_amt, {"from": bob})

    # Test exchange count
    assert FRE.getNumberOfExchanges() == (num_exchanges_before + 1)
    assert len(FRE.getExchanges()) == (num_exchanges_before + 1)

    # Test generateExchangeId
    assert FRE.generateExchangeId(OCEAN.address, DT.address) == exchange_id
    
    # Test exchange supply. It shouldn't have supply yet
    status = FRE.status(exchange_id)
    OCEAN_allowance = OCEAN.allowance(bob.address, FRE.address)
    assert status.dtSupply == 0
    assert status.btSupply == OCEAN_allowance

    # ==========================================================================
    # Carlos buys DT. (Carlos spends OCEAN, Bob spends DT)
    DT_buy = to_wei(11)

    DT_carlos_before = DT.balanceOf(carlos.address)
    DT_bob_before = DT.balanceOf(bob.address)
    OCEAN_bob_before = OCEAN.balanceOf(bob.address)

    # Q: OCEAN.approve() by Carlos? A: It happens inside DT.buy()
    # Q: DT.approve() by Bob? A: He already approved, just after create..()
    tx_receipt = DT.buy(DT_buy, exchange_id, {"from": carlos})
    
    assert DT.balanceOf(carlos.address) == (DT_carlos_before + DT_buy)
    assert OCEAN.balanceOf(bob.address) > OCEAN_bob_before

    # Check fixed rate exchange outputs. Price = Rate = 1
    event_log = tx_receipt.events["Swapped"]
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
    
    DT_bob_before = DT.balanceOf(bob.address)
    OCEAN_bob_before = OCEAN.balanceOf(bob.address)
    
    # Q: DT.approve() by Bob? A: It happens inside DT.sell()
    DT.sell(DT_sell, exchange_id, {"from": bob})
    
    # Bob should now have more OCEAN, and fewer DT
    OCEAN_received, _, _, _ = \
        FRE.calcBaseOutGivenInDT(exchange_id, DT_sell, 0)
    assert OCEAN.balanceOf(bob.address) == (OCEAN_bob_before + OCEAN_received)
    assert DT.balanceOf(bob.address) == (DT_bob_before - DT_sell)

    # Test exchange's DT & OCEAN supply
    status = FRE.status(exchange_id)
    assert status.dtSupply == DT_sell
    assert status.btSupply == OCEAN.allowance(status.exchangeOwner, FRE.address)

    # ==========================================================================
    # Bob's the payment collector. He collects his all DT payments
    assert DT.getPaymentCollector() == bob.address
    DT_bob_before = DT.balanceOf(bob.address)

    receipt = FRE.collectDT(exchange_id, status.dtBalance, {"from": bob})
    DT_received = receipt.events["TokenCollected"]["amount"]
    
    assert DT.balanceOf(bob.address) == (DT_bob_before + DT_received)

    # ==========================================================================
    # Bob withdraws his OCEAN balance. He needs to buy bc he sold all DT, and BT balance will be 0
    DT.approve(FRE.address, to_wei(10), {"from": bob})

    # Carlos buys DT
    FRE.buyDT(
        exchange_id,
        to_wei(10),
        huge_num_DT,
        bob.address,
        to_wei("0.1"),
        {"from": carlos}, # Q: was this supposed to be Bob??
    )
    assert DT.balanceOf(carlos.address) == DT_sell + to_wei(10)
    BT_before = OCEAN.balanceOf(bob.address)

    receipt = FRE.collectBT(exchange_id, FRE.status(exchange_id).btBalance, {"from": bob})

    logs = receipt.events["TokenCollected"]
    assert OCEAN.balanceOf(bob.address) == BT_before + logs["amount"]

    # Exchange should have fees available and claimable
    # Market fee collector bt balance
    BT_before = OCEAN.balanceOf(carlos.address)

    fees = FRE.fees(exchange_id)
    assert fees.marketFee == market_fee
    assert fees.marketFeeCollector == carlos.address
    assert fees.opcFee == to_wei(0.001)
    assert fees.marketFeeAvailable > 0
    assert fees.oceanFeeAvailable > 0

    FRE.collectMarketFee(exchange_id, {"from": carlos})

    assert OCEAN.balanceOf(carlos.address) == BT_before + fees.marketFeeAvailable

    # ==========================================================================
    # Change market fee collector from Carlos -> Bob
    
    # Only the current collector (Carlos) can update
    with pytest.raises(Exception, match="not marketFeeCollector"):
        FRE.updateMarketFeeCollector(exchange_id, bob.address, {"from": bob})

    FRE.updateMarketFeeCollector(exchange_id, bob.address, {"from": carlos})

    # ==========================================================================
    # Test deactivating exchange
    FRE.toggleExchangeState(exchange_id, {"from": alice})
    assert not FRE.isActive(exchange_id)
    FRE.toggleExchangeState(exchange_id, {"from": alice})

    # ==========================================================================
    # Test setting price (rate)
    FRE.setRate(exchange_id, to_wei("1.1"), {"from": alice})
    assert FRE.getRate(exchange_id) == to_wei("1.1")

