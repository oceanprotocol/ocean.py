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
from ocean_lib.assets.asset_downloader import download_asset_files, is_consumable
from ocean_lib.assets.ddo import DDO
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.datatoken import TokenFeeInfo
from ocean_lib.ocean.util import to_wei
from ocean_lib.services.service import Service
from tests.resources.ddo_helpers import (
    get_first_service_by_type,
    get_registered_asset_with_access_service,
    get_sample_ddo,
)


@pytest.mark.unit
def test_is_consumable():
    ddo_dict = get_sample_ddo()
    ddo = DDO.from_dict(ddo_dict)
    service_dict = ddo_dict["services"][0]
    service = Service.from_dict(service_dict)
    with patch(
        "ocean_lib.assets.test.test_asset_downloader.DataServiceProvider.check_asset_file_info",
        return_value=False,
    ):
        assert (
            is_consumable(ddo, service, {}, True) == ConsumableCodes.CONNECTIVITY_FAIL
        )

    with patch(
        "ocean_lib.assets.test.test_asset_downloader.DataServiceProvider.check_asset_file_info",
        return_value=True,
    ):
        assert (
            is_consumable(ddo, service, {"type": "address", "value": "0xdddd"}, True)
            == ConsumableCodes.CREDENTIAL_NOT_IN_ALLOW_LIST
        )


@pytest.mark.unit
def test_ocean_assets_download_failure(publisher_wallet):
    """Tests that downloading from an empty service raises an AssertionError."""

    ddo_dict = get_sample_ddo()
    ddo = DDO.from_dict(ddo_dict)
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
    ddo = DDO.from_dict(ddo_dict)
    ddo.services[0].service_endpoint = "http://nothing-here.com"

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
    ddo = DDO.from_dict(ddo_dict)
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
def test_ocean_assets_download_indexes(publisher_wallet):
    """Tests different values of indexes that raise AssertionError."""

    ddo_dict = get_sample_ddo()
    ddo = DDO.from_dict(ddo_dict)

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


@pytest.mark.integration
def test_ocean_assets_download_destination_file(
    tmpdir,
    publisher_wallet,
    publisher_ocean,
):
    """Convert tmpdir: py._path.local.LocalPath to str, satisfy enforce-typing."""
    data_provider = DataServiceProvider
    data_nft, datatoken, ddo = get_registered_asset_with_access_service(
        publisher_ocean, publisher_wallet
    )

    access_service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)

    datatoken.mint(
        publisher_wallet.address,
        to_wei(50),
        {"from": publisher_wallet},
    )

    initialize_response = data_provider.initialize(
        did=ddo.did,
        service=access_service,
        consumer_address=publisher_wallet.address,
    )

    provider_fees = initialize_response.json()["providerFee"]
    consume_market_fees = TokenFeeInfo(
        address=publisher_wallet.address,
        token=datatoken.address,
    )

    receipt = datatoken.start_order(
        consumer=publisher_wallet.address,
        service_index=ddo.get_index_of_service(access_service),
        provider_fees=provider_fees,
        consume_market_fees=consume_market_fees,
        tx_dict={"from": publisher_wallet},
    )

    orders = publisher_ocean.get_user_orders(
        publisher_wallet.address, datatoken.address
    )
    assert datatoken.address in [order.address for order in orders]
    assert receipt.txid in [order.transactionHash.hex() for order in orders]

    written_path = download_asset_files(
        ddo, access_service, publisher_wallet, str(tmpdir), receipt.txid
    )

    assert os.path.exists(written_path)

    # index not found, even though tx_id exists
    with pytest.raises(AssertionError):
        download_asset_files(
            ddo,
            ddo.services[0],
            publisher_wallet,
            str(tmpdir),
            receipt.txid,
            index=4,
        )
