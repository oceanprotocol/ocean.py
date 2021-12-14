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
from ocean_lib.assets.asset import V3Asset
from ocean_lib.assets.v4.asset import V4Asset
from ocean_lib.http_requests.requests_session import get_requests_session

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

        # FIXME: add v1 for Aquarius version
        self.base_url = f"{aquarius_url}/api/aquarius/assets"

        logging.debug(f"Metadata Store connected at {aquarius_url}")
        logging.debug(f"Metadata Store API documentation at {aquarius_url}/api/v1/docs")
        logging.debug(f"Metadata assets at {self.base_url}")

        self.requests_session = get_requests_session()

    @classmethod
    def get_instance(cls, metadata_cache_uri: str) -> "Aquarius":
        return cls(metadata_cache_uri)

    @enforce_types
    def get_service_endpoint(self) -> str:
        """
        Retrieve the endpoint with the ddo for a given did.

        :return: Return the url of the ddo location
        """
        return f"{self.base_url}/ddo/" + "{did}"

    @enforce_types
    def get_encrypt_endpoint(self) -> str:
        """
        Retrieve the endpoint for DDO encryption

        :return: Return the url of the Aquarius ddo encryption endpoint
        """
        return f"{self.base_url}/ddo/encrypt"

    @enforce_types
    def get_asset_ddo(self, did: str) -> Optional[Union[V3Asset, V4Asset]]:
        """
        Retrieve asset ddo for a given did.

        :param did: Asset DID string
        :return: V3Asset or V4Asset instance
        """
        response = self.requests_session.get(f"{self.base_url}/ddo/{did}")

        if response.status_code == 200:
            response_dict = response.json()
            if response_dict.get("version").startswith("4."):
                return V4Asset.from_dict(response_dict)
            else:
                return V3Asset(dictionary=response_dict)

        return None

    @enforce_types
    def ddo_exists(self, did: str) -> bool:
        """
        Return whether the Asset with this did exists in Aqua

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
        :return: metadata key of the Asset instance
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
        :return: List of V3Asset instance
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
    def validate_asset(self, asset: V4Asset) -> Tuple[bool, Union[list, dict]]:
        """
        Validate the asset.

        :param asset: conforming to the asset accepted by Ocean Protocol, V4Asset
        :return: bool
        """
        asset_dict = asset.as_dictionary()

        response = self.requests_session.post(
            f"{self.base_url.replace('/v1/', '/')}/ddo/validate-remote",
            data=json.dumps(asset_dict),
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
