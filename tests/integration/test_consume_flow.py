#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import shutil

import pytest
from web3 import Web3

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_nft import ERC721NFT
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import parse_units, to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import get_first_service_by_type
from tests.resources.helper_functions import (
    get_address_of_type,
    transfer_base_token_if_balance_lte,
)


@pytest.mark.integration
@pytest.mark.parametrize(
    "base_token_name, publish_market_order_fee",
    [
        ("Ocean", "10"),
        ("MockDAI", "10"),
        ("MockUSDC", "10"),
    ],
)
def test_consume_flow(
    web3: Web3,
    config: Config,
    publisher_wallet: Wallet,
    consumer_wallet: Wallet,
    provider_wallet: Wallet,
    factory_deployer_wallet: Wallet,
    base_token_name: str,
    publish_market_order_fee: str,
    erc721_nft: ERC721NFT,
    file1,
):
    bt = ERC20Token(web3, get_address_of_type(config, base_token_name))

    # Send base tokens to the consumer so they can pay for fees
    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=factory_deployer_wallet,
        recipient=consumer_wallet.address,
        min_balance=parse_units("1500", bt.decimals()),
        amount_to_transfer=parse_units("1500", bt.decimals()),
    )

    data_provider = DataServiceProvider
    asset = OceanAssets(config, web3, data_provider)
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }
    files = [file1]

    # Encrypt file objects
    encrypt_response = data_provider.encrypt(files, config.provider_url)
    encrypted_files = encrypt_response.content.decode("utf-8")

    # Publish a plain asset with one data token on chain
    publish_market_order_fee_in_wei = parse_units(
        publish_market_order_fee, bt.decimals()
    )
    asset = asset.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_nft.address,
        erc20_templates=[1],
        erc20_names=["Datatoken 1"],
        erc20_symbols=["DT1"],
        erc20_minters=[publisher_wallet.address],
        erc20_fee_managers=[publisher_wallet.address],
        erc20_publish_market_order_fee_addresses=[ZERO_ADDRESS],
        erc20_publish_market_order_fee_tokens=[bt.address],
        erc20_caps=[to_wei(100)],  # Doesn't matter, DT cap is always MAX_WEI
        erc20_publish_market_order_fee_amounts=[publish_market_order_fee_in_wei],
        erc20_bytess=[[b""]],
    )

    assert asset, "The asset is not created."
    assert asset.nft["name"] == "NFT"
    assert asset.nft["symbol"] == "NFTSYMBOL"
    assert asset.nft["address"] == erc721_nft.address
    assert asset.nft["owner"] == publisher_wallet.address
    assert asset.datatokens[0]["name"] == "Datatoken 1"
    assert asset.datatokens[0]["symbol"] == "DT1"

    service = get_first_service_by_type(asset, ServiceTypes.ASSET_ACCESS)
    dt = ERC20Token(web3, asset.datatokens[0]["address"])

    # Mint 50 ERC20 tokens in consumer wallet from publisher. Max cap = 100
    dt.mint(
        account_address=consumer_wallet.address,
        value=to_wei("50"),
        from_wallet=publisher_wallet,
    )

    # Check balances
    publisher_bt_balance_before = bt.balanceOf(publisher_wallet.address)
    publisher_dt_balance_before = dt.balanceOf(publisher_wallet.address)
    consumer_bt_balance_before = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance_before = dt.balanceOf(consumer_wallet.address)
    provider_bt_balance_before = bt.balanceOf(provider_wallet.address)
    provider_dt_balance_before = dt.balanceOf(provider_wallet.address)

    # Initialize service
    response = data_provider.initialize(
        did=asset.did, service=service, consumer_address=consumer_wallet.address
    )
    assert response
    assert response.status_code == 200
    assert response.json()["providerFee"]
    provider_fees = response.json()["providerFee"]

    # Start order for consumer
    tx_id = dt.start_order(
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
        consume_market_order_fee_address=consumer_wallet.address,
        consume_market_order_fee_token=dt.address,
        consume_market_order_fee_amount=0,
        from_wallet=consumer_wallet,
    )

    # Get balances
    publisher_bt_balance_after_order = bt.balanceOf(publisher_wallet.address)
    publisher_dt_balance_after_order = dt.balanceOf(publisher_wallet.address)
    consumer_bt_balance_after_order = bt.balanceOf(consumer_wallet.address)
    consuemr_dt_balance_after_order = dt.balanceOf(consumer_wallet.address)
    provider_bt_balance_after_order = bt.balanceOf(provider_wallet.address)
    provider_dt_balance_after_order = dt.balanceOf(provider_wallet.address)

    # Get order fee amount
    publish_market_order_fee_amount = dt.get_publishing_market_fee()[2]

    # Check balances
    assert (
        publisher_bt_balance_after_order + publish_market_order_fee_amount
        == publisher_bt_balance_after_order
    )
    assert publisher_dt_balance_before + to_wei(1) == publisher_dt_balance_after_order
    assert (
        consumer_bt_balance_before - publish_market_order_fee_amount
        == consumer_bt_balance_after_order
    )
    assert consumer_dt_balance_before - to_wei(1) == consuemr_dt_balance_after_order
    assert provider_bt_balance_before == provider_bt_balance_after_order
    assert provider_dt_balance_before == provider_dt_balance_after_order

    # Download file
    destination = config.downloads_path
    if not os.path.isabs(destination):
        destination = os.path.abspath(destination)

    if os.path.exists(destination) and len(os.listdir(destination)) > 0:
        list(
            map(
                lambda d: shutil.rmtree(os.path.join(destination, d)),
                os.listdir(destination),
            )
        )

    if not os.path.exists(destination):
        os.makedirs(destination)

    assert len(os.listdir(destination)) == 0

    asset.download_asset(
        asset=asset,
        service=service,
        consumer_wallet=consumer_wallet,
        destination=destination,
        order_tx_id=tx_id,
    )

    assert len(
        os.listdir(os.path.join(destination, os.listdir(destination)[0]))
    ) == len(files), "The asset folder is empty."

    # Get balances
    publisher_bt_balance_after_download = bt.balanceOf(publisher_wallet.address)
    publisher_dt_balance_after_download = dt.balanceOf(publisher_wallet.address)
    consumer_bt_balance_after_download = bt.balanceOf(consumer_wallet.address)
    consuemr_dt_balance_after_download = dt.balanceOf(consumer_wallet.address)
    provider_bt_balance_after_download = bt.balanceOf(provider_wallet.address)
    provider_dt_balance_after_download = dt.balanceOf(provider_wallet.address)

    # Check balances and provider fees
