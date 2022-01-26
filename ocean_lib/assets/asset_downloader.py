#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os
from typing import Optional

from enforce_typing import enforce_types
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger(__name__)


@enforce_types
def download_asset_files(
    asset: Asset,
    provider_uri: str,
    consumer_wallet: Wallet,
    destination: str,
    order_tx_id: str,
    index: Optional[int] = None,
    userdata: Optional[dict] = None,
) -> str:
    """Download asset data file or result file from compute job.

    :param asset: Asset instance
    :param provider_uri: Url of Provider, str
    :param consumer_wallet: Wallet instance of the consumer
    :param destination: Path, str
    :param order_tx_id: hex str the transaction hash of the startOrder tx
    :param index: Index of the document that is going to be downloaded, Optional[int]
    :param userdata: Dict of additional data from user
    :return: asset folder path, str
    """
    data_provider = DataServiceProvider
    assert data_provider.is_valid_provider(provider_uri=provider_uri), logger.error(
        "Invalid provider URI."
    )

    service = asset.get_service(ServiceTypes.ASSET_ACCESS)
    if not service.service_endpoint:
        logger.error(
            'Consume asset failed, service definition is missing the "serviceEndpoint".'
        )
        raise AssertionError(
            'Consume asset failed, service definition is missing the "serviceEndpoint".'
        )

    if index is not None:
        assert isinstance(index, int), logger.error("index has to be an integer.")
        assert index >= 0, logger.error("index has to be 0 or a positive integer.")

    asset_folder = os.path.join(destination, f"datafile.{asset.did}.{service.id}")
    if not os.path.exists(asset_folder):
        os.mkdir(asset_folder)

    data_provider.download(
        did=asset.did,
        service=service,
        tx_id=order_tx_id,
        consumer_wallet=consumer_wallet,
        destination_folder=asset_folder,
        index=index,
        userdata=userdata,
    )
    return asset_folder
