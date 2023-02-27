#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime, timedelta
from time import sleep

import pytest

from ocean_lib.models.datatoken_base import DatatokenBase, TokenFeeInfo
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.ocean.util import get_address_of_type, to_wei
from ocean_lib.structures.file_objects import FilesType
from ocean_lib.web3_internal.constants import MAX_UINT256
from tests.flows.test_start_order_fees import create_asset_with_order_fee_and_timeout
from tests.resources.helper_functions import (
    deploy_erc721_erc20,
    get_provider_fees,
    get_wallet,
    int_units,
    transfer_bt_if_balance_lte,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "base_token_name, provider_fee_in_unit",
    [
        # Small fees
        ("Ocean", "7"),
        ("MockDAI", "7"),
        ("MockUSDC", "7"),
        # Zero fees
        ("Ocean", "0"),
        ("MockUSDC", "0"),
        # Min fees
        ("Ocean", "0.000000000000000001"),  # Smallest OCEAN amount
        ("MockUSDC", "0.000001"),  # Smallest USDC amount
        # Large fees
        ("Ocean", "700"),
        ("MockUSDC", "700"),
    ],
)
def test_reuse_order_fees(
    config: dict,
    publisher_wallet,
    consumer_wallet,
    provider_wallet,
    factory_deployer_wallet,
    file1: FilesType,
    base_token_name: str,
    provider_fee_in_unit: str,
):
    bt = DatatokenBase.get_typed(config, get_address_of_type(config, base_token_name))
    data_nft = deploy_erc721_erc20(config, publisher_wallet)
    publish_market_wallet = get_wallet(4)
    consume_market_wallet = get_wallet(5)

    # Send base tokens to the consumer so they can pay for fees
    transfer_bt_if_balance_lte(
        config=config,
        bt_address=bt.address,
        from_wallet=factory_deployer_wallet,
        recipient=consumer_wallet.address,
        min_balance=int_units("4000", bt.decimals()),
        amount_to_transfer=int_units("4000", bt.decimals()),
    )

    # Publish ddo, service, and datatoken. Orders expire after 5 seconds
    ddo, service, dt = create_asset_with_order_fee_and_timeout(
        config=config,
        file=file1,
        data_nft=data_nft,
        publisher_wallet=publisher_wallet,
        publish_market_order_fees=TokenFeeInfo(
            address=publish_market_wallet.address,
            token=bt.address,
            amount=int_units("10", bt.decimals()),
        ),
        timeout=5,
    )

    # Mint 50 datatokens in consumer wallet from publisher.
    dt.mint(
        consumer_wallet.address,
        to_wei(50),
        {"from": publisher_wallet},
    )

    # Mock non-zero provider fees (simulate first time paying provider fees)
    provider_fee = int_units(provider_fee_in_unit, bt.decimals())
    valid_until = int((datetime.utcnow() + timedelta(seconds=10)).timestamp())
    provider_fees = get_provider_fees(
        provider_wallet,
        bt.address,
        provider_fee,
        valid_until,
    )

    # Grant datatoken infinite approval to spend consumer's base tokens
    bt.approve(dt.address, MAX_UINT256, {"from": consumer_wallet})

    if base_token_name == "Ocean" and provider_fee_in_unit == "700":
        bt.mint(
            consumer_wallet.address,
            int_units("2000", bt.decimals()),
            {"from": factory_deployer_wallet},
        )

    # Start order: pay order fees and provider fees
    start_order_receipt = dt.start_order(
        consumer=consumer_wallet.address,
        service_index=ddo.get_index_of_service(service),
        provider_fees=provider_fees,
        consume_market_fees=TokenFeeInfo(
            address=consume_market_wallet.address,
            token=bt.address,
            amount=int_units("10", bt.decimals()),
        ),
        tx_dict={"from": consumer_wallet},
    )

    # Reuse order where:
    #     Order: valid
    #     Provider fees: valid
    # Simulate valid provider fees by setting them to 0
    reuse_order_with_mock_provider_fees(
        provider_fee_in_unit="0",
        start_order_tx_id=start_order_receipt.txid,
        bt=bt,
        dt=dt,
        publisher_wallet=publisher_wallet,
        publish_market_wallet=publish_market_wallet,
        consume_market_wallet=consume_market_wallet,
        consumer_wallet=consumer_wallet,
        provider_wallet=provider_wallet,
    )

    # Reuse order where:
    #     Order: valid
    #     Provider fees: expired
    # Simulate expired provider fees by setting them to non-zero
    reuse_order_with_mock_provider_fees(
        provider_fee_in_unit=provider_fee_in_unit,
        start_order_tx_id=start_order_receipt.txid,
        bt=bt,
        dt=dt,
        publisher_wallet=publisher_wallet,
        publish_market_wallet=publish_market_wallet,
        consume_market_wallet=consume_market_wallet,
        consumer_wallet=consumer_wallet,
        provider_wallet=provider_wallet,
    )

    # Sleep for 6 seconds, long enough for order to expire
    sleep(6)

    # Reuse order where:
    #     Order: expired
    #     Provider fees: valid
    # Simulate valid provider fees by setting them to 0
    reuse_order_with_mock_provider_fees(
        provider_fee_in_unit="0",
        start_order_tx_id=start_order_receipt.txid,
        bt=bt,
        dt=dt,
        publisher_wallet=publisher_wallet,
        publish_market_wallet=publish_market_wallet,
        consume_market_wallet=consume_market_wallet,
        consumer_wallet=consumer_wallet,
        provider_wallet=provider_wallet,
    )

    # Reuse order where:
    #     Order: expired
    #     Provider fees: expired
    # Simulate expired provider fees by setting them to non-zero
    reuse_order_with_mock_provider_fees(
        provider_fee_in_unit=provider_fee_in_unit,
        start_order_tx_id=start_order_receipt.txid,
        bt=bt,
        dt=dt,
        publisher_wallet=publisher_wallet,
        publish_market_wallet=publish_market_wallet,
        consume_market_wallet=consume_market_wallet,
        consumer_wallet=consumer_wallet,
        provider_wallet=provider_wallet,
    )


