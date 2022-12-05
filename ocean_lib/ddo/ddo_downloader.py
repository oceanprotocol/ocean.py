#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os
from typing import Optional, Union

from enforce_typing import enforce_types

from ocean_lib.agreements.consumable import ConsumableCodes, DDONotConsumable
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.ddo.ddo import DDO
from ocean_lib.services.service import Service

logger = logging.getLogger(__name__)


@enforce_types
def download_ddo_files(
    ddo: DDO,
    service: Service,
    consumer_wallet,
    destination: str,
    order_tx_id: Union[str, bytes],
    index: Optional[int] = None,
    userdata: Optional[dict] = None,
) -> str:
    """Download DDO data file or result file from compute job.

    :param ddo: DDO instance
    :param service: Sevice instance
    :param consumer_wallet: Wallet instance of the consumer
    :param destination: Path, str
    :param order_tx_id: hex str or hex bytes the transaction hash of the startOrder tx
    :param index: Index of the document that is going to be downloaded, Optional[int]
    :param userdata: Dict of additional data from user
    :return: DDO folder path, str
    """
    data_provider = DataServiceProvider

    if not service.service_endpoint:
        logger.error(
            'Consume DDO failed, service definition is missing the "serviceEndpoint".'
        )
        raise AssertionError(
            'Consume DDO failed, service definition is missing the "serviceEndpoint".'
        )

    if index is not None:
        assert isinstance(index, int), logger.error("index has to be an integer.")
        assert index >= 0, logger.error("index has to be 0 or a positive integer.")

    consumable_result = is_consumable(
        ddo,
        service,
        {"type": "address", "value": consumer_wallet.address},
        with_connectivity_check=True,
        userdata=userdata,
    )
    if consumable_result != ConsumableCodes.OK:
        raise DDONotConsumable(consumable_result)

    service_index_in_ddo = ddo.get_index_of_service(service)
    ddo_folder = os.path.join(destination, f"datafile.{ddo.did},{service_index_in_ddo}")

    if not os.path.exists(ddo_folder):
        os.makedirs(ddo_folder)

    data_provider.download(
        did=ddo.did,
        service=service,
        tx_id=order_tx_id,
        consumer_wallet=consumer_wallet,
        destination_folder=ddo_folder,
        index=index,
        userdata=userdata,
    )

    return ddo_folder


@enforce_types
def is_consumable(
    ddo: DDO,
    service: Service,
    credential: Optional[dict] = None,
    with_connectivity_check: bool = True,
    userdata: Optional[dict] = None,
) -> bool:
    """Checks whether a DDO is consumable and returns a ConsumableCode."""
    if ddo.is_disabled:
        return ConsumableCodes.DDO_DISABLED

    if with_connectivity_check and not DataServiceProvider.check_ddo_file_info(
        ddo.did, service.id, service.service_endpoint, userdata=userdata
    ):
        return ConsumableCodes.CONNECTIVITY_FAIL

    # to be parameterized in the future, can implement other credential classes
    if ddo.requires_address_credential:
        return ddo.validate_access(credential)

    return ConsumableCodes.OK
