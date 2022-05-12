#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import inspect
import json
from unittest.mock import Mock

from requests.models import Response
from requests.sessions import Session

TEST_SERVICE_ENDPOINTS = {
    "computeDelete": ["DELETE", "/api/services/compute"],
    "computeStart": ["POST", "/api/services/compute"],
    "computeStatus": ["GET", "/api/services/compute"],
    "computeStop": ["PUT", "/api/services/compute"],
    "computeResult": ["GET", "/api/services/computeResult"],
    "download": ["GET", "/api/services/download"],
    "encrypt": ["POST", "/api/services/encrypt"],
    "decrypt": ["POST", "/api/services/decrypt"],
    "fileinfo": ["POST", "/api/services/fileinfo"],
    "initialize": ["GET", "/api/services/initialize"],
    "initializeCompute": ["GET", "/api/services/initializeCompute"],
    "nonce": ["GET", "/api/services/nonce"],
    "computeEnvironments": ["GET", "/api/services/computeEnvironments"],
}


class HttpClientMockBase(Session):
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
                "serviceEndpoints": TEST_SERVICE_ENDPOINTS
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

    @staticmethod
    def specific_get(*args, **kwargs):
        return None


class HttpClientNiceMock(HttpClientMockBase):
    """Mock that returns 200 results and successful responses."""

    @staticmethod
    def specific_get(*args, **kwargs):
        the_response = Mock(spec=Response)
        the_response.status_code = 200
        the_response.content = '{"good_job": "with_mock"}'.encode("utf-8")

        return the_response

    @staticmethod
    def return_nice_response(indication, *args, **kwargs):
        the_response = Mock(spec=Response)
        the_response.status_code = 200
        json_result = {"good_job": ("with_mock_" + indication)}
        the_response.content = json.dumps(json_result).encode("utf-8")

        return the_response

    @staticmethod
    def delete(*args, **kwargs):
        return HttpClientNiceMock.return_nice_response("delete", *args, **kwargs)

    @staticmethod
    def put(*args, **kwargs):
        return HttpClientNiceMock.return_nice_response("put", *args, **kwargs)

    @staticmethod
    def post(*args, **kwargs):
        return HttpClientNiceMock.return_nice_response("post", *args, **kwargs)
