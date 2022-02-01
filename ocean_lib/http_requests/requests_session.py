#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from requests.adapters import HTTPAdapter
from requests.sessions import Session


@enforce_types
def get_requests_session() -> Session:
    """
    Set connection pool maxsize and block value to avoid `connection pool full` warnings.

    :return: requests session
    """
    session = Session()
    session.mount(
        "http://",
        HTTPAdapter(
            pool_connections=25, pool_maxsize=25, pool_block=True, max_retries=1
        ),
    )
    session.mount(
        "https://",
        HTTPAdapter(
            pool_connections=25, pool_maxsize=25, pool_block=True, max_retries=1
        ),
    )
    return session
