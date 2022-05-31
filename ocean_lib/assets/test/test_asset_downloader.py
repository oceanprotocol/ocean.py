#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
from unittest.mock import patch

import pytest
from requests.exceptions import InvalidURL

from ocean_lib.agreements.consumable import AssetNotConsumable, ConsumableCodes
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_downloader import download_asset_files, is_consumable
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.services.service import Service
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.ddo_helpers import (
    create_asset,
    create_basics,
    get_first_service_by_type,
    get_sample_ddo,
)


@pytest.mark.unit
def test_is_consumable():
    ddo_dict = get_sample_ddo()
    asset = Asset.from_dict(ddo_dict)
    service_dict = ddo_dict["services"][0]
    service = Service.from_dict(service_dict)
    with patch(
        "ocean_lib.assets.test.test_asset_downloader.DataServiceProvider.check_asset_file_info",
        return_value=False,
    ):
        assert (
            is_consumable(asset, service, {}, True) == ConsumableCodes.CONNECTIVITY_FAIL
        )

    with patch(
        "ocean_lib.assets.test.test_asset_downloader.DataServiceProvider.check_asset_file_info",
        return_value=True,
    ):
        assert (
            is_consumable(asset, service, {"type": "address", "value": "0xdddd"}, True)
            == ConsumableCodes.CREDENTIAL_NOT_IN_ALLOW_LIST
        )


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
    publisher_wallet, publisher_ocean_instance, tmpdir
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
    ddo = create_asset(publisher_ocean_instance, publisher_wallet)
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
    web3,
    config,
    tmpdir,
    publisher_wallet,
    publisher_ocean_instance,
    data_nft,
    datatoken,
):
    """Convert tmpdir: py._path.local.LocalPath to str, satisfy enforce-typing."""
    ocean_assets_download_destination_file_helper(
        web3,
        config,
        str(tmpdir),
        publisher_wallet,
        publisher_ocean_instance,
        data_nft,
        datatoken,
    )


def ocean_assets_download_destination_file_helper(
    web3,
    config,
    tmpdir,
    publisher_wallet,
    publisher_ocean_instance,
    data_nft,
    datatoken,
):
    """Downloading to an existing directory."""
    data_provider = DataServiceProvider

    _, metadata, encrypted_files = create_basics(config, web3, data_provider)
    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        data_nft_address=data_nft.address,
        deployed_datatokens=[datatoken],
    )
    access_service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)

    datatoken.mint(
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

    tx_id = datatoken.start_order(
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
        consume_market_order_fee_address=publisher_wallet.address,
        consume_market_order_fee_token=datatoken.address,
        consume_market_order_fee_amount=0,
        from_wallet=publisher_wallet,
    )

    orders = publisher_ocean_instance.get_user_orders(publisher_wallet.address)
    assert datatoken.address in [order.address for order in orders]
    assert tx_id in [order.transactionHash.hex() for order in orders]

    written_path = download_asset_files(
        ddo, access_service, publisher_wallet, tmpdir, tx_id
    )

    assert os.path.exists(written_path)
