#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from ocean_lib.assets.asset_downloader import download_asset_files
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from tests.resources.ddo_helpers import get_sample_ddo


def test_ocean_assets_download_failure(publisher_wallet):
    """Tests that downloading from an empty service raises an AssertionError."""
    data_provider = DataServiceProvider

    ddo = get_sample_ddo()
    sa = ddo.get_service(ServiceTypes.ASSET_ACCESS)
    sa.service_endpoint = None
    ddo.services[1] = sa

    with pytest.raises(AssertionError):
        download_asset_files(
            sa.index,
            ddo,
            publisher_wallet,
            "test_destination",
            "",
            "test_order_tx_id",
            data_provider,
        )


def test_ocean_assets_download_indexes(publisher_wallet):
    """Tests different values of indexes that raise AssertionError."""
    data_provider = DataServiceProvider

    ddo = get_sample_ddo()
    sa = ddo.get_service(ServiceTypes.ASSET_ACCESS)

    index = range(3)
    with pytest.raises(TypeError):
        download_asset_files(
            sa.index,
            ddo,
            publisher_wallet,
            "test_destination",
            "",
            "test_order_tx_id",
            data_provider,
            index,
        )

    index = -1
    with pytest.raises(AssertionError):
        download_asset_files(
            sa.index,
            ddo,
            publisher_wallet,
            "test_destination",
            "",
            "test_order_tx_id",
            data_provider,
            index,
        )
    index = 4
    with pytest.raises(AssertionError):
        download_asset_files(
            sa.index,
            ddo,
            publisher_wallet,
            "test_destination",
            "",
            "test_order_tx_id",
            data_provider,
            index,
        )


def test_ocean_assets_download_destination_file(tmpdir):
    """Convert tmpdir: py._path.local.LocalPath to str, satisfy enforce-typing."""
    ocean_assets_download_destination_file_helper(str(tmpdir))


def ocean_assets_download_destination_file_helper(tmpdir, publisher_wallet):
    """Tests downloading to an existing directory."""
    data_provider = DataServiceProvider

    ddo = get_sample_ddo()
    sa = ddo.get_service(ServiceTypes.ASSET_ACCESS)

    written_path = download_asset_files(
        sa.index,
        ddo,
        publisher_wallet,
        tmpdir,
        "0x1",
        "test_order_tx_id",
        data_provider,
    )
    assert os.path.exists(written_path)
