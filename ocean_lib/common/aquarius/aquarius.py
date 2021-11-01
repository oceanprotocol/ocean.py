#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
Aquarius module.
Help to communicate with the metadata store.
"""

import json
import logging
from typing import Optional, Tuple, Union

from enforce_typing import enforce_types
from ocean_lib.common.ddo.ddo import DDO
from ocean_lib.common.http_requests.requests_session import get_requests_session

logger = logging.getLogger("aquarius")


class Aquarius:
    """Aquarius wrapper to call different endpoint of aquarius component."""

    @enforce_types
    def __init__(self, aquarius_url: str) -> None:
        """
        The Metadata class is a wrapper on the Metadata Store, which has exposed a REST API.

        :param aquarius_url: Url of the aquarius instance.
        """
        assert aquarius_url, f'Invalid url "{aquarius_url}"'
        # :HACK:
        if "/api/v1/aquarius/assets" in aquarius_url:
            aquarius_url = aquarius_url[: aquarius_url.find("/api/v1/aquarius/assets")]

        self.base_url = f"{aquarius_url}/api/v1/aquarius/assets"

        logging.debug(f"Metadata Store connected at {aquarius_url}")
        logging.debug(f"Metadata Store API documentation at {aquarius_url}/api/v1/docs")
        logging.debug(f"Metadata assets at {self.base_url}")

        self.requests_session = get_requests_session()

    @enforce_types
    def get_service_endpoint(self) -> str:
        """
        Retrieve the endpoint with the ddo for a given did.

        :return: Return the url of the the ddo location
        """
        return f"{self.base_url}/ddo/" + "{did}"

    @enforce_types
    def get_encrypt_endpoint(self) -> str:
        """
        Retrieve the endpoint for DDO encrption

        :return: Return the url of the the Aquarius ddo encryption endpoint
        """
        return f"{self.base_url}/ddo/encrypt"

    @enforce_types
    def get_asset_ddo(self, did: str) -> Optional[DDO]:
        """
        Retrieve asset ddo for a given did.

        :param did: Asset DID string
        :return: DDO instance
        """
        response = self.requests_session.get(f"{self.base_url}/ddo/{did}")

        if response.status_code == 200:
            return DDO(dictionary=response.json())

        return None

    @enforce_types
    def ddo_exists(self, did: str) -> bool:
        """
        Return whether the DDO with this did exists in Aqua

        :param did: Asset DID string
        :return: bool
        """
        response = self.requests_session.get(f"{self.base_url}/ddo/{did}").content

        return f"Asset DID {did} not found in Elasticsearch" not in str(response)

    @enforce_types
    def get_asset_metadata(self, did: str) -> list:
        """
        Retrieve asset metadata for a given did.

        :param did: Asset DID string
        :return: metadata key of the DDO instance
        """
        response = self.requests_session.get(f"{self.base_url}/metadata/{did}")
        if response.status_code == 200:
            return response.json()

        return []

    @enforce_types
    def query_search(self, search_query: dict) -> list:
        """
        Search using a query.

        Currently implemented is the MongoDB query model to search for documents according to:
        https://docs.mongodb.com/manual/tutorial/query-documents/

        And an Elastic Search driver, which implements a basic parser to convert the query into
        elastic search format.

        Example: query_search({"price":[0,10]})

        :param search_query: Python dictionary, query following elasticsearch syntax
        :return: List of DDO instance
        """
        response = self.requests_session.post(
            f"{self.base_url}/query",
            data=json.dumps(search_query),
            headers={"content-type": "application/json"},
        )

        if response.status_code == 200:
            return response.json()["hits"]["hits"]

        raise ValueError(f"Unable to search for DDO: {response.content}")

    @enforce_types
    def validate_metadata(self, metadata: dict) -> Tuple[bool, Union[list, dict]]:
        """
        Validate that the metadata of your ddo is valid.

        :param metadata: conforming to the Metadata accepted by Ocean Protocol, dict
        :return: bool
        """
        response = self.requests_session.post(
            f"{self.base_url}/ddo/validate",
            data=json.dumps(metadata),
            headers={"content-type": "application/json"},
        )

        if response.content == b"true\n":
            return True, []

        parsed_response = response.json()
        return False, parsed_response

    @enforce_types
    def encrypt(self, text: str) -> bytes:
        """
        Encrypt the contents of an asset.

        :return: Return the encrypted asset string.
        """
        try:
            endpoint = self.get_encrypt_endpoint()
            response = self.requests_session.post(
                endpoint,
                data=text,
                headers={"content-type": "application/octet-stream"},
            )

            if response and response.status_code == 200:
                return response.content
            else:
                raise ValueError("Failed to encrypt asset.")
        except Exception:
            raise ValueError("Failed to encrypt asset.")
