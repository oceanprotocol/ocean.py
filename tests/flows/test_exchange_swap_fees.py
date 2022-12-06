#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from decimal import Decimal

import pytest
from web3.main import Web3

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.models.test.test_factory_router import (
    OPC_SWAP_FEE_APPROVED,
    OPC_SWAP_FEE_NOT_APPROVED,
)
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from tests.resources.ddo_helpers import get_opc_collector_address_from_exchange
from tests.resources.helper_functions import (
    base_token_to_datatoken,
    int_units,
    transfer_base_token_if_balance_lte,
)

toWei, fromWei = Web3.toWei, Web3.fromWei

@pytest.mark.unit
@pytest.mark.parametrize(
    "bt_name, pub_mkt_swap_fee, consume_mkt_swap_fee, price, with_mint",
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
    bt_name: str,
    datatoken: Datatoken,
    pub_mkt_swap_fee: str,
    consume_mkt_swap_fee: str,
    price: str,
    with_mint: int,
):
    """
    Tests fixed rate exchange swap fees with OCEAN, DAI, and USDC as base token

    OCEAN is an approved base token with 18 decimals (OPC Fee = 0.1%)
    DAI is a non-approved base token with 18 decimals (OPC Fee = 0.2%)
    USDC is a non-approved base token with 6 decimals (OPC Fee = 0.2%)
    """
    bt_deployer_wallet = factory_deployer_wallet
    consume_mkt_swap_fee_collector = another_consumer_wallet
    ocean = Ocean(config)
    bt = Datatoken(config, get_address_of_type(config, bt_name))
    dt = datatoken

    transfer_base_token_if_balance_lte(
        config=config,
        base_token_address=bt.address,
        from_wallet=bt_deployer_wallet,
        recipient=publisher_wallet.address,
        min_balance=int_units("1500", bt.decimals()),
        amount_to_transfer=int_units("1500", bt.decimals()),
    )

    transfer_base_token_if_balance_lte(
        config=config,
        base_token_address=bt.address,
        from_wallet=bt_deployer_wallet,
        recipient=consumer_wallet.address,
        min_balance=int_units("1500", bt.decimals()),
        amount_to_transfer=int_units("1500", bt.decimals()),
    )

    pub_mkt_swap_fee = toWei(pub_mkt_swap_fee, "ether")
    consume_mkt_swap_fee = toWei(consume_mkt_swap_fee, "ether")

    FRE = ocean.fixed_rate_exchange
    price_wei = toWei(price, "ether")
    receipt = dt.contract.createFixedRate(
        fixed_price_address=FRE.address,
        base_token_address=bt.address,
        owner=publisher_wallet.address,
        publish_market_swap_fee_collector=publisher_wallet.address,
        allowed_swapper=ZERO_ADDRESS,
        base_token_decimals=bt.decimals(),
        datatoken_decimals=dt.decimals(),
        fixed_rate=price_wei,
        publish_market_swap_fee_amount=pub_mkt_swap_fee,
        with_mint=with_mint,
        transaction_parameters={"from": publisher_wallet},
    )
    assert FRE.address == receipt.events["NewFixedRate"]["exchangeContract"]

    exchange_id = receipt.events["NewFixedRate"]["exchangeId"]
    assert exchange_id == FRE.generateExchangeId(bt.address, dt.address)

    # Verify fee collectors are configured correctly
    fees = FRE.fees(exchange_id)
    assert fees.marketFeeCollector == publisher_wallet.address

    # Verify fees are configured correctly
    router = ocean.factory_router()
    if router.isApprovedToken(bt.address):
        assert fees.opcFee == OPC_SWAP_FEE_APPROVED
    else:
        assert fees.opcFee == OPC_SWAP_FEE_NOT_APPROVED
    assert FRE.getOPCFee(bt.address) == fees.opcFee
    assert FRE.getOPCFee(bt.address) == router.getOPCFee(bt.address)
    assert FRE.getMarketFee(exchange_id) == pub_mkt_swap_fee
    assert fees.marketFee == pub_mkt_swap_fee

    # Verify 0 fees have been collected so far
    assert fees.marketFeeAvailable == 0
    assert fees.oceanFeeAvailable == 0

    # Verify that price is configured correctly
    assert fromWei(FRE.getRate(exchange_id), "ether") == price

    # Verify exchange starting balance and supply.
    status = FRE.status(exchange_id)
    assert status.btBalance == 0
    assert status.dtBalance == 0
    assert status.btSupply == 0
    if with_mint == 1:
        assert status.dtSupply == dt.cap()
    else:
        assert status.dtSupply == 0

    # Grant infinite approvals for exchange to spend consumer's BT and DT
    dt.approve(FRE.address, MAX_UINT256, {"from": consumer_wallet})
    bt.approve(FRE.address, MAX_UINT256, {"from": consumer_wallet})

    # if the exchange cannot mint it's own datatokens,
    # Mint datatokens to publisher and
    # Grant infinite approval for exchange to spend publisher's datatokens
    if with_mint != 1:
        dt.mint(publisher_wallet.address, MAX_UINT256, {"from": publisher_wallet})
        dt.approve(FRE.address, MAX_UINT256, {"from": publisher_wallet})

    one_base_token = int_units("1", bt.decimals())
    dt_per_bt_wei = toWei(Decimal(1) / Decimal(price), "ether")

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "buy",
        base_token_to_datatoken(one_base_token, bt.decimals(), dt_per_bt_wei),
        config,
        FRE,
        exchange_id,
        consume_mkt_swap_fee_collector.address,
        consume_mkt_swap_fee,
        consumer_wallet,
    )

    buy_or_sell_dt_and_verify_balances_swap_fees(
        "sell",
        base_token_to_datatoken(one_base_token, bt.decimals(), dt_per_bt_wei),
        config,
        FRE,
        exchange_id,
        consume_mkt_swap_fee_collector.address,
        consume_mkt_swap_fee,
        consumer_wallet,
    )

    # Collect BT
    _collect_bt(config, FRE, exchange_id, consumer_wallet)
    _collect_dt(config, FRE, exchange_id, consumer_wallet)

    # Update publish market swap fee
    new_pub_mkt_swap_fee = toWei(0.09, "ether")
    FRE.updateMarketFee(
        exchange_id, new_pub_mkt_swap_fee, {"from": publisher_wallet}
    )
    fees = FRE.fees(exchange_id)
    assert fees.marketFee == new_pub_mkt_swap_fee

    # Increase rate (base tokens per datatoken) by 1
    new_price_wei = price_wei + toWei(1, "ether")
    FRE.setRate(exchange_id, new_price_wei, {"from": publisher_wallet})
    assert FRE.getRate(exchange_id) == new_price_wei

    new_dt_per_bt_wei = toWei(
        Decimal(1) / fromWei(new_price_wei, "ether"), "ether"
    )
    buy_or_sell_dt_and_verify_balances_swap_fees(
        "buy",
        base_token_to_datatoken(one_base_token, bt.decimals(), new_dt_per_bt_wei),
        config,
        FRE,
        exchange_id,
        consume_mkt_swap_fee_collector.address,
        consume_mkt_swap_fee,
        consumer_wallet,
    )

    # Update market fee collector to be the consumer
    new_market_fee_collector = consumer_wallet.address
    FRE.updateMarketFeeCollector(
        exchange_id, new_market_fee_collector, {"from": publisher_wallet}
    )
    
    fees = FRE.fees(exchange_id)
    assert fees.marketFeeCollector == new_market_fee_collector

    _collect_market_fee(config, FRE, exchange_id, consumer_wallet)
    _collect_ocean_fee(config, FRE, exchange_id, consumer_wallet)


