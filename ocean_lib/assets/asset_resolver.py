#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""DID Resolver module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging

from ocean_lib.assets.asset import Asset
from ocean_lib.common.aquarius.aquarius_provider import AquariusProvider
from ocean_lib.models.data_token import DataToken

logger = logging.getLogger("keeper")


def resolve_asset(did, metadata_cache_uri=None, token_address=None):
    """Resolve a DID to an URL/DDO or later an internal/external DID.

    :param did: the asset id to resolve, this is part of the ocean
        DID did:op:<32 byte value>
    :param metadata_cache_uri: str the url of the metadata store
    :param token_address: str the address of the DataToken smart contract

    :return string: DDO of the resolved DID
    :return None: if the DID cannot be resolved
    """
    assert (
        metadata_cache_uri or token_address
    ), "One of metadata_cache_uri or token_address is required."

    metadata_url = metadata_cache_uri
    if not metadata_cache_uri and token_address:
        metadata_url = DataToken(token_address).get_metadata_url()

    logger.debug(f"found did {did} -> url={metadata_url}")
    ddo = AquariusProvider.get_aquarius(metadata_url).get_asset_ddo(did)
    return Asset(dictionary=ddo.as_dictionary())
