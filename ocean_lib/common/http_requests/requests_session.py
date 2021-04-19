#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import requests
from requests.adapters import HTTPAdapter


def get_requests_session():
    """
    Set connection pool maxsize and block value to avoid `connection pool full` warnings.

    :return: requests session
    """
    session = requests.sessions.Session()
    session.mount(
        "http://", HTTPAdapter(pool_connections=25, pool_maxsize=25, pool_block=True)
    )
    session.mount(
        "https://", HTTPAdapter(pool_connections=25, pool_maxsize=25, pool_block=True)
    )
    return session
