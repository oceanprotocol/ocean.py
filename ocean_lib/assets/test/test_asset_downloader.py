#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_downloader import download_asset_file
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from tests.resources.ddo_helpers import get_sample_ddo
from tests.resources.mocks.data_provider_mock import DataProviderMock


def test_ocean_assets_download_failure(publisher_wallet):
    """Tests that downloading from an empty service raises an AssertionError."""
    data_provider = DataServiceProvider

    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)
    access_service = ddo.get_service(ServiceTypes.ASSET_ACCESS)
    access_service.service_endpoint = None
    ddo.services[0] = access_service

    with pytest.raises(AssertionError):
        download_asset_file(
            ddo,
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
            data_provider,
            0,
        )


def test_ocean_assets_download_indexes(publisher_wallet):
    """Tests different values of indexes that raise AssertionError."""
    data_provider = DataServiceProvider

    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)

    index = range(3)
    with pytest.raises(TypeError):
        download_asset_file(
            ddo,
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
            data_provider,
            index,
        )

    index = -1
    with pytest.raises(AssertionError):
        download_asset_file(
            ddo,
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
            data_provider,
            index,
        )


def test_ocean_assets_download_destination_file(tmpdir, publisher_wallet):
    """Convert tmpdir: py._path.local.LocalPath to str, satisfy enforce-typing."""
    ocean_assets_download_destination_file_helper(str(tmpdir), publisher_wallet)


def ocean_assets_download_destination_file_helper(tmpdir, publisher_wallet):
    """Tests downloading to an existing directory."""
    data_provider = DataProviderMock
    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)
    ddo.services[0].files = "https://url.com/file1.csv"
    ddo.services[0].service_endpoint = "http://localhost:8030"

    written_path = download_asset_file(
        ddo, publisher_wallet, tmpdir, "test_order_tx_id", data_provider, 0
    )
    assert os.path.exists(written_path)
