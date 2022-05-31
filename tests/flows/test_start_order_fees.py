#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime, timedelta
from typing import Tuple

import pytest
from web3 import Web3

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.services.service import Service
from ocean_lib.structures.file_objects import FilesType
from ocean_lib.web3_internal.currency import MAX_WEI, parse_units, to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import (
    get_first_service_by_type,
    get_opc_collector_address_from_datatoken,
)
from tests.resources.helper_functions import (
    get_address_of_type,
    get_provider_fees,
    transfer_base_token_if_balance_lte,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "base_token_name, publish_market_order_fee_in_unit, consume_market_order_fee_in_unit, provider_fee_in_unit",
    [
        # Small fees
        ("Ocean", "5", "6", "7"),
        ("MockDAI", "5", "6", "7"),
        ("MockUSDC", "5", "6", "7"),
        # Zero fees
        ("Ocean", "0", "0", "0"),
        ("MockUSDC", "0", "0", "0"),
        # Min fees
        (
            "Ocean",
            "0.000000000000000001",  # 1 wei
            "0.000000000000000001",  # 1 wei
            "0.000000000000000001",  # 1 wei
        ),
        ("MockUSDC", "0.000001", "0.000001", "0.000001"),  # Smallest USDC amounts
        # Large fees
        ("Ocean", "500", "600", "700"),
        ("MockUSDC", "500", "600", "700"),
    ],
)
def test_start_order_fees(
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
    factory_router: FactoryRouter,
    base_token_name: str,
    publish_market_order_fee_in_unit: str,
    consume_market_order_fee_in_unit: str,
    provider_fee_in_unit: str,
):
    bt = Datatoken(web3, get_address_of_type(config, base_token_name))

    # Send base tokens to the consumer so they can pay for fees
    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=factory_deployer_wallet,
        recipient=consumer_wallet.address,
        min_balance=parse_units("2000", bt.decimals()),
        amount_to_transfer=parse_units("2000", bt.decimals()),
    )

    publish_market_order_fee = parse_units(
        publish_market_order_fee_in_unit, bt.decimals()
    )

    asset, service, dt = create_asset_with_order_fee_and_timeout(
        web3=web3,
        config=config,
        file=file1,
        data_nft=data_nft,
        publisher_wallet=publisher_wallet,
        publish_market_order_fee_address=publish_market_wallet.address,
        publish_market_order_fee_token=bt.address,
        publish_market_order_fee_amount=publish_market_order_fee,
        timeout=3600,
    )

    # Mint 50 datatokens in consumer wallet from publisher.
    dt.mint(
        account_address=consumer_wallet.address,
        value=to_wei("50"),
        from_wallet=publisher_wallet,
    )

    opc_collector_address = get_opc_collector_address_from_datatoken(dt)

    # Get balances
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

    # Get provider fees
    provider_fee = parse_units(provider_fee_in_unit, bt.decimals())
    valid_for_two_hours = int((datetime.utcnow() + timedelta(hours=2)).timestamp())
    provider_fees = get_provider_fees(
        web3,
        provider_wallet,
        bt.address,
        provider_fee,
        valid_for_two_hours,
    )

    # Grant datatoken infinite approval to spend consumer's base tokens
    bt.approve(dt.address, MAX_WEI, consumer_wallet)

    # Start order for consumer
    consume_market_order_fee = parse_units(
        consume_market_order_fee_in_unit, bt.decimals()
    )
    dt.start_order(
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
        consume_market_order_fee_amount=consume_market_order_fee,
        from_wallet=consumer_wallet,
    )

    # Get balances
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

    # Get order fee amount
    publish_market_order_fee_amount = dt.get_publishing_market_fee()[2]
    assert publish_market_order_fee_amount == publish_market_order_fee

    # Get Ocean community fee amount
    ocean_community_order_fee = factory_router.get_opc_consume_fee()
    assert ocean_community_order_fee == to_wei("0.03")

    one_datatoken = to_wei(1)

    # Check balances
    assert publisher_bt_balance_before == publisher_bt_balance_after
    assert (
        publisher_dt_balance_before + one_datatoken - ocean_community_order_fee
        == publisher_dt_balance_after
    )
    assert (
        publish_market_bt_balance_before + publish_market_order_fee
        == publish_market_bt_balance_after
    )
    assert publish_market_dt_balance_before == publish_market_dt_balance_after
    assert (
        consume_market_bt_balance_before + consume_market_order_fee
        == consume_market_bt_balance_after
    )
    assert consume_market_dt_balance_before == consume_market_dt_balance_after
    assert (
        consumer_bt_balance_before
        - publish_market_order_fee
        - consume_market_order_fee
        - provider_fee
        == consumer_bt_balance_after
    )
    assert consumer_dt_balance_before - one_datatoken == consumer_dt_balance_after
    assert provider_bt_balance_before + provider_fee == provider_bt_balance_after
    assert provider_dt_balance_before == provider_dt_balance_after
    assert opc_bt_balance_before == opc_bt_balance_after
    assert opc_dt_balance_before + ocean_community_order_fee == opc_dt_balance_after


def create_asset_with_order_fee_and_timeout(
    web3: Web3,
    config: Config,
    file: FilesType,
    data_nft: DataNFT,
    publisher_wallet: Wallet,
    publish_market_order_fee_address: str,
    publish_market_order_fee_token: str,
    publish_market_order_fee_amount: int,
    timeout: int,
) -> Tuple[Asset, Service, Datatoken]:

    # Create datatoken with order fee
    datatoken = data_nft.create_datatoken(
        template_index=1,
        name="Datatoken 1",
        symbol="DT1",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publish_market_order_fee_address,
        publish_market_order_fee_token=publish_market_order_fee_token,
        publish_market_order_fee_amount=publish_market_order_fee_amount,
        bytess=[b""],
        from_wallet=publisher_wallet,
    )

    data_provider = DataServiceProvider
    ocean_assets = OceanAssets(config, web3, data_provider)
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }

    # Encrypt file objects
    encrypt_response = data_provider.encrypt([file], config.provider_url)
    encrypted_files = encrypt_response.content.decode("utf-8")

    # Create service with timeout
    service = Service(
        service_id="5",
        service_type=ServiceTypes.ASSET_ACCESS,
        service_endpoint=data_provider.get_url(config),
        datatoken=datatoken.address,
        files=encrypted_files,
        timeout=timeout,
    )

    # Publish asset
    asset = ocean_assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        services=[service],
        data_nft_address=data_nft.address,
        deployed_datatokens=[datatoken],
    )

    service = get_first_service_by_type(asset, ServiceTypes.ASSET_ACCESS)
    dt = Datatoken(web3, asset.datatokens[0]["address"])

    return asset, service, dt
