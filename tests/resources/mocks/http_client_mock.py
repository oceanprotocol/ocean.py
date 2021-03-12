#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import Mock

from requests.models import Response


class HttpClientEvilMock:
    @staticmethod
    def post(*args, **kwargs):
        the_response = Mock(spec=Response)
        the_response.status_code = 400
        the_response.text = "Bad request (mocked)."
        return the_response


class HttpClientNiceMock:
    pass
