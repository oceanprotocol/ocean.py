#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Storage module."""
import logging
import os
from json import JSONDecodeError

from enforce_typing import enforce_types
from huggingface_hub import create_repo
from pathlib import Path
from requests.exceptions import InvalidURL
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
        self.gateway = os.getenv("IPFS_GATEWAY")
        if not self.gateway:
            raise StorageProviderException("No IPFS_GATEWAY defined.")
        self.gateway_uri = StorageProvider.get_gateway_uri(self.gateway)
        self.gateway_type = StorageProvider.get_gateway_type(self.gateway_uri)
        self.requests_session = get_requests_session()
        self.payload_key = {"estuary.tech": "data", "web3.storage": "file"}

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
            self.gateway_uri,
            files={self.payload_key[self.gateway_type]: object_to_upload},
            headers={"Authorization": "Bearer " + os.environ["STORAGE_TOKEN"]},
        )

        if not hasattr(response, "status_code"):
            raise StorageProviderException(
                f"Failed to get a response for request: storageEndpoint={self.gateway}, response is {response}"
            )

        if response.status_code != 200:
            msg = (
                f"Upload file failed at the storageEndpoint "
                f"{self.gateway}, reason {response.text}, status {response.status_code}"
            )
            logger.error(msg)
            raise StorageProviderException

        logger.info(
            f"Asset urls encrypted successfully, encrypted urls str: {response.text},"
            f" encryptedEndpoint {self.gateway}"
        )

        return response

    @enforce_types
    def download(self, cid: str) -> Response:
        if self.gateway_type == "web3.storage":
            url = f"https://{cid}.ipfs.dweb.link/"
            response = self.requests_session.get(url, timeout=20)
        elif self.gateway_type == "estuary.tech":
            url = f"https://dweb.link/ipfs/{cid}"
            response = requests.get(url, allow_redirects=True)  # to get content
            with open(cid, "wb") as f:
                f.write(response.content)
        return response

    @staticmethod
    @enforce_types
    def get_gateway_uri(gateway: str) -> str:
        parts = gateway.split("/")
        
        if len(parts) < 2:
            raise InvalidURL(f"InvalidURL {gateway}.")
        
        try:
            response = requests.get(gateway).json()
        except (requests.exceptions.RequestException, JSONDecodeError):
            raise InvalidURL(f"InvalidURL {gateway}.")

        gateway_type = StorageProvider.get_gateway_type(gateway)

        if gateway_type not in ['web3.storage', "estuary.tech"]:
            raise InvalidURL(f"InvalidURL {gateway}.")

        if gateway not in ["https://api.web3.storage/upload", "https://api.estuary.tech/content/add", "https://shuttle-5.estuary.tech/content/add"]:
            raise InvalidURL(f"InvalidURL {gateway}.")

        return gateway

    @staticmethod
    @enforce_types
    def get_gateway_type(gateway_uri: str) -> str:
        parts = gateway_uri.split("/")[2]
        parts = parts.split(".")[1:]
    
        gateway_type = parts[0] + '.' + parts[1]

        return gateway_type

    @staticmethod
    @enforce_types
    def is_valid_gateway(gateway: str) -> bool:
        try:
            StorageProvider.get_gateway_uri(gateway)
        except InvalidURL:
            return False

        return True