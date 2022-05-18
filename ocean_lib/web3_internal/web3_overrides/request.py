#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Copied from Web3 python library to control the `requests` session parameters."""

import lru
import requests
from enforce_typing import enforce_types
from requests.adapters import HTTPAdapter
from requests.sessions import Session
from web3._utils.caching import generate_cache_key


@enforce_types
def _remove_session(key: str, session: Session) -> None:
    session.close()


_session_cache = lru.LRU(8, callback=_remove_session)


@enforce_types
def _get_session(*args, **kwargs) -> Session:
    cache_key = generate_cache_key((args, kwargs))
    if cache_key not in _session_cache:
        # This is the main change from original Web3 `_get_session`
        session = requests.sessions.Session()
        session.mount(
            "http://",
            HTTPAdapter(pool_connections=25, pool_maxsize=25, pool_block=True),
        )
        session.mount(
            "https://",
            HTTPAdapter(pool_connections=25, pool_maxsize=25, pool_block=True),
        )
        _session_cache[cache_key] = session
    return _session_cache[cache_key]


@enforce_types
def make_post_request(endpoint_uri: str, data: bytes, *args, **kwargs) -> bytes:
    kwargs.setdefault("timeout", 10)
    session = _get_session(endpoint_uri)
    response = session.post(endpoint_uri, data=data, *args, **kwargs)
    response.raise_for_status()

    return response.content
