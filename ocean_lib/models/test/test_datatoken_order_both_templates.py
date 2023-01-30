#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime

import pytest

from ocean_lib.models.datatoken import Datatoken, TokenFeeInfo
from ocean_lib.models.dispenser import DispenserArguments
from ocean_lib.models.fixed_rate_exchange import ExchangeArguments
from ocean_lib.ocean.util import from_wei, get_address_of_type, to_wei
from ocean_lib.web3_internal.constants import MAX_UINT256
from tests.resources.helper_functions import (
    confirm_failed,
    deploy_erc721_erc20,
    get_mock_provider_fees,
)

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
        {"from": publisher_wallet},
        DispenserArguments(to_wei(1), to_wei(1)),
    )

    status = DT.dispenser_status()

    assert status.active
    assert status.owner_address == publisher_wallet.address
    assert status.is_minter

    # ALLOWED_SWAPPER == ZERO means anyone should be able to request dispense
    # However, ERC20TemplateEnterprise.sol has a quirk where this isn't allowed
    # Below, we test the quirk.
    args = (to_wei(1), {"from": consumer_wallet, "required_confs": 0})
    confirm_failed(DT, "dispense", args, "This address is not allowed to request DT")

    consume_fee_amount = to_wei(2)
    consume_fee_address = consumer_wallet.address
    DT.setPublishingMarketFee(
        consume_fee_address,
        USDC.address,
        consume_fee_amount,
        {"from": publisher_wallet},
    )

    publish_market_fees = DT.get_publish_market_order_fees()

    USDC.transfer(
        publisher_wallet.address,
        publish_market_fees.amount,
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
        consume_market_fees=TokenFeeInfo(
            address=consume_fee_address,
            token=DAI.address,
        ),
        tx_dict={"from": publisher_wallet},
    )

    assert tx
    assert DT.totalSupply() == to_wei(0)

    balance_opf_consume = DAI.balanceOf(opf_collector_address)
    balance_publish = USDC.balanceOf(publish_market_fees.address)

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
        {"from": publisher_wallet},
        DispenserArguments(to_wei(1), to_wei(1)),
    )

    provider_fees = get_mock_provider_fees(
        "MockDAI", publisher_wallet, valid_until=valid_until
    )

    tx = DT.dispense_and_order(
        consumer=consumer_wallet.address,
        service_index=1,
        provider_fees=provider_fees,
        tx_dict={"from": publisher_wallet},
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
        ExchangeArguments(
            rate=to_wei(1),
            base_token_addr=USDC.address,
            publish_market_fee=to_wei(0.1),
            with_mint=True,
        ),
        tx_dict={"from": publisher_wallet},
    )
    assert exchange.details.active
    assert exchange.details.with_mint

    if template_index == 2:
        args = {
            "datatoken_amt": to_wei(1),
            "max_basetoken_amt": to_wei(1),
            "tx_dict": {"from": consumer_wallet, "required_confs": 0},
        }
        confirm_failed(exchange, "buy_DT", args, "This address is not allowed to swap")

    consume_fee_amount = to_wei(2)
    consume_fee_address = consumer_wallet.address
    DT.setPublishingMarketFee(
        consume_fee_address,
        USDC.address,
        consume_fee_amount,
        {"from": publisher_wallet},
    )

    publish_market_fees = DT.get_publish_market_order_fees()

    USDC.transfer(
        publisher_wallet.address,
        publish_market_fees.amount + to_wei(3),
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

    args = {
        "consumer": another_consumer_wallet.address,
        "service_index": 1,
        "provider_fees": provider_fees,
        "consume_market_fees": TokenFeeInfo(
            address=consume_fee_address,
            token=DAI.address,
        ),
        "exchange": exchange,
        "tx_dict": {"from": publisher_wallet},
    }

    if template_index == 2:
        args["max_base_token_amount"] = to_wei(2.5)
        args["consume_market_swap_fee_amount"] = to_wei(0.001)  # 1e15 => 0.1%
        args["consume_market_swap_fee_address"] = another_consumer_wallet.address

    tx = DT.buy_DT_and_order(**args)

    assert tx

    if template_index == 2:
        assert DT.totalSupply() == to_wei(0)

    consume_bal2 = DAI.balanceOf(consume_fee_address)
    publish_bal2 = USDC.balanceOf(publish_market_fees.address)

    assert from_wei(consume_bal2) == from_wei(consume_bal1)

    assert from_wei(publish_bal2) == from_wei(publish_bal1) + 2.0

    if template_index == 2:
        assert from_wei(DT.balanceOf(DT.getPaymentCollector())) == 0
