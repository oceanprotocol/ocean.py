#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import inspect
from abc import ABC
from unittest.mock import Mock

from requests.models import Response


class HttpClientMockBase(ABC):
    """Parent class for all HTTPClient mocks."""

    @classmethod
    def get(cls, *args, **kwargs):
        """Handles the base case of service endpoints."""
        is_get_endpoints_request = False
        for (_, _, _, fn, _, _) in inspect.getouterframes(inspect.currentframe()):
            if fn == "get_service_endpoints":
                is_get_endpoints_request = True

        if is_get_endpoints_request:
            the_response = Mock(spec=Response)
            the_response.status_code = 200
            the_response.json.return_value = {
                "serviceEndpoints": {"nonce": ["GET", "nonce/endpoint"]}
            }
            return the_response

        return cls.specific_get(*args, **kwargs)


class HttpClientEvilMock(HttpClientMockBase):
    """Mock that generally returns 400 results and errors."""

    @staticmethod
    def post(*args, **kwargs):
        the_response = Mock(spec=Response)
        the_response.status_code = 400
        the_response.text = "Bad request (mocked)."
        return the_response

    @staticmethod
    def specific_get(*args, **kwargs):
        the_response = Mock(spec=Response)
        the_response.status_code = 400
        the_response.text = "Bad request (mocked)."
        return the_response


class HttpClientEmptyMock(HttpClientMockBase):
    """Mock unresponsiveness."""

    @staticmethod
    def post(*args, **kwargs):
        return None


class HttpClientNiceMock(HttpClientMockBase):
    """Mock that returns 200 results and successful responses."""
