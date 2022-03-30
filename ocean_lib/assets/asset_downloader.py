#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os
from typing import Optional, Union

from enforce_typing import enforce_types

from ocean_lib.agreements.consumable import AssetNotConsumable, ConsumableCodes
from ocean_lib.assets.asset import Asset
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.services.service import Service
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger(__name__)


@enforce_types
def download_asset_files(
    asset: Asset,
    service: Service,
    consumer_wallet: Wallet,
    destination: str,
    order_tx_id: Union[str, bytes],
    index: Optional[int] = None,
    userdata: Optional[dict] = None,
) -> str:
    """Download asset data file or result file from compute job.

    :param asset: Asset instance
    :param service: Sevice instance
    :param consumer_wallet: Wallet instance of the consumer
    :param destination: Path, str
    :param order_tx_id: hex str or hex bytes the transaction hash of the startOrder tx
    :param index: Index of the document that is going to be downloaded, Optional[int]
    :param userdata: Dict of additional data from user
    :return: asset folder path, str
    """
    data_provider = DataServiceProvider

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

    consumable_result = service.is_consumable(
        asset,
        {"type": "address", "value": consumer_wallet.address},
        with_connectivity_check=True,
    )
    if consumable_result != ConsumableCodes.OK:
        raise AssetNotConsumable(consumable_result)

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
