#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime, timedelta
from time import sleep

import pytest
from web3 import Web3

from ocean_lib.config import Config
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.structures.file_objects import FilesType
from ocean_lib.web3_internal.currency import MAX_WEI, parse_units, to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.flows.test_start_order_fees import create_asset_with_order_fee_and_timeout
from tests.resources.ddo_helpers import get_opc_collector_address_from_datatoken
from tests.resources.helper_functions import (
    get_address_of_type,
    get_provider_fees,
    transfer_base_token_if_balance_lte,
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
    web3: Web3,
    config: Config,
    publisher_wallet: Wallet,
    consumer_wallet: Wallet,
    provider_wallet: Wallet,
    factory_deployer_wallet: Wallet,
    publish_market_wallet: Wallet,
    consume_market_wallet: Wallet,
    data_nft: DataNFT,
    file1: FilesType,
    base_token_name: str,
    provider_fee_in_unit: str,
):
    bt = Datatoken(web3, get_address_of_type(config, base_token_name))

    # Send base tokens to the consumer so they can pay for fees
    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=factory_deployer_wallet,
        recipient=consumer_wallet.address,
        min_balance=parse_units("4000", bt.decimals()),
        amount_to_transfer=parse_units("4000", bt.decimals()),
    )

    # Publish asset, service, and datatoken. Orders expire after 5 seconds
    asset, service, dt = create_asset_with_order_fee_and_timeout(
        web3=web3,
        config=config,
        file=file1,
        data_nft=data_nft,
        publisher_wallet=publisher_wallet,
        publish_market_order_fee_address=publish_market_wallet.address,
        publish_market_order_fee_token=bt.address,
        publish_market_order_fee_amount=parse_units("10", bt.decimals()),
        timeout=5,
    )

    # Mint 50 datatokens in consumer wallet from publisher.
    dt.mint(
        account_address=consumer_wallet.address,
        value=to_wei("50"),
        from_wallet=publisher_wallet,
    )

    # Mock non-zero provider fees (simulate first time paying provider fees)
    provider_fee = parse_units(provider_fee_in_unit, bt.decimals())
    valid_until = int((datetime.utcnow() + timedelta(seconds=10)).timestamp())
    provider_fees = get_provider_fees(
        web3,
        provider_wallet,
        bt.address,
        provider_fee,
        valid_until,
    )

    # Grant datatoken infinite approval to spend consumer's base tokens
    bt.approve(dt.address, MAX_WEI, consumer_wallet)

    # Start order: pay order fees and provider fees
    start_order_tx_id = dt.start_order(
        consumer=consumer_wallet.address,
        service_index=asset.get_index_of_service(service),
        provider_fee_address=provider_fees["providerFeeAddress"],
        provider_fee_token=provider_fees["providerFeeToken"],
        provider_fee_amount=provider_fees["providerFeeAmount"],
        v=provider_fees["v"],
        r=provider_fees["r"],
        s=provider_fees["s"],
        valid_until=provider_fees["validUntil"],
        provider_data=provider_fees["providerData"],
        consume_market_order_fee_address=consume_market_wallet.address,
        consume_market_order_fee_token=bt.address,
        consume_market_order_fee_amount=parse_units("10", bt.decimals()),
        from_wallet=consumer_wallet,
    )

    # Reuse order where:
    #     Order: valid
    #     Provider fees: valid
    # Simulate valid provider fees by setting them to 0
    reuse_order_with_mock_provider_fees(
        provider_fee_in_unit="0",
        start_order_tx_id=start_order_tx_id,
        bt=bt,
        dt=dt,
        publisher_wallet=publisher_wallet,
        publish_market_wallet=publish_market_wallet,
        consume_market_wallet=consume_market_wallet,
        consumer_wallet=consumer_wallet,
        provider_wallet=provider_wallet,
        web3=web3,
    )

    # Reuse order where:
    #     Order: valid
    #     Provider fees: expired
    # Simulate expired provider fees by setting them to non-zero
    reuse_order_with_mock_provider_fees(
        provider_fee_in_unit=provider_fee_in_unit,
        start_order_tx_id=start_order_tx_id,
        bt=bt,
        dt=dt,
        publisher_wallet=publisher_wallet,
        publish_market_wallet=publish_market_wallet,
        consume_market_wallet=consume_market_wallet,
        consumer_wallet=consumer_wallet,
        provider_wallet=provider_wallet,
        web3=web3,
    )

    # Sleep for 6 seconds, long enough for order to expire
    sleep(6)

    # Reuse order where:
    #     Order: expired
    #     Provider fees: valid
    # Simulate valid provider fees by setting them to 0
    reuse_order_with_mock_provider_fees(
        provider_fee_in_unit="0",
        start_order_tx_id=start_order_tx_id,
        bt=bt,
        dt=dt,
        publisher_wallet=publisher_wallet,
        publish_market_wallet=publish_market_wallet,
        consume_market_wallet=consume_market_wallet,
        consumer_wallet=consumer_wallet,
        provider_wallet=provider_wallet,
        web3=web3,
    )

    # Reuse order where:
    #     Order: expired
    #     Provider fees: expired
    # Simulate expired provider fees by setting them to non-zero
    reuse_order_with_mock_provider_fees(
        provider_fee_in_unit=provider_fee_in_unit,
        start_order_tx_id=start_order_tx_id,
        bt=bt,
        dt=dt,
        publisher_wallet=publisher_wallet,
        publish_market_wallet=publish_market_wallet,
        consume_market_wallet=consume_market_wallet,
        consumer_wallet=consumer_wallet,
        provider_wallet=provider_wallet,
        web3=web3,
    )


def reuse_order_with_mock_provider_fees(
    provider_fee_in_unit: str,
    start_order_tx_id: str,
    bt: Datatoken,
    dt: Datatoken,
    publisher_wallet: Wallet,
    publish_market_wallet: Wallet,
    consume_market_wallet: Wallet,
    consumer_wallet: Wallet,
    provider_wallet: Wallet,
    web3: Web3,
):
    """Call reuse_order, and verify the balances/fees are correct"""

    opc_collector_address = get_opc_collector_address_from_datatoken(dt)

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
    provider_fee = parse_units(provider_fee_in_unit, bt.decimals())
    valid_until = int((datetime.utcnow() + timedelta(seconds=10)).timestamp())
    provider_fees = get_provider_fees(
        web3,
        provider_wallet,
        bt.address,
        provider_fee,
        valid_until,
    )

    # Reuse order
    dt.reuse_order(
        order_tx_id=start_order_tx_id,
        provider_fee_address=provider_fees["providerFeeAddress"],
        provider_fee_token=provider_fees["providerFeeToken"],
        provider_fee_amount=provider_fees["providerFeeAmount"],
        v=provider_fees["v"],
        r=provider_fees["r"],
        s=provider_fees["s"],
        valid_until=provider_fees["validUntil"],
        provider_data=provider_fees["providerData"],
        from_wallet=consumer_wallet,
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
