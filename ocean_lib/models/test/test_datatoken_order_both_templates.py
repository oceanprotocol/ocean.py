#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime

import pytest

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.util import from_wei, get_address_of_type, to_wei
from ocean_lib.web3_internal.constants import MAX_UINT256
from tests.resources.helper_functions import deploy_erc721_erc20, get_mock_provider_fees

from ocean_lib.models.arguments import FeeTokenArguments  # isort:skip

valid_until = int(datetime(2032, 12, 31).timestamp())


@pytest.mark.unit
def test_dispense_and_order_with_non_defaults(
    config,
    publisher_wallet,
    consumer_wallet,
    factory_deployer_wallet,
):
    """Tests dispense_and_order function of the Datatoken Enterprise"""
    _, DT = deploy_erc721_erc20(config, publisher_wallet, publisher_wallet, 2)

    USDC = Datatoken(config, get_address_of_type(config, "MockUSDC"))
    DAI = Datatoken(config, get_address_of_type(config, "MockDAI"))

    _ = DT.create_dispenser(
        max_tokens=to_wei(1),
        max_balance=to_wei(1),
        tx_dict={"from": publisher_wallet},
    )

    status = DT.dispenser_status()

    assert status.active
    assert status.owner_address == publisher_wallet.address
    assert status.is_minter

    # ALLOWED_SWAPPER == ZERO means anyone should be able to request dispense
    # However, ERC20TemplateEnterprise.sol has a quirk where this isn't allowed
    # Below, we test the quirk.
    match_s = "This address is not allowed to request DT"
    with pytest.raises(Exception, match=match_s):
        DT.dispense(to_wei(1), {"from": consumer_wallet})

    consume_fee_amount = to_wei(2)
    consume_fee_address = consumer_wallet.address
    DT.setPublishingMarketFee(
        consume_fee_address,
        USDC.address,
        consume_fee_amount,
        {"from": publisher_wallet},
    )

    (publishMarketFeeAddress, _, publishMarketFeeAmount) = DT.getPublishingMarketFee()

    USDC.transfer(
        publisher_wallet.address,
        publishMarketFeeAmount,
        {"from": factory_deployer_wallet},
    )

    USDC.approve(
        DT.address,
        consume_fee_amount,
        {"from": publisher_wallet},
    )

    DAI.transfer(
        publisher_wallet.address,
        consume_fee_amount,
        {"from": factory_deployer_wallet},
    )

    DAI.approve(
        DT.address,
        consume_fee_amount,
        {"from": publisher_wallet},
    )

    provider_fees = get_mock_provider_fees(
        "MockDAI", publisher_wallet, valid_until=valid_until
    )

    opf_collector_address = get_address_of_type(config, "OPFCommunityFeeCollector")

    balance_opf_consume_before = DAI.balanceOf(opf_collector_address)
    publish_bal_before = USDC.balanceOf(consumer_wallet.address)

    tx = DT.dispense_and_order(
        consumer=consume_fee_address,
        service_index=1,
        provider_fees=provider_fees,
        consume_market_fees=FeeTokenArguments(
            address=consume_fee_address,
            token=DAI.address,
        ),
        transaction_parameters={"from": publisher_wallet},
    )

    assert tx
    assert DT.totalSupply() == to_wei(0)

    balance_opf_consume = DAI.balanceOf(opf_collector_address)
    balance_publish = USDC.balanceOf(publishMarketFeeAddress)

    assert balance_opf_consume - balance_opf_consume_before == 0
    assert balance_publish - publish_bal_before == to_wei(2)

    assert DT.balanceOf(DT.getPaymentCollector()) == 0


@pytest.mark.unit
@pytest.mark.parametrize("template_index", [1, 2])
def test_dispense_and_order_with_defaults(
    config, publisher_wallet, consumer_wallet, factory_deployer_wallet, template_index
):
    """Tests dispense_and_order function of the Datatoken and DatatokenEnterprise"""
    _, DT = deploy_erc721_erc20(
        config, publisher_wallet, publisher_wallet, template_index
    )

    _ = DT.create_dispenser(
        max_tokens=to_wei(1),
        max_balance=to_wei(1),
        tx_dict={"from": publisher_wallet},
    )

    provider_fees = get_mock_provider_fees(
        "MockDAI", publisher_wallet, valid_until=valid_until
    )

    tx = DT.dispense_and_order(
        consumer=consumer_wallet.address,
        service_index=1,
        provider_fees=provider_fees,
        transaction_parameters={"from": publisher_wallet},
    )

    assert tx
    assert DT.totalSupply() == (to_wei(0) if template_index == 2 else to_wei(1))


