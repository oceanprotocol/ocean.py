import os

import pytest
from ocean_utils.agreements.service_agreement import ServiceAgreement
from ocean_utils.agreements.service_types import ServiceTypes

from ocean_lib.assets.asset_downloader import download_asset_files
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from tests.resources.ddo_helpers import wait_for_ddo
from tests.resources.helper_functions import get_publisher_wallet


def test_ocean_assets_download_failure(publisher_ocean_instance, metadata):
    """Tests that downloading from an empty service raises an AssertionError."""
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()
    data_provider = DataServiceProvider()

    ddo = publisher_ocean_instance.assets.create(metadata_copy, publisher)
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    sa = ServiceAgreement.from_ddo(ServiceTypes.ASSET_ACCESS, ddo)
    sa.__dict__["_service_endpoint"] = None
    ddo.__dict__["_services"][1] = sa

    with pytest.raises(AssertionError):
        download_asset_files(
            sa.index,
            ddo,
            publisher,
            "test_destination",
            ddo.data_token_address,
            "test_order_tx_id",
            data_provider,
        )


def test_ocean_assets_download_indexes(publisher_ocean_instance, metadata):
    """Tests different values of indexes that raise AssertionError."""
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()
    data_provider = DataServiceProvider()

    ddo = publisher_ocean_instance.assets.create(metadata_copy, publisher)
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    sa = ServiceAgreement.from_ddo(ServiceTypes.ASSET_ACCESS, ddo)

    index = range(3)
    with pytest.raises(AssertionError):
        download_asset_files(
            sa.index,
            ddo,
            publisher,
            "test_destination",
            ddo.data_token_address,
            "test_order_tx_id",
            data_provider,
            index,
        )
    index = -1
    with pytest.raises(AssertionError):
        download_asset_files(
            sa.index,
            ddo,
            publisher,
            "test_destination",
            ddo.data_token_address,
            "test_order_tx_id",
            data_provider,
            index,
        )
    index = 4
    with pytest.raises(AssertionError):
        download_asset_files(
            sa.index,
            ddo,
            publisher,
            "test_destination",
            ddo.data_token_address,
            "test_order_tx_id",
            data_provider,
            index,
        )


def test_ocean_assets_download_destination_file(publisher_ocean_instance, metadata):
    """Tests downloading to an existing directory."""
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()
    data_provider = DataServiceProvider()

    ddo = publisher_ocean_instance.assets.create(metadata_copy, publisher)
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    sa = ServiceAgreement.from_ddo(ServiceTypes.ASSET_ACCESS, ddo)

    with pytest.raises(IsADirectoryError):
        destination = os.path.abspath("tests/resources/downloads")
        written_path = download_asset_files(
            sa.index,
            ddo,
            publisher,
            destination,
            ddo.data_token_address,
            "test_order_tx_id",
            data_provider,
        )
        assert os.path.exists(written_path)
        os.remove(written_path)
