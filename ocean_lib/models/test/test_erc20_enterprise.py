#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.ddo_helpers import create_basics, get_first_service_by_type
from tests.resources.helper_functions import get_address_of_type


@pytest.mark.unit
def test_buy_from_dispenser_and_order(
    web3,
    config,
    publisher_wallet,
    consumer_wallet,
    factory_deployer_wallet,
    erc721_nft,
    erc20_enterprise_token,
    publisher_ocean_instance,
):
    """Tests buy_from_dispenser_and_order function of the ERC20 Enterprise"""
    mock_usdc_contract = ERC20Token(web3, get_address_of_type(config, "MockUSDC"))
    mock_dai_contract = ERC20Token(web3, get_address_of_type(config, "MockDAI"))
    dispenser = Dispenser(web3, get_address_of_type(config, "Dispenser"))

    tx = erc20_enterprise_token.create_dispenser(
        dispenser_address=dispenser.address,
        allowed_swapper=ZERO_ADDRESS,
        max_balance=to_wei("1"),
        with_mint=True,
        max_tokens=to_wei("1"),
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert tx_receipt.status == 1

    status = dispenser.status(erc20_enterprise_token.address)

    assert status[0] is True
    assert status[1] == publisher_wallet.address
    assert status[2] is True

    with pytest.raises(exceptions.ContractLogicError) as err:
        dispenser.dispense(
            datatoken=erc20_enterprise_token.address,
            amount=to_wei("1"),
            destination=consumer_wallet.address,
            from_wallet=consumer_wallet,
        )

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert This address is not allowed to request DT"
    )

    consume_fee_amount = to_wei("2")
    consume_fee_address = consumer_wallet.address
    erc20_enterprise_token.set_publishing_market_fee(
        publish_market_order_fee_address=consume_fee_address,
        publish_market_order_fee_token=mock_usdc_contract.address,
        publish_market_order_fee_amount=consume_fee_amount,
        from_wallet=publisher_wallet,
    )
    publish_fees = erc20_enterprise_token.get_publishing_market_fee()

    mock_usdc_contract.transfer(
        to=publisher_wallet.address,
        amount=publish_fees[2],
        from_wallet=factory_deployer_wallet,
    )

    mock_usdc_contract.approve(
        spender=erc20_enterprise_token.address,
        amount=consume_fee_amount,
        from_wallet=publisher_wallet,
    )

    mock_dai_contract.transfer(
        to=publisher_wallet.address,
        amount=consume_fee_amount,
        from_wallet=factory_deployer_wallet,
    )

    mock_dai_contract.approve(
        spender=erc20_enterprise_token.address,
        amount=consume_fee_amount,
        from_wallet=publisher_wallet,
    )

    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)
    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_nft.address,
        deployed_erc20_tokens=[erc20_enterprise_token],
    )
    access_service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)

    initialize_response = data_provider.initialize(
        ddo.did, access_service, consumer_address=publisher_wallet.address
    )
    initialize_data = initialize_response.json()
    provider_fees = initialize_data["providerFee"]

    opf_collector_address = get_address_of_type(config, "OPFCommunityFeeCollector")

    balance_opf_consume_before = mock_dai_contract.balanceOf(opf_collector_address)
    balance_publish_before = mock_usdc_contract.balanceOf(consumer_wallet.address)

    tx = erc20_enterprise_token.buy_from_dispenser_and_order(
        consumer=consume_fee_address,
        service_index=1,
        provider_fee_address=provider_fees["providerFeeAddress"],
        provider_fee_token=provider_fees["providerFeeToken"],
        provider_fee_amount=provider_fees["providerFeeAmount"],
        v=provider_fees["v"],
        r=provider_fees["r"],
        s=provider_fees["s"],
        valid_until=provider_fees["validUntil"],
        provider_data=provider_fees["providerData"],
        consume_market_order_fee_address=consume_fee_address,
        consume_market_order_fee_token=mock_dai_contract.address,
        consume_market_order_fee_amount=0,
        dispenser_address=dispenser.address,
        from_wallet=publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert tx_receipt.status == 1
    assert erc20_enterprise_token.get_total_supply() == to_wei("0")

    balance_opf_consume = mock_dai_contract.balanceOf(opf_collector_address)
    balance_publish = mock_usdc_contract.balanceOf(publish_fees[0])

    assert balance_opf_consume - balance_opf_consume_before == 0
    assert balance_publish - balance_publish_before == to_wei("2")

    assert (
        erc20_enterprise_token.balanceOf(erc20_enterprise_token.get_payment_collector())
        == 0
    )


@pytest.mark.unit
def test_buy_from_fre_and_order(
    web3,
    config,
    publisher_wallet,
    consumer_wallet,
    factory_deployer_wallet,
    another_consumer_wallet,
    erc721_nft,
    erc20_enterprise_token,
    publisher_ocean_instance,
):
    """Tests buy_from_fre_and_order function of the ERC20 Enterprise"""
    mock_usdc_contract = ERC20Token(web3, get_address_of_type(config, "MockUSDC"))
    mock_dai_contract = ERC20Token(web3, get_address_of_type(config, "MockDAI"))
    fixed_rate_exchange = FixedRateExchange(
        web3, get_address_of_type(config, "FixedPrice")
    )

    tx = erc20_enterprise_token.create_fixed_rate(
        fixed_price_address=fixed_rate_exchange.address,
        base_token_address=mock_usdc_contract.address,
        owner=publisher_wallet.address,
        publish_market_swap_fee_collector=publisher_wallet.address,
        allowed_swapper=ZERO_ADDRESS,
        base_token_decimals=18,
        datatoken_decimals=18,
        fixed_rate=to_wei(1),
        publish_market_swap_fee_amount=to_wei("0.1"),
        with_mint=1,
        from_wallet=publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert tx_receipt.status == 1

    new_fixed_rate_event = erc20_enterprise_token.get_event_log(
        "NewFixedRate",
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    exchange_id = new_fixed_rate_event[0].args.exchangeId
    status = fixed_rate_exchange.get_exchange(exchange_id)

    assert status[6] is True  # is active
    assert status[11] is True  # is minter

    with pytest.raises(exceptions.ContractLogicError) as err:
        fixed_rate_exchange.buy_dt(
            exchange_id=exchange_id,
            datatoken_amount=to_wei("1"),
            max_base_token_amount=to_wei("1"),
            consume_market_swap_fee_address=ZERO_ADDRESS,
            consume_market_swap_fee_amount=0,
            from_wallet=consumer_wallet,
        )

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert FixedRateExchange: This address is not allowed to swap"
    )

    consume_fee_amount = to_wei("2")
    consume_fee_address = consumer_wallet.address
    erc20_enterprise_token.set_publishing_market_fee(
        publish_market_order_fee_address=consume_fee_address,
        publish_market_order_fee_token=mock_usdc_contract.address,
        publish_market_order_fee_amount=consume_fee_amount,
        from_wallet=publisher_wallet,
    )
    publish_fees = erc20_enterprise_token.get_publishing_market_fee()

    mock_usdc_contract.transfer(
        to=publisher_wallet.address,
        amount=publish_fees[2] + to_wei("3"),
        from_wallet=factory_deployer_wallet,
    )
    mock_usdc_contract.approve(
        spender=erc20_enterprise_token.address,
        amount=2**256 - 1,
        from_wallet=publisher_wallet,
    )
    mock_dai_contract.transfer(
        to=publisher_wallet.address,
        amount=consume_fee_amount,
        from_wallet=factory_deployer_wallet,
    )
    mock_dai_contract.approve(
        spender=erc20_enterprise_token.address,
        amount=consume_fee_amount,
        from_wallet=publisher_wallet,
    )
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)
    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_nft.address,
        deployed_erc20_tokens=[erc20_enterprise_token],
    )
    access_service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)

    initialize_response = data_provider.initialize(
        ddo.did, access_service, consumer_address=publisher_wallet.address
    )
    initialize_data = initialize_response.json()
    provider_fees = initialize_data["providerFee"]

    balance_consume_before = mock_dai_contract.balanceOf(consume_fee_address)
    balance_publish_before = mock_usdc_contract.balanceOf(consumer_wallet.address)
    provider_fee_balance_before = mock_usdc_contract.balanceOf(
        another_consumer_wallet.address
    )

    tx = erc20_enterprise_token.buy_from_fre_and_order(
        consumer=another_consumer_wallet.address,
        service_index=1,
        provider_fee_address=provider_fees["providerFeeAddress"],
        provider_fee_token=provider_fees["providerFeeToken"],
        provider_fee_amount=provider_fees["providerFeeAmount"],
        v=provider_fees["v"],
        r=provider_fees["r"],
        s=provider_fees["s"],
        valid_until=provider_fees["validUntil"],
        provider_data=provider_fees["providerData"],
        consume_market_order_fee_address=consume_fee_address,
        consume_market_order_fee_token=mock_dai_contract.address,
        consume_market_order_fee_amount=0,
        exchange_contract=fixed_rate_exchange.address,
        exchange_id=exchange_id,
        max_base_token_amount=to_wei("2.5"),
        consume_market_swap_fee_amount=to_wei("0.001"),  # 1e15 => 0.1%
        consume_market_swap_fee_address=another_consumer_wallet.address,
        from_wallet=publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert tx_receipt.status == 1
    assert erc20_enterprise_token.get_total_supply() == to_wei("0")

    provider_fee_balance_after = mock_usdc_contract.balanceOf(
        another_consumer_wallet.address
    )
    balance_consume = mock_dai_contract.balanceOf(consume_fee_address)
    balance_publish = mock_usdc_contract.balanceOf(publish_fees[0])

    assert balance_consume - balance_consume_before == 0
    assert provider_fee_balance_after - provider_fee_balance_before == to_wei("0.001")

    assert balance_publish - balance_publish_before == to_wei("2")

    assert (
        erc20_enterprise_token.balanceOf(erc20_enterprise_token.get_payment_collector())
        == 0
    )