def buy_or_sell_dt_and_verify_balances_swap_fees(
    buy_or_sell: str,
    dt_amount: int,
    config: dict,
    FRE: FixedRateExchange,
    exchange_id: bytes,
    consume_mkt_swap_fee_address: str,
    consume_mkt_swap_fee: int,
    consumer_wallet,
):
    status = FRE.status(exchange_id)
    bt = Datatoken(config, status.baseToken)
    dt = Datatoken(config, status.datatoken)

    # Get balances before swap
    consumer_bt_balance1 = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance1 = dt.balanceOf(consumer_wallet.address)
    exchange_bt_balance1 = status.btBalance
    exchange_dt_balance1 = status.dtBalance

    fees = FRE.fees(exchange_id)

    publish_market_fee_bt_balance1 = fees.marketFeeAvailable
    opc_fee_bt_balance1 = fees.oceanFeeAvailable
    consume_mkt_fee_bt_balance1 = bt.balanceOf(consume_mkt_swap_fee_address)

    if buy_or_sell == "buy":
        method = FRE.buyDT
        min_or_max_base_token = MAX_UINT256
    else:
        method = FRE.sellDT
        min_or_max_base_token = 0

    # Buy or Sell DT
    receipt = method(
        exchange_id,
        dt_amount,
        min_or_max_base_token,
        consume_mkt_swap_fee_address,
        consume_mkt_swap_fee,
        {"from": consumer_wallet},
    )

    # Get exchange info again
    status = FRE.status(exchange_id)

    # Get balances after swap
    consumer_bt_balance2 = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance2 = dt.balanceOf(consumer_wallet.address)
    exchange_bt_balance2 = status.btBalance
    exchange_dt_balance2 = status.dtBalance

    # Get Swapped event
    swapped_event = receipt.events["Swapped"]

    # Assign "in" token and "out" token
    if swapped_event["tokenOutAddress"] == dt.address:
        in_token_amount = swapped_event["baseTokenSwappedAmount"]
        out_token_amount = swapped_event["datatokenSwappedAmount"]
        consumer_in_token_balance1 = consumer_bt_balance1
        consumer_out_token_balance1 = consumer_dt_balance1
        consumer_in_token_balance2 = consumer_bt_balance2
        consumer_out_token_balance2 = consumer_dt_balance2
    else:
        in_token_amount = swapped_event["datatokenSwappedAmount"]
        out_token_amount = swapped_event["baseTokenSwappedAmount"]
        consumer_in_token_balance1 = consumer_dt_balance1
        consumer_out_token_balance1 = consumer_bt_balance1
        consumer_in_token_balance2 = consumer_dt_balance2
        consumer_out_token_balance2 = consumer_bt_balance2

    # Check consumer balances
    assert (
        consumer_in_token_balance1 - in_token_amount
        == consumer_in_token_balance2
    )
    assert (
        consumer_out_token_balance1 + out_token_amount
        == consumer_out_token_balance2
    )

    # Check exchange balances
    if swapped_event["tokenOutAddress"] == dt.address:
        assert (
            exchange_bt_balance1
            + swapped_event["baseTokenSwappedAmount"]
            - swapped_event["marketFeeAmount"]
            - swapped_event["oceanFeeAmount"]
            - swapped_event["consumeMarketFeeAmount"]
            == exchange_bt_balance2
        )
        # When buying DT, exchange DT balance doesn't change because exchange mints DT
        assert exchange_dt_balance1 == exchange_dt_balance2
    else:
        assert (
            exchange_bt_balance1
            - swapped_event["baseTokenSwappedAmount"]
            - swapped_event["marketFeeAmount"]
            - swapped_event["oceanFeeAmount"]
            - swapped_event["consumeMarketFeeAmount"]
            == exchange_bt_balance2
        )
        assert (
            exchange_dt_balance1 + swapped_event["datatokenSwappedAmount"]
            == exchange_dt_balance2
        )

    # Get current fee balances
    # Exchange fees are always base tokens
    fees = FRE.fees(exchange_id)
    publish_market_fee_bt_balance2 = fees.marketFeeAvailable
    opc_fee_bt_balance2 = fees.oceanFeeAvailable
    consume_mkt_fee_bt_balance2 = bt.balanceOf(consume_mkt_swap_fee_address)

    # Check fees
    assert (
        publish_market_fee_bt_balance1 + swapped_event["marketFeeAmount"]
        == publish_market_fee_bt_balance2
    )
    assert (
        opc_fee_bt_balance1 + swapped_event["oceanFeeAmount"]
        == opc_fee_bt_balance2
    )
    assert (
        consume_mkt_fee_bt_balance1 + swapped_event["consumeMarketFeeAmount"]
        == consume_mkt_fee_bt_balance2
    )


