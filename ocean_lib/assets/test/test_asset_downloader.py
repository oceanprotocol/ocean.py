#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from requests.exceptions import InvalidURL

from ocean_lib.agreements.consumable import AssetNotConsumable
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_downloader import download_asset_files
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.ddo_helpers import (
    create_asset,
    create_basics,
    get_first_service_by_type,
    get_sample_ddo,
)
from tests.resources.helper_functions import deploy_erc721_erc20


@pytest.mark.unit
def test_ocean_assets_download_failure(publisher_wallet):
    """Tests that downloading from an empty service raises an AssertionError."""

    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)
    access_service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)
    access_service.service_endpoint = None
    ddo.services[0] = access_service

    with pytest.raises(AssertionError):
        download_asset_files(
            ddo,
            access_service,
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
        )


@pytest.mark.unit
def test_invalid_provider_uri(publisher_wallet):
    """Tests with invalid provider URI that raise AssertionError."""
    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)

    with pytest.raises(InvalidURL):
        download_asset_files(
            ddo,
            ddo.services[0],
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
        )


@pytest.mark.unit
def test_invalid_state(publisher_wallet):
    """Tests different scenarios that raise AssetNotConsumable."""
    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)
    ddo.nft["state"] = 1

    with pytest.raises(AssetNotConsumable):
        download_asset_files(
            ddo,
            ddo.services[0],
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
        )

    ddo.metadata = []
    with pytest.raises(AssetNotConsumable):
        download_asset_files(
            ddo,
            ddo.services[0],
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
        )


@pytest.mark.integration
def test_ocean_assets_download_indexes(
    publisher_wallet, config, publisher_ocean_instance, tmpdir
):
    """Tests different values of indexes that raise AssertionError."""

    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)

    index = range(3)
    with pytest.raises(TypeError):
        download_asset_files(
            ddo,
            ddo.services[0],
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
            index=index,
        )

    index = -1
    with pytest.raises(AssertionError):
        download_asset_files(
            ddo,
            ddo.services[0],
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
            index=index,
        )

    index = 4
    ddo = create_asset(publisher_ocean_instance, publisher_wallet, config)
    with pytest.raises(AssertionError):
        download_asset_files(
            ddo,
            ddo.services[0],
            publisher_wallet,
            str(tmpdir),
            "test_order_tx_id",
            index=index,
        )


@pytest.mark.integration
def test_ocean_assets_download_destination_file(
    web3, config, tmpdir, publisher_wallet, publisher_ocean_instance
):
    """Convert tmpdir: py._path.local.LocalPath to str, satisfy enforce-typing."""
    ocean_assets_download_destination_file_helper(
        web3, config, str(tmpdir), publisher_wallet, publisher_ocean_instance
    )


def ocean_assets_download_destination_file_helper(
    web3, config, tmpdir, publisher_wallet, publisher_ocean_instance
):
    """Downloading to an existing directory."""
    data_provider = DataServiceProvider
    erc721_nft, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet, cap=to_wei("100")
    )

    _, metadata, encrypted_files = create_basics(config, web3, data_provider)
    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_nft.address,
        deployed_erc20_tokens=[erc20_token],
    )
    access_service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)

    erc20_token.mint(
        account_address=publisher_wallet.address,
        value=to_wei("50"),
        from_wallet=publisher_wallet,
    )

    initialize_response = data_provider.initialize(
        did=ddo.did,
        service=access_service,
        consumer_address=publisher_wallet.address,
    )

    provider_fees = initialize_response.json()["providerFee"]

    tx_id = erc20_token.start_order(
        consumer=publisher_wallet.address,
        service_index=ddo.get_index_of_service(access_service),
        provider_fee_address=provider_fees["providerFeeAddress"],
        provider_fee_token=provider_fees["providerFeeToken"],
        provider_fee_amount=provider_fees["providerFeeAmount"],
        v=provider_fees["v"],
        r=provider_fees["r"],
        s=provider_fees["s"],
        valid_until=provider_fees["validUntil"],
        provider_data=provider_fees["providerData"],
        consumer_market_fee_address=publisher_wallet.address,
        consumer_market_fee_token=erc20_token.address,
        consumer_market_fee_amount=0,
        from_wallet=publisher_wallet,
    )

    orders = publisher_ocean_instance.get_user_orders(publisher_wallet.address)
    assert erc20_token.address in [order.address for order in orders]
    assert tx_id in [order.transactionHash.hex() for order in orders]

    written_path = download_asset_files(
        ddo, access_service, publisher_wallet, tmpdir, tx_id
    )

    assert os.path.exists(written_path)
