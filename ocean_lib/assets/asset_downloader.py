#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os
from typing import Optional, Type

from enforce_typing import enforce_types
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger(__name__)


@enforce_types
def download_asset_file(
    asset: Asset,
    consumer_wallet: Wallet,
    destination: str,
    order_tx_id: str,
    data_provider: Type[DataServiceProvider],
    file_index: int,
    userdata: Optional[dict] = None,
) -> str:
    """Download asset data file or result file from compute job.

    :param asset: Asset instance
    :param consumer_wallet: Wallet instance of the consumer
    :param destination: Path, str
    :param order_tx_id: hex str the transaction hash of the startOrder tx
    :param data_provider: DataServiceProvider class object
    :param file_index: Index of the document that is going to be downloaded, int
    :param userdata: Dict of additional data from user
    :return: asset folder path, str
    """
    service = asset.get_service(ServiceTypes.ASSET_ACCESS)
    service_endpoint = service.service_endpoint
    if not service_endpoint:
        logger.error(
            'Consume asset failed, service definition is missing the "serviceEndpoint".'
        )
        raise AssertionError(
            'Consume asset failed, service definition is missing the "serviceEndpoint".'
        )
    service_id = service.id

    assert isinstance(file_index, int), logger.error("index has to be an integer.")
    assert file_index >= 0, logger.error("index has to be 0 or a positive integer.")

    service_endpoint += "/api/services/initialize"
    data_provider.initialize(
        did=asset.did,
        service_id=service_id,
        file_index=file_index,
        consumer_address=consumer_wallet.address,
        service_endpoint=service_endpoint,
        userdata=userdata,
    )

    if not os.path.isabs(destination):
        destination = os.path.abspath(destination)
    if not os.path.exists(destination):
        os.mkdir(destination)

    asset_folder = os.path.join(destination, f"datafile.{asset.did}.{service_id}")
    if not os.path.exists(asset_folder):
        os.mkdir(asset_folder)

    service_endpoint.replace("initialize", "download")
    data_provider.download(
        did=asset.did,
        service_id=service_id,
        tx_id=order_tx_id,
        file_index=file_index,
        consumer_wallet=consumer_wallet,
        download_endpoint=service_endpoint,
        destination_folder=asset_folder,
        userdata=userdata,
    )
    return asset_folder