@pytest.mark.unit
@pytest.mark.parametrize("template_index", [1, 2])
def test_buy_DT_and_order(
    config,
    publisher_wallet,
    consumer_wallet,
    factory_deployer_wallet,
    another_consumer_wallet,
    template_index,
):
    """Tests buy_DT_and_order function of the Datatoken and DatatokenEnterprise"""
    _, DT = deploy_erc721_erc20(
        config, publisher_wallet, publisher_wallet, template_index
    )

    USDC = Datatoken(config, get_address_of_type(config, "MockUSDC"))
    DAI = Datatoken(config, get_address_of_type(config, "MockDAI"))

    exchange = DT.create_exchange(
        rate=to_wei(1),
        base_token_addr=USDC.address,
        tx_dict={"from": publisher_wallet},
        publish_market_fee=to_wei(0.1),
        with_mint=True,
    )
    assert exchange.details.active
    assert exchange.details.with_mint

    if template_index == 2:
        with pytest.raises(Exception, match="This address is not allowed to swap"):
            exchange.buy_DT(
                datatoken_amt=to_wei(1),
                max_basetoken_amt=to_wei(1),
                tx_dict={"from": consumer_wallet},
            )

    consume_fee_amount = to_wei(2)
    consume_fee_address = consumer_wallet.address
    DT.setPublishingMarketFee(
        consume_fee_address,
        USDC.address,
        consume_fee_amount,
        {"from": publisher_wallet},
    )

    (publishMarketFeeAddress, _, publishMarketFeeAmount) = DT.getPublishingMarketFee()

    USDC.transfer(
        publisher_wallet.address,
        publishMarketFeeAmount + to_wei(3),
        {"from": factory_deployer_wallet},
    )
    USDC.approve(
        DT.address,
        MAX_UINT256,
        {"from": publisher_wallet},
    )
    USDC.approve(
        exchange.address,
        MAX_UINT256,
        {"from": publisher_wallet},
    )
    DAI.transfer(
        publisher_wallet.address,
        consume_fee_amount,
        {"from": factory_deployer_wallet},
    )
    DAI.approve(DT.address, consume_fee_amount, {"from": publisher_wallet})

    provider_fees = get_mock_provider_fees(
        "MockDAI", publisher_wallet, valid_until=valid_until
    )

    consume_bal1 = DAI.balanceOf(consume_fee_address)
    publish_bal1 = USDC.balanceOf(consumer_wallet.address)
    provider_fee_bal1 = USDC.balanceOf(another_consumer_wallet.address)

    tx = DT.buy_DT_and_order(
        consumer=another_consumer_wallet.address,
        service_index=1,
        provider_fees=provider_fees,
        consume_market_order_fee_address=consume_fee_address,
        consume_market_order_fee_token=DAI.address,
        consume_market_order_fee_amount=0,
        exchange=exchange,
        max_base_token_amount=to_wei(2.5),
        consume_market_swap_fee_amount=to_wei(0.001),  # 1e15 => 0.1%
        consume_market_swap_fee_address=another_consumer_wallet.address,
        transaction_parameters={"from": publisher_wallet},
    )

    assert tx

    if template_index == 2:
        assert DT.totalSupply() == to_wei(0)

    provider_fee_bal2 = USDC.balanceOf(another_consumer_wallet.address)
    consume_bal2 = DAI.balanceOf(consume_fee_address)
    publish_bal2 = USDC.balanceOf(publishMarketFeeAddress)

    assert from_wei(consume_bal2) == from_wei(consume_bal1)

    assert from_wei(publish_bal2) == from_wei(publish_bal1) + 2.0

    if template_index == 2:
        assert from_wei(DT.balanceOf(DT.getPaymentCollector())) == 0
