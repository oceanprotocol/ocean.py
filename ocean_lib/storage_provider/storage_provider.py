#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Storage module."""
import logging
import os

from enforce_typing import enforce_types
from requests.models import Response

from ocean_lib.config import Config
from ocean_lib.exceptions import StorageProviderException
from ocean_lib.http_requests.requests_session import get_requests_session

logger = logging.getLogger(__name__)

class StorageProvider:
    """StorageProvider class."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.storage_url = self.config.storage_url
        self.requests_session = get_requests_session()

    @enforce_types
    def upload(self, object_to_upload: bytes) -> Response:

        response = self.requests_session.post(
            self.storage_url,
            data={"file": object_to_upload},
            headers={"Authorization": "Bearer " + os.environ["STORAGE_TOKEN"]},
        )

        if not hasattr(response, "status_code"):
            raise StorageProviderException(
                f"Failed to get a response for request: storageEndpoint={self.storage_url}, response is {response}"
            )

        if response.status_code != 200:
            msg = (
                f"Upload file failed at the storageEndpoint "
                f"{self.storage_url}, reason {response.text}, status {response.status_code}"
            )
            logger.error(msg)
            raise StorageProviderException

        logger.info(
            f"Asset urls encrypted successfully, encrypted urls str: {response.text},"
            f" encryptedEndpoint {self.storage_url}"
        )

        return response

    @enforce_types
    def download(cid: str, provider: str ="web3.storage") -> Response:
        if provider == "web3.storage":
            url = f"https://{cid}.ipfs.dweb.link/"
            response = self.requests_session.get(
                url, timeout=20
            )
        elif provider == "estuary":
            url = f'https://dweb.link/ipfs/{cid}'
            response = requests.get(url, allow_redirects=True)  # to get content
            with open(cid, 'wb') as f:
                f.write(response.content)
        return response