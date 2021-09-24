#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""DID Resolver module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging
from typing import Optional

from enforce_typing import enforce_types
from ocean_lib.assets.asset import Asset
from ocean_lib.common.aquarius.aquarius_provider import AquariusProvider
from ocean_lib.models.data_token import DataToken
from web3.main import Web3

logger = logging.getLogger("keeper")


@enforce_types
def resolve_asset(
    did: str,
    metadata_cache_uri: Optional[str] = None,
    web3: Optional[Web3] = None,
    token_address: Optional[str] = None,
) -> Asset:
    """Resolve a DID to an URL/DDO or later an internal/external DID.

    :param did: the asset id to resolve, this is part of the ocean
        DID did:op:<32 byte value>
    :param metadata_cache_uri: str the url of the metadata store
    :param web3: Web3 instance
    :param token_address: str the address of the DataToken smart contract

    :return Asset: the resolved DID
    """
    assert metadata_cache_uri or (
        web3 and token_address
    ), "Either metadata_cache_uri or (web3 and token_address) is required."

    if not metadata_cache_uri:
        metadata_cache_uri = DataToken(web3, token_address).get_metadata_url()

    logger.debug(f"found did {did} -> url={metadata_cache_uri}")
    ddo = AquariusProvider.get_aquarius(metadata_cache_uri).get_asset_ddo(did)

    if ddo:
        return Asset(dictionary=ddo.as_dictionary())
