#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.web3_internal.web3_overrides.request import make_post_request
from web3 import HTTPProvider


class CustomHTTPProvider(HTTPProvider):
    """Override requests to control the connection pool to make it blocking."""

    def make_request(self, method, params):
        self.logger.debug(
            "Making request HTTP. URI: %s, Method: %s", self.endpoint_uri, method
        )
        request_data = self.encode_rpc_request(method, params)
        raw_response = make_post_request(
            self.endpoint_uri, request_data, **self.get_request_kwargs()
        )
        response = self.decode_rpc_response(raw_response)
        self.logger.debug(
            "Getting response HTTP. URI: %s, " "Method: %s, Response: %s",
            self.endpoint_uri,
            method,
            response,
        )
        return response
