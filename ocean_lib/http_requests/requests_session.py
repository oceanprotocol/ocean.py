#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from requests.adapters import HTTPAdapter
from requests.sessions import Session


@enforce_types
class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = 30
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        # timeout = kwargs.get("timeout")
        # if timeout is None:
        kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def get_requests_session() -> Session:
    """
    Set connection pool maxsize and block value to avoid `connection pool full` warnings.

    :return: requests session
    """
    session = Session()
    session.mount(
        "http://",
        TimeoutHTTPAdapter(
            pool_connections=25,
            pool_maxsize=25,
            pool_block=True,
            max_retries=1,
            timeout=30,
        ),
    )
    session.mount(
        "https://",
        TimeoutHTTPAdapter(
            pool_connections=25,
            pool_maxsize=25,
            pool_block=True,
            max_retries=1,
            timeout=30,
        ),
    )
    return session
