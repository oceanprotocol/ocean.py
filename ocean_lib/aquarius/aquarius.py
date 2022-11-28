#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
Aquarius module.
Help to communicate with the metadata store.
"""

import json
import logging
import time
from typing import Optional, Tuple, Union

from enforce_typing import enforce_types

from ocean_lib.assets.asset import Asset
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
        if "/api/aquarius/assets" in aquarius_url:
            aquarius_url = aquarius_url[: aquarius_url.find("/api/aquarius/assets")]

        self.requests_session = get_requests_session()
        try:
            response = self.requests_session.get(f"{aquarius_url}")
        except Exception:
            response = None

        if not response or response.status_code != 200:
            raise Exception(f"Invalid or unresponsive aquarius url {aquarius_url}")

        self.base_url = f"{aquarius_url}/api/aquarius/assets"

        logging.debug(f"Aquarius metadata store connected at {aquarius_url}")
        logging.debug(f"Aquarius API documentation at {aquarius_url}/api/v1/docs")
        logging.debug(f"Aquarius DDOs at {self.base_url}")

    @classmethod
    def get_instance(cls, metadata_cache_uri: str) -> "Aquarius":
        return cls(metadata_cache_uri)

    @enforce_types
    def get_ddo(self, did: str) -> Optional[Asset]:
        """Retrieve ddo for a given did."""
        response = self.requests_session.get(f"{self.base_url}/ddo/{did}")

        if response.status_code == 200:
            response_dict = response.json()

            return Asset.from_dict(response_dict)

        return None

    @enforce_types
    def ddo_exists(self, did: str) -> bool:
        """Return whether the ddo with this did exists in Aqua"""
        response = self.requests_session.get(f"{self.base_url}/ddo/{did}").content
        #do _not_ change the string below unless github.com/oceanprotocol/aquarius is changed accordingly
        return f"Asset DID {did} not found in Elasticsearch" not in str(response)

    @enforce_types
    def get_ddo_metadata(self, did: str) -> dict:
        """
        Retrieve ddo metadata for a given did.

        :param did: DID string
        :return: metadata key of the DDO
        """
        response = self.requests_session.get(f"{self.base_url}/metadata/{did}")
        if response.status_code == 200:
            return response.json()

        return {}

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
    def validate_ddo(self, ddo: Asset) -> Tuple[bool, Union[list, dict]]:
        """Does the DDO conform to the Ocean DDO schema? 
        Schema definition: https://docs.oceanprotocol.com/core-concepts/did-ddo"""
        ddo_dict = ddo.as_dictionary()
        data = json.dumps(ddo_dict, separators=(",", ":")).encode("utf-8")

        response = self.requests_session.post(
            f"{self.base_url.replace('/v1/', '/')}/ddo/validate",
            data=data,
            headers={"content-type": "application/octet-stream"},
        )

        parsed_response = response.json()

        if parsed_response.get("hash"):
            return True, parsed_response

        return False, parsed_response

    @enforce_types
    def wait_for_ddo(self, did: str, timeout=60):
        start = time.time()
        ddo = None
        while not ddo:
            ddo = self.get_ddo(did)

            if not ddo:
                time.sleep(0.2)

            if time.time() - start > timeout:
                break

        return ddo

    @enforce_types
    def wait_for_ddo_update(self, ddo: Asset, tx: str):
        start = time.time()
        ddo = None
        while True:
            try:
                ddo = self.get_ddo(ddo.did)
            except ValueError:
                pass
            if not ddo:
                time.sleep(0.2)
            elif ddo.event.get("tx") == tx:
                logger.debug(
                    f"Transaction matching the given tx id detected in metadata store. ddo.event = {ddo.event}"
                )
                break

            if time.time() - start > 60:
                break

        return ddo
