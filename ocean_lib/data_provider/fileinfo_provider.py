#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Provider module."""
import logging
from typing import Any

from enforce_typing import enforce_types
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend
from requests.models import Response

from ocean_lib.data_provider.base import DataServiceProviderBase
from ocean_lib.http_requests.requests_session import get_requests_session

logger = logging.getLogger(__name__)
keys = KeyAPI(NativeECCBackend)


class FileInfoProvider(DataServiceProviderBase):
    """DataServiceProvider class.

    The main functions available are:
    - consume_service
    - run_compute_service (not implemented yet)
    """

    _http_client = get_requests_session()
    provider_info = None

    @staticmethod
    @enforce_types
    def fileinfo(
        did: str, service: Any, with_checksum: bool = False
    ) -> Response:  # Can not add Service typing due to enforce_type errors.
        _, fileinfo_endpoint = DataServiceProviderBase.build_fileinfo(
            service.service_endpoint
        )
        payload = {"did": did, "serviceId": service.id}

        if with_checksum:
            payload["checksum"] = 1

        response = DataServiceProviderBase._http_method(
            "post", fileinfo_endpoint, json=payload
        )

        DataServiceProviderBase.check_response(
            response, "fileInfoEndpoint", fileinfo_endpoint, payload
        )

        logger.info(
            f"Retrieved asset files successfully"
            f" FileInfoEndpoint {fileinfo_endpoint} from did {did} with service id {service.id}"
        )
        return response