def _collect_bt(config, FRE, exchange_id, from_wallet):
    BT = Datatoken(config, FRE.status(exchange_id).baseToken)
    pubmkt_address = dt.getPaymentCollector()

    BT_exchange1 = FRE.status(exchange_id).btBalance
    BT_pubmkt1 = BT.balanceOf(pubmkt_address)

    FRE.collectBT(exchange_id, BT_exchange1, {"from": from_wallet})

    BT_exchange2 = FRE.status(exchange_id).btBalance
    BT_pubmkt2 = BT.balanceOf(pubmkt_address)

    assert BT_exchange2 == 0
    assert BT_pubmkt2 = (BT_pubmkt1 + BT_exchange1)

def _collect_dt(config, FRE, exchange_id, from_wallet):
    DT = Datatoken(config, FRE.status(exchange_id).datatoken)
    pubmkt_address = dt.getPaymentCollector()

    DT_exchange1 = FRE.status(exchange_id).dtBalance
    DT_pubmkt1 = DT.balanceOf(pubmkt_address)

    FRE.collectDT(exchange_id, DT_exchange1, {"from": from_wallet})

    DT_exchange2 = FRE.status(exchange_id).dtBalance
    DT_pubmkt2 = DT.balanceOf(pubmkt_address)

    assert DT_exchange2 == 0
    assert DT_pubmkt2 == (DT_pubmkt1 + DT_exchange1)

def _collect_market_fee(config, FRE, exchange_id, from_wallet):
    BT = Datatoken(config, FRE.status(exchange_id).baseToken)
    collector_addr = FRE.status(exchange_id).marketFeeCollector

    BT_mktfee1 = FRE.fees(exchange_id).marketFeeAvailable
    BT_collector1 = BT.balanceOf(collector_addr)

    FRE.collectMarketFee(exchange_id, {"from": from_wallet})

    BT_mktfee2 = FRE.fees(exchange_id).marketFeeAvailable
    BT_collector2 = BT.balanceOf(collector_addr)

    assert BT_mktfee2 == 0
    assert BT_collector2 == (BT_collector1 + BT_mktfee1)

    
def _collect_opc_fee(config, FRE, exchange_id, from_wallet):
    BT = Datatoken(config, FRE.status(exchange_id).baseToken)
    collector_addr = get_opc_collector_address_from_exchange(FRE)

    BT_mktfee1 = FRE.fees(exchange_id).oceanFeeAvailable
    BT_collector1 = BT.balanceOf(collector_addr)

    FRE.collectOceanFee(exchange_id, {"from": from_wallet})

    BT_mktfee2 = FRE.fees(exchange_id).oceanFeeAvailable
    BT_collector2 = BT.balanceOf(collector_addr)

    assert BT_mktfee2 == 0
    assert BT_collector2 == (BT_collector1 + BT_mktfee1)
