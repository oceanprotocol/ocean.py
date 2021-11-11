#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.v4.dispenser import DispenserV4
from ocean_lib.models.v4.erc20_enterprise import ERC20Enterprise
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.fixed_rate_exchange import FixedRateExchangeV4
from ocean_lib.models.v4.models_structures import DispenserData, FixedData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


def test_buy_from_dispenser_and_order(
    web3, config, consumer_wallet, publisher_wallet, factory_deployer_wallet
):
    mock_usdc_contract = ERC20Token(web3, get_address_of_type(config, "MockUSDC"))
    mock_dai_contract = ERC20Token(web3, get_address_of_type(config, "MockDAI"))
    dispenser = DispenserV4(web3, get_address_of_type(config, "Dispenser"))

    _, erc20_enterprise_token = deploy_erc721_erc20(
        web3=web3,
        config=config,
        cap=web3.toWei(100, "ether"),
        erc20_minter=consumer_wallet,
        erc721_publisher=consumer_wallet,
        template_index=2,
    )
    erc20_enterprise_token = ERC20Enterprise(web3, erc20_enterprise_token.address)

    dispenser_data = DispenserData(
        dispenser_address=dispenser.address,
        allowed_swapper=ZERO_ADDRESS,
        max_balance=web3.toWei(1, "ether"),
        max_tokens=web3.toWei(1, "ether"),
    )
    tx = erc20_enterprise_token.create_dispenser(
        dispenser_data=dispenser_data, from_wallet=consumer_wallet, with_mint=True
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)
    assert tx_receipt["status"] == 1

    status = dispenser.status(erc20_enterprise_token.address)

    assert status[0] is True
    assert status[1] == consumer_wallet.address
    assert status[2] is True

    with pytest.raises(exceptions.ContractLogicError) as err:
        dispenser.dispense(
            data_token=erc20_enterprise_token.address,
            amount=web3.toWei(1, "ether"),
            destination=publisher_wallet.address,
            from_wallet=publisher_wallet,
        )

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert This address is not allowed to request DT"
    )

    consume_fee_amount = web3.toWei(2, "ether")
    consume_fee_address = publisher_wallet.address
    erc20_enterprise_token.set_publishing_market_fee(
        publish_market_fee_address=consume_fee_address,
        publish_market_fee_token=mock_usdc_contract.address,
        publish_market_fee_amount=consume_fee_amount,
        from_wallet=consumer_wallet,
    )
    publish_fees = erc20_enterprise_token.get_publishing_market_fee()

    mock_usdc_contract.transfer(
        to=consumer_wallet.address,
        amount=publish_fees[2],
        from_wallet=factory_deployer_wallet,
    )

    mock_usdc_contract.approve(
        spender=erc20_enterprise_token.address,
        amount=consume_fee_amount,
        from_wallet=consumer_wallet,
    )

    mock_dai_contract.transfer(
        to=consumer_wallet.address,
        amount=consume_fee_amount,
        from_wallet=factory_deployer_wallet,
    )

    mock_dai_contract.approve(
        spender=erc20_enterprise_token.address,
        amount=consume_fee_amount,
        from_wallet=consumer_wallet,
    )

    order_params = {
        "consumer": consume_fee_address,
        "amount": web3.toWei(1, "ether"),
        "serviceId": 1,
        "consumeFeeAddress": consume_fee_address,
        "consumeFeeToken": mock_dai_contract.address,
        "consumeFeeAmount": consume_fee_amount,
    }
    opf_collector_address = get_address_of_type(config, "OPFCommunityFeeCollector")

    balance_consume_before = mock_dai_contract.balanceOf(consume_fee_address)
    balance_opf_consume_before = mock_dai_contract.balanceOf(opf_collector_address)
    balance_publish_before = mock_usdc_contract.balanceOf(publisher_wallet.address)
    balance_opf_publish_before = mock_usdc_contract.balanceOf(opf_collector_address)

    tx = erc20_enterprise_token.buy_from_dispenser_and_order(
        order_params=order_params,
        dispenser_address=dispenser.address,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert tx_receipt["status"] == 1

    balance_consume = mock_dai_contract.balanceOf(consume_fee_address)
    balance_opf_consume = mock_dai_contract.balanceOf(opf_collector_address)

    balance_publish = mock_usdc_contract.balanceOf(publish_fees[0])
    balance_opf_publish = mock_usdc_contract.balanceOf(opf_collector_address)

    expected_consume = consume_fee_amount - consume_fee_amount / 100
    expected_opf_consume = consume_fee_amount / 100

    expected_publish = publish_fees[2] - publish_fees[2] / 100
    expected_opf_publish = publish_fees[2] / 100

    assert balance_consume - balance_consume_before == expected_consume
    assert balance_opf_consume - balance_opf_consume_before == expected_opf_consume

    assert balance_publish - balance_publish_before == expected_publish
    assert balance_opf_publish - balance_opf_publish_before == expected_opf_publish

    assert (
        erc20_enterprise_token.balanceOf(erc20_enterprise_token.get_fee_collector())
        == 0
    )


def test_buy_from_fre_and_order(
    web3, config, consumer_wallet, publisher_wallet, factory_deployer_wallet
):
    mock_usdc_contract = ERC20Token(web3, get_address_of_type(config, "MockUSDC"))
    mock_dai_contract = ERC20Token(web3, get_address_of_type(config, "MockDAI"))
    fixed_rate_exchange = FixedRateExchangeV4(
        web3, get_address_of_type(config, "FixedPrice")
    )

    _, erc20_enterprise_token = deploy_erc721_erc20(
        web3=web3,
        config=config,
        cap=web3.toWei(100, "ether"),
        erc20_minter=consumer_wallet,
        erc721_publisher=consumer_wallet,
        template_index=2,
    )
    erc20_enterprise_token = ERC20Enterprise(web3, erc20_enterprise_token.address)

    fixed_data = FixedData(
        fixed_price_address=fixed_rate_exchange.address,
        addresses=[
            mock_usdc_contract.address,
            consumer_wallet.address,
            consumer_wallet.address,
            ZERO_ADDRESS,
        ],
        uints=[18, 18, web3.toWei(1, "ether"), web3.toWei(1, "ether"), 1],
    )

    tx = erc20_enterprise_token.create_fixed_rate(
        fixed_data=fixed_data,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert tx_receipt["status"] == 1

    new_fixed_rate_event = erc20_enterprise_token.get_event_log(
        "NewFixedRate",
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    exchange_id = new_fixed_rate_event[0]["args"]["exchangeId"]
    status = fixed_rate_exchange.get_exchange(exchange_id)

    assert status[6] is True  # is active
    assert status[11] is True  # is minter

    with pytest.raises(exceptions.ContractLogicError) as err:
        fixed_rate_exchange.buy_dt(
            exchange_id=exchange_id,
            data_token_amount=web3.toWei(1, "ether"),
            max_base_token_amount=web3.toWei(1, "ether"),
            from_wallet=publisher_wallet,
        )

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert FixedRateExchange: This address is not allowed to swap"
    )

    consume_fee_amount = web3.toWei(5, "ether")
    consume_fee_address = publisher_wallet.address
    erc20_enterprise_token.set_publishing_market_fee(
        publish_market_fee_address=consume_fee_address,
        publish_market_fee_token=mock_usdc_contract.address,
        publish_market_fee_amount=consume_fee_amount,
        from_wallet=consumer_wallet,
    )
    publish_fees = erc20_enterprise_token.get_publishing_market_fee()

    mock_usdc_contract.transfer(
        to=consumer_wallet.address,
        amount=consume_fee_amount,
        from_wallet=factory_deployer_wallet,
    )
    mock_usdc_contract.approve(
        spender=erc20_enterprise_token.address,
        amount=web3.toWei(1000, "ether"),
        from_wallet=consumer_wallet,
    )
    mock_dai_contract.transfer(
        to=consumer_wallet.address,
        amount=consume_fee_amount,
        from_wallet=factory_deployer_wallet,
    )
    mock_dai_contract.approve(
        spender=erc20_enterprise_token.address,
        amount=web3.toWei(1000, "ether"),
        from_wallet=consumer_wallet,
    )

    order_params = {
        "consumer": consumer_wallet.address,
        "amount": web3.toWei(1, "ether"),
        "serviceId": 1,
        "consumeFeeAddress": consume_fee_address,
        "consumeFeeToken": mock_dai_contract.address,
        "consumeFeeAmount": consume_fee_amount,
    }

    fre_params = {
        "exchangeContract": fixed_rate_exchange.address,
        "exchangeId": exchange_id,
        "maxBaseTokenAmount": web3.toWei(3, "ether"),
    }

    opf_collector_address = get_address_of_type(config, "OPFCommunityFeeCollector")

    balance_consume_before = mock_dai_contract.balanceOf(consume_fee_address)
    balance_opf_consume_before = mock_dai_contract.balanceOf(opf_collector_address)
    balance_publish_before = mock_usdc_contract.balanceOf(publisher_wallet.address)
    balance_opf_publish_before = mock_usdc_contract.balanceOf(opf_collector_address)

    tx = erc20_enterprise_token.buy_from_fre_and_order(
        order_params=order_params,
        fre_params=fre_params,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert tx_receipt["status"] == 1

    balance_consume = mock_dai_contract.balanceOf(consume_fee_address)
    balance_opf_consume = mock_dai_contract.balanceOf(opf_collector_address)

    balance_publish = mock_usdc_contract.balanceOf(publish_fees[0])
    balance_opf_publish = mock_usdc_contract.balanceOf(opf_collector_address)

    expected_consume = consume_fee_amount - consume_fee_amount / 100
    expected_opf_consume = consume_fee_amount / 100

    expected_publish = publish_fees[2] - publish_fees[2] / 100
    expected_opf_publish = publish_fees[2] / 100

    assert balance_consume - balance_consume_before == expected_consume
    assert balance_opf_consume - balance_opf_consume_before == expected_opf_consume

    assert balance_publish - balance_publish_before == expected_publish
    assert balance_opf_publish - balance_opf_publish_before == expected_opf_publish

    assert (
        erc20_enterprise_token.balanceOf(erc20_enterprise_token.get_fee_collector())
        == 0
    )
