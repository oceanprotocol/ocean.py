#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.fixed_rate_exchange import (
    FixedExchangeBaseInOutData,
    FixedRateExchange,
    FixedRateExchangeDetails,
    FixedRateExchangeFeesInfo,
)
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


@pytest.mark.unit
def test_properties(web3, config):
    """Tests the events' properties."""

    fixed_exchange = FixedRateExchange(web3, get_address_of_type(config, "FixedPrice"))

    assert (
        fixed_exchange.event_ExchangeCreated.abi["name"]
        == FixedRateExchange.EVENT_EXCHANGE_CREATED
    )
    assert (
        fixed_exchange.event_ExchangeRateChanged.abi["name"]
        == FixedRateExchange.EVENT_EXCHANGE_RATE_CHANGED
    )
    assert (
        fixed_exchange.event_ExchangeActivated.abi["name"]
        == FixedRateExchange.EVENT_EXCHANGE_ACTIVATED
    )
    assert (
        fixed_exchange.event_ExchangeDeactivated.abi["name"]
        == FixedRateExchange.EVENT_EXCHANGE_DEACTIVATED
    )
    assert fixed_exchange.event_Swapped.abi["name"] == FixedRateExchange.EVENT_SWAPPED
    assert (
        fixed_exchange.event_TokenCollected.abi["name"]
        == FixedRateExchange.EVENT_TOKEN_COLLECTED
    )
    assert (
        fixed_exchange.event_OceanFeeCollected.abi["name"]
        == FixedRateExchange.EVENT_OCEAN_FEE_COLLECTED
    )
    assert (
        fixed_exchange.event_MarketFeeCollected.abi["name"]
        == FixedRateExchange.EVENT_MARKET_FEE_COLLECTED
    )
    assert (
        fixed_exchange.event_ConsumeMarketFee.abi["name"]
        == FixedRateExchange.EVENT_CONSUME_MARKET_FEE
    )
    assert (
        fixed_exchange.event_PublishMarketFeeChanged.abi["name"]
        == FixedRateExchange.EVENT_PUBLISH_MARKET_FEE_CHANGED
    )
    assert (
        fixed_exchange.event_SWAP_FEES.abi["name"]
        == FixedRateExchange.EVENT_LOG_SWAP_FEES
    )


