#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Provider module."""
import json
import logging
from typing import Union

from enforce_typing import enforce_types
from requests.models import Response

from ocean_lib.data_provider.base import DataServiceProviderBase
from ocean_lib.exceptions import OceanEncryptAssetUrlsError

logger = logging.getLogger(__name__)


class DataEncryptor(DataServiceProviderBase):
    """DataEncryptor class."""

    @staticmethod
    @enforce_types
    def encrypt(
        objects_to_encrypt: Union[list, str, bytes, dict],
        provider_uri: str,
        chain_id: int,
    ) -> Response:
        if isinstance(objects_to_encrypt, dict):
            data = json.dumps(objects_to_encrypt, separators=(",", ":"))
            payload = data.encode("utf-8")
        elif isinstance(objects_to_encrypt, str):
            payload = objects_to_encrypt.encode("utf-8")
        else:
            payload = objects_to_encrypt

        method, encrypt_endpoint = DataServiceProviderBase.build_endpoint(
            "encrypt", provider_uri, {"chainId": chain_id}
        )

        response = DataServiceProviderBase._http_method(
            method,
            encrypt_endpoint,
            data=payload,
            headers={"Content-type": "application/octet-stream"},
        )

        DataServiceProviderBase.check_response(
            response,
            "encryptEndpoint",
            encrypt_endpoint,
            payload,
            [201],
            OceanEncryptAssetUrlsError,
        )

        logger.info(
            f"Asset urls encrypted successfully, encrypted urls str: {response.text},"
            f" encryptedEndpoint {encrypt_endpoint}"
        )

        return response
