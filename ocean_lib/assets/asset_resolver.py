#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""DID Resolver module."""

import logging

from enforce_typing import enforce_types

from ocean_lib.aquarius import Aquarius
from ocean_lib.assets.asset import Asset

logger = logging.getLogger("keeper")


@enforce_types
def resolve_asset(did: str, metadata_cache_uri: str) -> Asset:
    """Resolve a DID to an URL/DDO or later an internal/external DID.

    :param did: the asset id to resolve, this is part of the ocean
        DID did:op:<32 byte value>
    :param metadata_cache_uri: str the url of the metadata store

    :return Asset: the resolved DID
    """
    assert metadata_cache_uri, "metadata_cache_uri is required."

    logger.debug(f"found did {did} -> url={metadata_cache_uri}")
    ddo = Aquarius.get_instance(metadata_cache_uri).get_asset_ddo(did)

    return ddo
