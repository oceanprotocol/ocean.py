#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Storage module."""
import logging
import os

from enforce_typing import enforce_types
from huggingface_hub import create_repo
from pathlib import Path
from requests.models import Response
from requests.sessions import Session
import requests
from typing import Union

from ocean_lib.config import Config
from ocean_lib.exceptions import StorageProviderException
from ocean_lib.http_requests.requests_session import get_requests_session

logger = logging.getLogger(__name__)


class StorageProvider:
    """StorageProvider class."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.storage_url = self.config.storage_url
        self.storage_type = get_storage_type(self.storage_url)
        self.requests_session = get_requests_session()
        self.payload_key = {"estuary": "data", "web3.storage": "file"}

    @staticmethod
    @enforce_types
    def get_requests_session() -> Session:
        """Get the http client."""
        return StorageProvider.requests_session

    @staticmethod
    @enforce_types
    def set_requests_session(requests_session: Session) -> None:
        """Set the http client to something other than the default `requests`."""
        StorageProvider.requests_session = requests_session

    @enforce_types
    def upload(self, object_to_upload: Union[str, bytes]) -> Response:

        response = self.requests_session.post(
            self.storage_url,
            files={self.payload_key[self.storage_type]: object_to_upload},
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
    def download(self, cid: str) -> Response:
        if self.storage_type == "web3.storage":
            url = f"https://{cid}.ipfs.dweb.link/"
            response = self.requests_session.get(url, timeout=20)
        elif self.storage_type == "estuary":
            url = f"https://dweb.link/ipfs/{cid}"
            response = requests.get(url, allow_redirects=True)  # to get content
            with open(cid, "wb") as f:
                f.write(response.content)
        return response


def get_storage_type(storage_url):
    domain = storage_url.split("/")[2]
    domain_to_type_dict = {
        "api.web3.storage": "web3.storage",
        "api.estuary.tech": "estuary",
        "shuttle-5.estuary.tech": "estuary",
    }
    return domain_to_type_dict[domain]
