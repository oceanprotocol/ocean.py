#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Provider module."""
import json
import logging
from typing import Union

from enforce_typing import enforce_types
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend
from requests.models import Response

from ocean_lib.data_provider.base import DataServiceProviderBase
from ocean_lib.exceptions import DataProviderException, OceanEncryptAssetUrlsError

logger = logging.getLogger(__name__)
keys = KeyAPI(NativeECCBackend)


class DataEncryptor(DataServiceProviderBase):
    """DataEncryptor class."""

    @staticmethod
    @enforce_types
    def encrypt(
        objects_to_encrypt: Union[list, str, bytes, dict], provider_uri: str
    ) -> Response:
        if isinstance(objects_to_encrypt, dict):
            data = json.dumps(objects_to_encrypt, separators=(",", ":"))
            payload = data.encode("utf-8")
        elif isinstance(objects_to_encrypt, str):
            payload = objects_to_encrypt.encode("utf-8")
        else:
            payload = objects_to_encrypt

        _, encrypt_endpoint = DataServiceProviderBase.build_encrypt_endpoint(
            provider_uri
        )
        response = DataServiceProviderBase._http_method(
            "post",
            encrypt_endpoint,
            data=payload,
            headers={"Content-type": "application/octet-stream"},
        )

        if not response or not hasattr(response, "status_code"):
            raise DataProviderException(
                f"Failed to get a response for request: encryptEndpoint={encrypt_endpoint}, payload={payload}, response is {response}"
            )

        if response.status_code != 201:
            msg = (
                f"Encrypt file urls failed at the encryptEndpoint "
                f"{encrypt_endpoint}, reason {response.text}, status {response.status_code}"
            )
            logger.error(msg)
            raise OceanEncryptAssetUrlsError(msg)

        logger.info(
            f"Asset urls encrypted successfully, encrypted urls str: {response.text},"
            f" encryptedEndpoint {encrypt_endpoint}"
        )

        return response