def reuse_order_with_mock_provider_fees(
    provider_fee_in_unit: str,
    start_order_tx_id: str,
    bt: DatatokenBase,
    dt: DatatokenBase,
    publisher_wallet,
    publish_market_wallet,
    consume_market_wallet,
    consumer_wallet,
    provider_wallet,
):
    """Call reuse_order, and verify the balances/fees are correct"""

    router = FactoryRouter(bt.config_dict, dt.router())
    opc_collector_address = router.getOPCCollector()

    # Get balances before reuse_order
    publisher_bt_balance_before = bt.balanceOf(publisher_wallet.address)
    publisher_dt_balance_before = dt.balanceOf(publisher_wallet.address)
    publish_market_bt_balance_before = bt.balanceOf(publish_market_wallet.address)
    publish_market_dt_balance_before = dt.balanceOf(publish_market_wallet.address)
    consume_market_bt_balance_before = bt.balanceOf(consume_market_wallet.address)
    consume_market_dt_balance_before = dt.balanceOf(consume_market_wallet.address)
    consumer_bt_balance_before = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance_before = dt.balanceOf(consumer_wallet.address)
    provider_bt_balance_before = bt.balanceOf(provider_wallet.address)
    provider_dt_balance_before = dt.balanceOf(provider_wallet.address)
    opc_bt_balance_before = bt.balanceOf(opc_collector_address)
    opc_dt_balance_before = dt.balanceOf(opc_collector_address)

    # Mock provider fees
    provider_fee = int_units(provider_fee_in_unit, bt.decimals())
    valid_until = int((datetime.utcnow() + timedelta(seconds=10)).timestamp())
    provider_fees = get_provider_fees(
        provider_wallet,
        bt.address,
        provider_fee,
        valid_until,
    )

    # Reuse order
    dt.reuse_order(
        order_tx_id=start_order_tx_id,
        provider_fees=provider_fees,
        tx_dict={"from": consumer_wallet},
    )

    # Get balances after reuse_order
    publisher_bt_balance_after = bt.balanceOf(publisher_wallet.address)
    publisher_dt_balance_after = dt.balanceOf(publisher_wallet.address)
    publish_market_bt_balance_after = bt.balanceOf(publish_market_wallet.address)
    publish_market_dt_balance_after = dt.balanceOf(publish_market_wallet.address)
    consume_market_bt_balance_after = bt.balanceOf(consume_market_wallet.address)
    consume_market_dt_balance_after = dt.balanceOf(consume_market_wallet.address)
    consumer_bt_balance_after = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance_after = dt.balanceOf(consumer_wallet.address)
    provider_bt_balance_after = bt.balanceOf(provider_wallet.address)
    provider_dt_balance_after = dt.balanceOf(provider_wallet.address)
    opc_bt_balance_after = bt.balanceOf(opc_collector_address)
    opc_dt_balance_after = dt.balanceOf(opc_collector_address)

    # Check balances
    assert publisher_bt_balance_before == publisher_bt_balance_after
    assert publisher_dt_balance_before == publisher_dt_balance_after
    assert publish_market_bt_balance_before == publish_market_bt_balance_after
    assert publish_market_dt_balance_before == publish_market_dt_balance_after
    assert consume_market_bt_balance_before == consume_market_bt_balance_after
    assert consume_market_dt_balance_before == consume_market_dt_balance_after
    assert consumer_bt_balance_before - provider_fee == consumer_bt_balance_after
    assert consumer_dt_balance_before == consumer_dt_balance_after
    assert provider_bt_balance_before + provider_fee == provider_bt_balance_after
    assert provider_dt_balance_before == provider_dt_balance_after
    assert opc_bt_balance_before == opc_bt_balance_after
    assert opc_dt_balance_before == opc_dt_balance_after