@pytest.mark.unit
def test_exchange_rate_creation(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Test exchange with baseToken(OCEAN) 18 Decimals and dataToken 18 Decimals, RATE = 1"""
    cap = to_wei("100000")
    amount_dt_to_sell = to_wei("100")
    no_limit = to_wei("100000000000000000000")
    rate = to_wei("1")
    publish_market_fee = int(1e15)  # 0.1%
    ocean_token = ERC20Token(web3, get_address_of_type(config, "Ocean"))

    fixed_exchange = FixedRateExchange(web3, get_address_of_type(config, "FixedPrice"))

    erc721, erc20 = deploy_erc721_erc20(
        web3, config, consumer_wallet, consumer_wallet, cap
    )

    erc20.mint(consumer_wallet.address, cap, consumer_wallet)
    assert erc20.balanceOf(consumer_wallet.address) == cap
    number_of_exchanges_before = fixed_exchange.get_number_of_exchanges()

    tx = erc20.create_fixed_rate(
        fixed_price_address=get_address_of_type(config, "FixedPrice"),
        base_token_address=get_address_of_type(config, "Ocean"),
        owner=consumer_wallet.address,
        swap_market_fee_collector=another_consumer_wallet.address,
        allowed_swapper=ZERO_ADDRESS,
        base_token_decimals=18,
        datatoken_decimals=18,
        fixed_rate=rate,
        publish_market_fee=publish_market_fee,
        with_mint=0,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    registered_event = erc20.get_event_log(
        event_name=ERC721FactoryContract.EVENT_NEW_FIXED_RATE,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert fixed_exchange.get_number_of_exchanges() == (number_of_exchanges_before + 1)
    assert registered_event[0].args.owner == consumer_wallet.address
    assert len(fixed_exchange.get_exchanges()) == (number_of_exchanges_before + 1)

    exchange_id = registered_event[0].args.exchangeId

    # Generate exchange id works
    generated_exchange_id = fixed_exchange.generate_exchange_id(
        base_token=get_address_of_type(config, "Ocean"),
        datatoken=erc20.address,
        exchange_owner=consumer_wallet.address,
    )
    assert generated_exchange_id == exchange_id

    # Exchange is active
    is_active = fixed_exchange.is_active(exchange_id)
    assert is_active, "Exchange was not activated correctly!"

    # Exchange should not have supply yet
    exchange_details = fixed_exchange.get_exchange(exchange_id)

    assert (exchange_details[FixedRateExchangeDetails.DT_SUPPLY]) == 0
    assert (
        exchange_details[FixedRateExchangeDetails.BT_SUPPLY]
    ) == ocean_token.allowance(
        exchange_details[FixedRateExchangeDetails.EXCHANGE_OWNER],
        fixed_exchange.address,
    )

    # Consumer_wallet approves how many DT tokens wants to sell
    # Consumer_wallet only approves an exact amount so we can check supply etc later in the test
    erc20.approve(fixed_exchange.address, amount_dt_to_sell, consumer_wallet)
    # Another_consumer_wallet approves a big amount so that we don't need to re-approve during test
    ocean_token.approve(
        fixed_exchange.address, to_wei("1000000"), another_consumer_wallet
    )

    # Exchange should have supply and fees setup
    fee_info = fixed_exchange.get_fees_info(exchange_id)

    assert fee_info[FixedRateExchangeFeesInfo.MARKET_FEE] == publish_market_fee
    assert (
        fee_info[FixedRateExchangeFeesInfo.MARKET_FEE_COLLECTOR]
        == another_consumer_wallet.address
    )
    # token is approved, so 0.001
    assert fee_info[FixedRateExchangeFeesInfo.OPC_FEE] == to_wei("0.001")
    assert fee_info[FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE] == 0
    assert fee_info[FixedRateExchangeFeesInfo.OCEAN_FEE_AVAILABLE] == 0

    # Get exchange info
    # Get swapOceanFee
    # token address is not approved, so 0.002
    assert fixed_exchange.get_opc_fee(ZERO_ADDRESS) == to_wei("0.002")

    # Should get the exchange rate
    exchange_rate = fixed_exchange.get_rate(exchange_id)

    assert rate == exchange_rate

    # Buy should fail if price is too high
    with pytest.raises(exceptions.ContractLogicError) as err:
        fixed_exchange.buy_dt(
            exchange_id, amount_dt_to_sell, 1, ZERO_ADDRESS, 0, another_consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert FixedRateExchange: Too many base tokens"
    )

    ocean_token.transfer(
        another_consumer_wallet.address,
        ocean_token.balanceOf(consumer_wallet.address),
        consumer_wallet,
    )

    # Test buy DT workflow
    ocean_balance_publisher_before_swap = ocean_token.balanceOf(consumer_wallet.address)
    erc20_dt_balance_consumer_before_swap = erc20.balanceOf(
        another_consumer_wallet.address
    )

    assert ocean_balance_publisher_before_swap == 0
    assert erc20_dt_balance_consumer_before_swap == 0

    receipt = fixed_exchange.buy_dt(
        exchange_id,
        amount_dt_to_sell,
        no_limit,
        consumer_wallet.address,
        to_wei("0.1"),
        another_consumer_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(receipt)

    event_log = fixed_exchange.get_event_log(
        event_name=FixedRateExchange.EVENT_SWAPPED,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    # Check fixed rate exchange outputs. Rate = 1
    assert (
        event_log[0].args.baseTokenSwappedAmount
        - event_log[0].args.marketFeeAmount
        - event_log[0].args.oceanFeeAmount
        - event_log[0].args.consumeMarketFeeAmount
        == event_log[0].args.datatokenSwappedAmount
    )

    assert erc20.balanceOf(another_consumer_wallet.address) == amount_dt_to_sell
    assert (
        ocean_token.balanceOf(consumer_wallet.address)
        > ocean_balance_publisher_before_swap
    )
    # Test sell DT workflow
    erc20_dt_balance_consumer_before_swap = erc20.balanceOf(
        another_consumer_wallet.address
    )
    erc20.approve(
        fixed_exchange.address, erc20_dt_balance_consumer_before_swap, consumer_wallet
    )
    erc20_balance_before = erc20.balanceOf(consumer_wallet.address)
    ocean_balance_before = ocean_token.balanceOf(consumer_wallet.address)
    fixed_exchange.sell_dt(
        exchange_id, amount_dt_to_sell, 0, ZERO_ADDRESS, 0, consumer_wallet
    )

    # Base balance incremented as expect after selling data tokens
    assert (
        ocean_token.balanceOf(consumer_wallet.address)
        == fixed_exchange.calc_base_out_given_in_dt(
            exchange_id=exchange_id,
            datatoken_amount=amount_dt_to_sell,
            swap_market_fee=0,
        )[FixedExchangeBaseInOutData.BASE_TOKEN_AMOUNT]
        + ocean_balance_before
    )

    assert (
        erc20.balanceOf(consumer_wallet.address)
        == erc20_balance_before - amount_dt_to_sell
    )

    exchange_details = fixed_exchange.get_exchange(exchange_id)

    assert (exchange_details[FixedRateExchangeDetails.DT_SUPPLY]) == amount_dt_to_sell
    assert (
        exchange_details[FixedRateExchangeDetails.BT_SUPPLY]
    ) == ocean_token.allowance(
        exchange_details[FixedRateExchangeDetails.EXCHANGE_OWNER],
        fixed_exchange.address,
    )

    # Fixed Rate Exchange owner withdraws DT balance

    erc20_balance_before = erc20.balanceOf(consumer_wallet.address)

    # Only owner can withdraw
    with pytest.raises(exceptions.ContractLogicError) as err:
        fixed_exchange.collect_dt(exchange_id, another_consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert FixedRateExchange: invalid exchange owner"
    )
    tx = fixed_exchange.collect_dt(exchange_id, consumer_wallet)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    logs = fixed_exchange.get_event_log(
        event_name=FixedRateExchange.EVENT_TOKEN_COLLECTED,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert (
        erc20.balanceOf(consumer_wallet.address)
        == erc20_balance_before + logs[0].args.amount
    )

    # Fixed Rate Exchange owner withdraws BT balance

    bt_balance_before = ocean_token.balanceOf(consumer_wallet.address)

    with pytest.raises(exceptions.ContractLogicError) as err:
        fixed_exchange.collect_bt(exchange_id, another_consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert FixedRateExchange: invalid exchange owner"
    )

    tx = fixed_exchange.collect_bt(exchange_id, consumer_wallet)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    logs = fixed_exchange.get_event_log(
        event_name=FixedRateExchange.EVENT_TOKEN_COLLECTED,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert (
        ocean_token.balanceOf(consumer_wallet.address)
        == bt_balance_before + logs[0].args.amount
    )

    # Exchange should have fees available and claimable
    # Market fee collector bt balance
    bt_balance_before = ocean_token.balanceOf(another_consumer_wallet.address)

    fee_info = fixed_exchange.get_fees_info(exchange_id)

    assert fee_info[FixedRateExchangeFeesInfo.MARKET_FEE] == publish_market_fee
    assert (
        fee_info[FixedRateExchangeFeesInfo.MARKET_FEE_COLLECTOR]
        == another_consumer_wallet.address
    )
    assert fee_info[FixedRateExchangeFeesInfo.OPC_FEE] == to_wei("0.001")
    assert fee_info[FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE] > 0
    assert fee_info[FixedRateExchangeFeesInfo.OCEAN_FEE_AVAILABLE] > 0

    fixed_exchange.collect_market_fee(exchange_id, another_consumer_wallet)

    assert (
        ocean_token.balanceOf(another_consumer_wallet.address)
        == bt_balance_before + fee_info[FixedRateExchangeFeesInfo.MARKET_FEE_AVAILABLE]
    )

    # Market fee collector update
    # Only market fee collector should be able to update market_fee_collector
    with pytest.raises(exceptions.ContractLogicError) as err:
        fixed_exchange.update_market_fee_collector(
            exchange_id, consumer_wallet.address, consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert not marketFeeCollector"
    )

    fixed_exchange.update_market_fee_collector(
        exchange_id, consumer_wallet.address, another_consumer_wallet
    )

    # Deactive exchange should work
    fixed_exchange.toggle_exchange_state(exchange_id, consumer_wallet)
    assert not fixed_exchange.is_active(exchange_id)
    fixed_exchange.toggle_exchange_state(exchange_id, consumer_wallet)

    # Set exchange rate exchange should work
    fixed_exchange.set_rate(exchange_id, to_wei("1.1"), consumer_wallet)
    assert fixed_exchange.get_rate(exchange_id) == to_wei("1.1")
