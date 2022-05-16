#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Storage module."""
import os

from enforce_typing import enforce_types
from requests.models import Response

from ocean_lib.config import Config
from ocean_lib.http_requests.requests_session import get_requests_session

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
            headers={"Authorization": "Bearer " + os.environ["WEB3_STORAGE_TOKEN"]},
        )
        return response

    @enforce_types
    def download(cid: str) -> Response:
        url = f"https://{cid}.ipfs.dweb.link/"
        response = self.requests_session.get(
            url, timeout=20
        )
        return response        