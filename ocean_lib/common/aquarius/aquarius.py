#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
Aquarius module.
Help to communicate with the metadata store.
"""

#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import json
import logging

from ocean_lib.common.ddo.ddo import DDO
from ocean_lib.common.http_requests.requests_session import get_requests_session

logger = logging.getLogger("aquarius")


class Aquarius:
    """Aquarius wrapper to call different endpoint of aquarius component."""

    def __init__(self, aquarius_url):
        """
        The Metadata class is a wrapper on the Metadata Store, which has exposed a REST API.

        :param aquarius_url: Url of the aquarius instance.
        """
        assert aquarius_url, f'Invalid url "{aquarius_url}"'
        # :HACK:
        if "/api/v1/aquarius/assets" in aquarius_url:
            aquarius_url = aquarius_url[: aquarius_url.find("/api/v1/aquarius/assets")]

        self._base_url = f"{aquarius_url}/api/v1/aquarius/assets"
        self._headers = {"content-type": "application/json"}

        logging.debug(f"Metadata Store connected at {aquarius_url}")
        logging.debug(f"Metadata Store API documentation at {aquarius_url}/api/v1/docs")
        logging.debug(f"Metadata assets at {self._base_url}")

        self.requests_session = get_requests_session()

    @property
    def root_url(self):
        return self._base_url[: self._base_url.find("/api/v1/")]

    @property
    def url(self):
        """Base URL of the aquarius instance."""
        return f"{self._base_url}/ddo"

    def get_service_endpoint(self):
        """
        Retrieve the endpoint with the ddo for a given did.

        :return: Return the url of the the ddo location
        """
        return f"{self.url}/" + "{did}"

    def list_assets(self):
        """
        List all the assets registered in the aquarius instance.

        :return: List of DID string
        """
        response = self.requests_session.get(self._base_url).content
        asset_list = _parse_response(response, [])

        return asset_list

    def get_asset_ddo(self, did):
        """
        Retrieve asset ddo for a given did.

        :param did: Asset DID string
        :return: DDO instance
        """
        response = self.requests_session.get(f"{self.url}/{did}").content
        parsed_response = _parse_response(response, None)

        if not parsed_response:
            return {}

        return DDO(dictionary=parsed_response)

    def get_asset_metadata(self, did):
        """
        Retrieve asset metadata for a given did.

        :param did: Asset DID string
        :return: metadata key of the DDO instance
        """
        response = self.requests_session.get(f"{self._base_url}/metadata/{did}").content
        parsed_response = _parse_response(response, [])

        return parsed_response

    def list_assets_ddo(self):
        """
        List all the ddos registered in the aquarius instance.

        :return: List of DDO instance
        """
        return json.loads(self.requests_session.get(self.url).content)

    def text_search(self, text, sort=None, offset=100, page=1):
        """
        Search in aquarius using text query.

        Given the string aquarius will do a full-text query to search in all documents.

        Currently implemented are the MongoDB and Elastic Search drivers.

        For a detailed guide on how to search, see the MongoDB driver documentation:
        mongodb driverCurrently implemented in:
        https://docs.mongodb.com/manual/reference/operator/query/text/

        And the Elastic Search documentation:
        https://www.elastic.co/guide/en/elasticsearch/guide/current/full-text-search.html
        Other drivers are possible according to each implementation.

        :param text: String to be search.
        :param sort: 1/-1 to sort ascending or descending.
        :param offset: Integer with the number of elements displayed per page.
        :param page: Integer with the number of page.
        :return: List of DDO instance
        """
        assert page >= 1, f"Invalid page value {page}. Required page >= 1."
        payload = {"text": text, "sort": sort, "offset": offset, "page": page}
        response = self.requests_session.post(
            f"{self.url}/query", data=json.dumps(payload), headers=self._headers
        )
        if response.status_code == 200:
            return self._parse_search_response(response.content)
        else:
            raise Exception(f"Unable to search for DDO: {response.content}")

    def query_search(self, search_query, sort=None, offset=100, page=1):
        """
        Search using a query.

        Currently implemented is the MongoDB query model to search for documents according to:
        https://docs.mongodb.com/manual/tutorial/query-documents/

        And an Elastic Search driver, which implements a basic parser to convert the query into
        elastic search format.

        Example: query_search({"price":[0,10]})

        :param search_query: Python dictionary, query following mongodb syntax
        :param sort: 1/-1 to sort ascending or descending.
        :param offset: Integer with the number of elements displayed per page.
        :param page: Integer with the number of page.
        :return: List of DDO instance
        """
        assert page >= 1, f"Invalid page value {page}. Required page >= 1."
        search_query["sort"] = sort
        search_query["offset"] = offset
        search_query["page"] = page
        response = self.requests_session.post(
            f"{self.url}/query", data=json.dumps(search_query), headers=self._headers
        )
        if response.status_code == 200:
            return self._parse_search_response(response.content)
        else:
            raise Exception(f"Unable to search for DDO: {response.content}")

    def validate_metadata(self, metadata):
        """
        Validate that the metadata of your ddo is valid.

        :param metadata: conforming to the Metadata accepted by Ocean Protocol, dict
        :return: bool
        """
        response = self.requests_session.post(
            f"{self.url}/validate", data=json.dumps(metadata), headers=self._headers
        )
        if response.content == b"true\n":
            return True
        else:
            logger.info(self._parse_search_response(response.content))
            return False

    @staticmethod
    def _parse_search_response(response):
        parsed_response = _parse_response(response, None)

        if isinstance(parsed_response, dict) or isinstance(parsed_response, list):
            return parsed_response

        raise ValueError(
            f"Unknown search response, expecting a list or dict, got {type(parsed_response)}."
        )


def _parse_response(response, default_return):
    if not response:
        return default_return

    try:
        return json.loads(response)
    except TypeError:
        return default_return
    except ValueError:
        raise ValueError(response.decode("UTF-8"))

    return default_return
