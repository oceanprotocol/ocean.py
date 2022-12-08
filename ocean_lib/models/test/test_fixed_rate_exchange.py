#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3.main import Web3

from ocean_lib.models.fixed_rate_exchange import (
    FixedExchangeBaseInOutData,
    FixedRateExchange,
    FixedRateExchangeDetails,
    FixedRateExchangeFeesInfo,
)
from ocean_lib.models.test.test_factory_router import OPC_SWAP_FEE_APPROVED
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.ddo_helpers import get_opc_collector_address_from_exchange
from tests.resources.helper_functions import deploy_erc721_erc20


@pytest.mark.unit
def test_exchange_rate_creation(
    config,
    ocean_token,
    publisher_wallet,
    consumer_wallet,
    another_consumer_wallet,
):
    """Test exchange with baseToken(OCEAN) 18 Decimals and dataToken 18 Decimals, RATE = 1"""
    amount = Web3.toWei("100000", "ether")
    amount_dt_to_sell = Web3.toWei("100", "ether")
    no_limit = Web3.toWei("100000000000000000000", "ether")
    rate = Web3.toWei("1", "ether")
    publish_market_swap_fee = int(1e15)  # 0.1%

    _, datatoken = deploy_erc721_erc20(config, publisher_wallet, publisher_wallet)

    pmt_collector = datatoken.getPaymentCollector()

    fixed_exchange = FixedRateExchange(
        config, get_address_of_type(config, "FixedPrice")
    )

    datatoken.mint(consumer_wallet.address, amount, {"from": publisher_wallet})
    assert datatoken.balanceOf(consumer_wallet.address) == amount
    number_of_exchanges_before = fixed_exchange.getNumberOfExchanges()

    tx_receipt = datatoken.create_fixed_rate(
        fixed_price_address=get_address_of_type(config, "FixedPrice"),
        base_token_address=ocean_token.address,
        owner=consumer_wallet.address,
        publish_market_swap_fee_collector=another_consumer_wallet.address,
        allowed_swapper=ZERO_ADDRESS,
        base_token_decimals=18,
        datatoken_decimals=18,
        fixed_rate=rate,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        with_mint=0,
        transaction_parameters={"from": publisher_wallet},
    )

    registered_event = tx_receipt.events["NewFixedRate"]

    assert fixed_exchange.getNumberOfExchanges() == (number_of_exchanges_before + 1)
    assert registered_event["owner"] == consumer_wallet.address
    assert len(fixed_exchange.getExchanges()) == (number_of_exchanges_before + 1)

    exchange_id = registered_event["exchangeId"]

    # Generate exchange id works
    generated_exchange_id = fixed_exchange.generateExchangeId(
        ocean_token.address, datatoken.address
    )
    assert generated_exchange_id == exchange_id

    # Exchange is active
    is_active = fixed_exchange.isActive(exchange_id)
    assert is_active, "Exchange was not activated correctly!"

    # Exchange should not have supply yet
    exchange_details = fixed_exchange.getExchange(exchange_id)

    assert (exchange_details[FixedRateExchangeDetails.DT_SUPPLY]) == 0
    assert (
        exchange_details[FixedRateExchangeDetails.BT_SUPPLY]
    ) == ocean_token.allowance(
        exchange_details[FixedRateExchangeDetails.EXCHANGE_OWNER],
        fixed_exchange.address,
    )

    # Consumer_wallet approves how many DT tokens wants to sell
    # Consumer_wallet only approves an exact amount so we can check supply etc later in the test
    datatoken.approve(
        fixed_exchange.address, amount_dt_to_sell, {"from": consumer_wallet}
    )
    # Another_consumer_wallet approves a big amount so that we don't need to re-approve during test
    ocean_token.approve(
        fixed_exchange.address,
        Web3.toWei("1000000", "ether"),
        {"from": another_consumer_wallet},
    )

    # Exchange should have supply and fees setup
    fee_info = fixed_exchange.getFeesInfo(exchange_id)
    assert fee_info[FixedRateExchangeFeesInfo.MARKET_FEE] == publish_market_swap_fee
    assert (
        fee_info[FixedRateExchangeFeesInfo.MARKET_FEE_COLLECTOR]
        == another_consumer_wallet.address
    )
    # token is approved, so 0.001
    assert fee_info[FixedRateExchangeFeesInfo.OPC_FEE] == OPC_SWAP_FEE_APPROVED
    assert fee_info[FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE] == 0
    assert fee_info[FixedRateExchangeFeesInfo.OCEAN_FEE_AVAILABLE] == 0

    # Check OPC fee collector
    get_opc_collector_address_from_exchange(fixed_exchange) == get_address_of_type(
        config, "OPFCommunityFeeCollector"
    )

    # Get exchange info
    # Get swapOceanFee
    # token address is not approved, so 0.002
    assert fixed_exchange.getOPCFee(ZERO_ADDRESS) == Web3.toWei("0.002", "ether")

    # Should get the exchange rate
    exchange_rate = fixed_exchange.getRate(exchange_id)

    assert rate == exchange_rate

    # Buy should fail if price is too high
    with pytest.raises(Exception, match="Too many base tokens"):
        fixed_exchange.buyDT(
            exchange_id,
            amount_dt_to_sell,
            1,
            ZERO_ADDRESS,
            0,
            {"from": another_consumer_wallet},
        )

    ocean_token.transfer(
        another_consumer_wallet.address,
        ocean_token.balanceOf(consumer_wallet.address),
        {"from": consumer_wallet},
    )

    # Test buy DT workflow
    ocean_balance_publisher_before_swap = ocean_token.balanceOf(consumer_wallet.address)
    datatoken_dt_balance_consumer_before_swap = datatoken.balanceOf(
        another_consumer_wallet.address
    )

    assert ocean_balance_publisher_before_swap == 0
    assert datatoken_dt_balance_consumer_before_swap == 0

    tx_receipt = fixed_exchange.buyDT(
        exchange_id,
        amount_dt_to_sell,
        no_limit,
        consumer_wallet.address,
        Web3.toWei("0.1", "ether"),
        {"from": another_consumer_wallet},
    )

    event_log = tx_receipt.events["Swapped"]

    # Check fixed rate exchange outputs. Rate = 1
    assert (
        event_log["baseTokenSwappedAmount"]
        - event_log["marketFeeAmount"]
        - event_log["oceanFeeAmount"]
        - event_log["consumeMarketFeeAmount"]
        == event_log["datatokenSwappedAmount"]
    )

    assert datatoken.balanceOf(another_consumer_wallet.address) == amount_dt_to_sell
    assert (
        ocean_token.balanceOf(consumer_wallet.address)
        > ocean_balance_publisher_before_swap
    )
    # Test sell DT workflow
    datatoken_dt_balance_consumer_before_swap = datatoken.balanceOf(
        another_consumer_wallet.address
    )
    datatoken.approve(
        fixed_exchange.address,
        datatoken_dt_balance_consumer_before_swap,
        {"from": consumer_wallet},
    )
    datatoken_balance_before = datatoken.balanceOf(consumer_wallet.address)
    ocean_balance_before = ocean_token.balanceOf(consumer_wallet.address)
    fixed_exchange.sellDT(
        exchange_id, amount_dt_to_sell, 0, ZERO_ADDRESS, 0, {"from": consumer_wallet}
    )

    # Base balance incremented as expect after selling data tokens
    assert (
        ocean_token.balanceOf(consumer_wallet.address)
        == fixed_exchange.calcBaseOutGivenInDT(
            exchange_id,
            amount_dt_to_sell,
            0,
        )[FixedExchangeBaseInOutData.BASE_TOKEN_AMOUNT]
        + ocean_balance_before
    )

    assert (
        datatoken.balanceOf(consumer_wallet.address)
        == datatoken_balance_before - amount_dt_to_sell
    )

    exchange_details = fixed_exchange.getExchange(exchange_id)

    assert (exchange_details[FixedRateExchangeDetails.DT_SUPPLY]) == amount_dt_to_sell
    assert (
        exchange_details[FixedRateExchangeDetails.BT_SUPPLY]
    ) == ocean_token.allowance(
        exchange_details[FixedRateExchangeDetails.EXCHANGE_OWNER],
        fixed_exchange.address,
    )

    # Fixed Rate Exchange owner withdraws DT balance

    dt_balance_before = datatoken.balanceOf(pmt_collector)

    receipt = fixed_exchange.collectDT(
        exchange_id,
        exchange_details[FixedRateExchangeDetails.DT_BALANCE],
        {"from": consumer_wallet},
    )

    logs = receipt.events["TokenCollected"]
    assert datatoken.balanceOf(pmt_collector) == dt_balance_before + logs["amount"]

    # Fixed Rate Exchange owner withdraws BT balance
    # Needs to buy because he sold all the DT amount and BT balance will be 0.
    datatoken.approve(
        fixed_exchange.address, Web3.toWei(10, "ether"), {"from": consumer_wallet}
    )

    fixed_exchange.buyDT(
        exchange_id,
        Web3.toWei(10, "ether"),
        no_limit,
        consumer_wallet.address,
        Web3.toWei("0.1", "ether"),
        {"from": another_consumer_wallet},
    )
    assert datatoken.balanceOf(
        another_consumer_wallet.address
    ) == amount_dt_to_sell + Web3.toWei(10, "ether")
    bt_balance_before = ocean_token.balanceOf(pmt_collector)

    receipt = fixed_exchange.collectBT(
        exchange_id,
        exchange_details[FixedRateExchangeDetails.BT_BALANCE],
        {"from": consumer_wallet},
    )

    logs = receipt.events["TokenCollected"]

    assert ocean_token.balanceOf(pmt_collector) == bt_balance_before + logs["amount"]

    # Exchange should have fees available and claimable
    # Market fee collector bt balance
    bt_balance_before = ocean_token.balanceOf(another_consumer_wallet.address)

    fee_info = fixed_exchange.getFeesInfo(exchange_id)

    assert fee_info[FixedRateExchangeFeesInfo.MARKET_FEE] == publish_market_swap_fee
    assert (
        fee_info[FixedRateExchangeFeesInfo.MARKET_FEE_COLLECTOR]
        == another_consumer_wallet.address
    )
    assert fee_info[FixedRateExchangeFeesInfo.OPC_FEE] == Web3.toWei("0.001", "ether")
    assert fee_info[FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE] > 0
    assert fee_info[FixedRateExchangeFeesInfo.OCEAN_FEE_AVAILABLE] > 0

    fixed_exchange.collectMarketFee(exchange_id, {"from": another_consumer_wallet})

    assert (
        ocean_token.balanceOf(another_consumer_wallet.address)
        == bt_balance_before + fee_info[FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE]
    )

    # Market fee collector update
    # Only market fee collector should be able to update market_fee_collector
    with pytest.raises(Exception, match="not marketFeeCollector"):
        fixed_exchange.updateMarketFeeCollector(
            exchange_id, consumer_wallet.address, {"from": consumer_wallet}
        )

    fixed_exchange.updateMarketFeeCollector(
        exchange_id, consumer_wallet.address, {"from": another_consumer_wallet}
    )

    # Deactive exchange should work
    fixed_exchange.toggleExchangeState(exchange_id, {"from": publisher_wallet})
    assert not fixed_exchange.isActive(exchange_id)
    fixed_exchange.toggleExchangeState(exchange_id, {"from": publisher_wallet})

    # Set exchange rate exchange should work
    fixed_exchange.setRate(
        exchange_id, Web3.toWei("1.1", "ether"), {"from": publisher_wallet}
    )
    assert fixed_exchange.getRate(exchange_id) == Web3.toWei("1.1", "ether")
