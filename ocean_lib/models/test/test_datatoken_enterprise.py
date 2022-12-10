#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json

import pytest
from brownie import network
from web3.main import Web3

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.ocean.util import get_address_of_type, to_wei, from_wei
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from ocean_lib.web3_internal.utils import split_signature
from tests.resources.helper_functions import deploy_erc721_erc20


@pytest.mark.unit
def test_buy_from_dispenser_and_order(
    config,
    publisher_wallet,
    consumer_wallet,
    factory_deployer_wallet,
):
    """Tests buy_from_dispenser_and_order function of the Datatoken Enterprise"""
    _, DT = deploy_erc721_erc20(config, publisher_wallet, publisher_wallet, 2)

    USDC = Datatoken(config, get_address_of_type(config, "MockUSDC"))
    DAI = Datatoken(config, get_address_of_type(config, "MockDAI"))
    FRE_addr = get_address_of_type(config, "Dispenser")

    _ = DT.createDispenser(
        FRE_addr,
        to_wei(1),  # max_tokens
        to_wei(1),  # max_balance
        True,  # with_mint
        ZERO_ADDRESS,  # allowed_swapper
        {"from": publisher_wallet},
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

    provider_fee_address = publisher_wallet.address
    provider_fee_token = DAI.address
    provider_fee_amount = 0
    provider_data = json.dumps({"timeout": 0}, separators=(",", ":"))
    valid_until = 1958133628  # 2032

    message = Web3.solidityKeccak(
        ["bytes", "address", "address", "uint256", "uint256"],
        [
            Web3.toHex(Web3.toBytes(text=provider_data)),
            provider_fee_address,
            provider_fee_token,
            provider_fee_amount,
            valid_until,
        ],
    )
    signed = network.web3.eth.sign(provider_fee_address, data=message)
    signature = split_signature(signed)

    opf_collector_address = get_address_of_type(config, "OPFCommunityFeeCollector")

    balance_opf_consume_before = DAI.balanceOf(opf_collector_address)
    publish_bal_before = USDC.balanceOf(consumer_wallet.address)

    _ = DT.buy_from_dispenser_and_order(
        consumer=consume_fee_address,
        service_index=1,
        provider_fee_address=provider_fee_address,
        provider_fee_token=provider_fee_token,
        provider_fee_amount=provider_fee_amount,
        v=signature.v,
        r=signature.r,
        s=signature.s,
        valid_until=valid_until,
        provider_data=Web3.toHex(Web3.toBytes(text=provider_data)),
        consume_market_order_fee_address=consume_fee_address,
        consume_market_order_fee_token=DAI.address,
        consume_market_order_fee_amount=0,
        dispenser_address=FRE_addr,
        transaction_parameters={"from": publisher_wallet},
    )

    assert DT.totalSupply() == to_wei(0)

    balance_opf_consume = DAI.balanceOf(opf_collector_address)
    balance_publish = USDC.balanceOf(publishMarketFeeAddress)

    assert balance_opf_consume - balance_opf_consume_before == 0
    assert balance_publish - publish_bal_before == to_wei(2)

    assert DT.balanceOf(DT.getPaymentCollector()) == 0


@pytest.mark.unit
def test_buy_from_fre_and_order(
    config,
    publisher_wallet,
    consumer_wallet,
    factory_deployer_wallet,
    another_consumer_wallet,
):
    """Tests buy_from_fre_and_order function of the Datatoken Enterprise"""
    _, DT = deploy_erc721_erc20(config, publisher_wallet, publisher_wallet, 2)

    USDC = Datatoken(config, get_address_of_type(config, "MockUSDC"))
    DAI = Datatoken(config, get_address_of_type(config, "MockDAI"))
    FRE_addr = get_address_of_type(config, "FixedPrice")
    
    from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
    FRE = FixedRateExchange(config, FRE_addr)

    # HACK start========================================================
    (exchange, tx_receipt) = DT.create_exchange(
        rate = to_wei(1),
        base_token_addr = USDC.address,
        tx_dict = {"from": publisher_wallet},
        owner_addr = publisher_wallet.address,
        publish_market_fee_collector = publisher_wallet.address,
        publish_market_fee = to_wei(0.1),
        with_mint = True,
        allowed_swapper = ZERO_ADDRESS,
    )

    # HACK END==============================================================

    new_fixed_rate_event = tx_receipt.events["NewFixedRate"]
    exchange_id = new_fixed_rate_event["exchangeId"]
    
    assert exchange.details.active
    assert exchange.details.with_mint

    with pytest.raises(Exception,match="This address is not allowed to swap"):
        exchange.buy_DT(
            datatoken_amt = to_wei(1),
            max_basetoken_amt = to_wei(1),
            tx_dict = {"from": consumer_wallet},
        )

    consume_fee_amount = to_wei(2)
    consume_fee_address = consumer_wallet.address
    DT.setPublishingMarketFee(
        consume_fee_address,
        USDC.address,
        consume_fee_amount,
        {"from": publisher_wallet},
    )

    # HACK start
    # (publishMarketFeeAddress, _, publishMarketFeeAmount) = \
    #    DT.getPublishingMarketFee()
    publish_fees = DT.getPublishingMarketFee()
    # HACK end

    USDC.transfer(
        publisher_wallet.address,
        # publishMarketFeeAmount + to_wei(3), #HACK
        publish_fees[2] + to_wei(3),  # HACK
        {"from": factory_deployer_wallet},
    )
    USDC.approve(
        DT.address,
        MAX_UINT256,
        {"from": publisher_wallet},
    )
    DAI.transfer(
        publisher_wallet.address,
        consume_fee_amount,
        {"from": factory_deployer_wallet},
    )
    DAI.approve(DT.address, consume_fee_amount, {"from": publisher_wallet})

    provider_fee_address = publisher_wallet.address
    provider_fee_token = DAI.address
    provider_fee_amount = 0
    provider_data = json.dumps({"timeout": 0}, separators=(",", ":"))
    valid_until = 1958133628  # 2032

    message = Web3.solidityKeccak(
        ["bytes", "address", "address", "uint256", "uint256"],
        [
            Web3.toHex(Web3.toBytes(text=provider_data)),
            provider_fee_address,
            provider_fee_token,
            provider_fee_amount,
            valid_until,
        ],
    )
    signed = network.web3.eth.sign(provider_fee_address, data=message)
    signature = split_signature(signed)

    consume_bal1 = DAI.balanceOf(consume_fee_address)
    publish_bal1 = USDC.balanceOf(consumer_wallet.address)
    provider_fee_bal1 = USDC.balanceOf(another_consumer_wallet.address)

    _ = DT.buy_from_fre_and_order(
        consumer=another_consumer_wallet.address,
        service_index=1,
        provider_fee_address=publisher_wallet.address,
        provider_fee_token=provider_fee_token,
        provider_fee_amount=provider_fee_amount,
        v=signature.v,
        r=signature.r,
        s=signature.s,
        valid_until=valid_until,
        provider_data=Web3.toHex(Web3.toBytes(text=provider_data)),
        consume_market_order_fee_address=consume_fee_address,
        consume_market_order_fee_token=DAI.address,
        consume_market_order_fee_amount=0,
        #exchange_contract=exchange.address, #HACK1
        exchange_contract=FRE.address, #HACK1
        # exchange_id=exchange.exchange_id, #HACK2
        exchange_id=exchange_id,  # HACK2
        max_base_token_amount=to_wei(2.5),
        consume_market_swap_fee_amount=to_wei(0.001),  # 1e15 => 0.1%
        consume_market_swap_fee_address=another_consumer_wallet.address,
        transaction_parameters={"from": publisher_wallet},
    )

    assert DT.totalSupply() == to_wei(0)

    provider_fee_bal2 = USDC.balanceOf(another_consumer_wallet.address)
    consume_bal2 = DAI.balanceOf(consume_fee_address)
    # publish_bal2 = USDC.balanceOf(publishMarketFeeAddress) #HACK
    publish_bal2 = USDC.balanceOf(publish_fees[0])  # HACK

    assert from_wei(consume_bal2) == from_wei(consume_bal1)
    assert from_wei(provider_fee_bal2) == from_wei(provider_fee_bal1) + 0.001

    assert from_wei(publish_bal2) == from_wei(publish_bal1) + 2.0

    assert from_wei(DT.balanceOf(DT.getPaymentCollector())) == 0
