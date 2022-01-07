#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_downloader import download_asset_files
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.ddo_helpers import get_sample_ddo
from tests.resources.helper_functions import deploy_erc721_erc20, create_basics


def test_ocean_assets_download_failure(publisher_wallet, config):
    """Tests that downloading from an empty service raises an AssertionError."""
    data_provider = DataServiceProvider

    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)
    access_service = ddo.get_service(ServiceTypes.ASSET_ACCESS)
    access_service.service_endpoint = None
    ddo.services[0] = access_service

    with pytest.raises(AssertionError):
        download_asset_files(
            ddo,
            config.provider_url,
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
            data_provider,
        )


def test_ocean_assets_download_indexes(publisher_wallet, config):
    """Tests different values of indexes that raise AssertionError."""
    data_provider = DataServiceProvider

    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)

    index = range(3)
    with pytest.raises(TypeError):
        download_asset_files(
            ddo,
            config.provider_url,
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
            data_provider,
            index=index,
        )

    index = -1
    with pytest.raises(AssertionError):
        download_asset_files(
            ddo,
            config.provider_url,
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
            data_provider,
            index=index,
        )

    index = 4
    with pytest.raises(Exception):
        download_asset_files(
            ddo,
            config.provider_url,
            publisher_wallet,
            "test_destination",
            "test_order_tx_id",
            data_provider,
            index=index,
        )


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
    """Tests downloading to an existing directory."""
    data_provider = DataServiceProvider
    erc721_token, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet, cap=to_wei(100)
    )

    _, metadata, encrypted_files = create_basics(config, web3, data_provider)
    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_token.address,
        deployed_erc20_tokens=[erc20_token],
    )
    access_service = ddo.get_service(ServiceTypes.ASSET_ACCESS)

    erc20_token.mint(
        account_address=publisher_wallet.address,
        value=to_wei(50),
        from_wallet=publisher_wallet,
    )

    initialize_response = data_provider.initialize(
        did=ddo.did,
        service_id=access_service.id,
        consumer_address=publisher_wallet.address,
        service_endpoint=data_provider.build_initialize_endpoint(config.provider_url)[
            1
        ],
    )

    tx_id = erc20_token.start_order(
        consumer=publisher_wallet.address,
        service_id=int(access_service.id),
        provider_fees=initialize_response.json()["providerFee"],
        from_wallet=publisher_wallet,
    )

    written_path = download_asset_files(
        ddo, config.provider_url, publisher_wallet, tmpdir, tx_id, data_provider
    )

    assert os.path.exists(written_path)
