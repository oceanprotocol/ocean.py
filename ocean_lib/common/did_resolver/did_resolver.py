#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""DID Resolver module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging

from ocean_lib.common.aquarius.aquarius_provider import AquariusProvider

logger = logging.getLogger("keeper")


class DIDResolver:
    """
    DID Resolver class
    Resolve DID to a URL/DDO.
    """

    def __init__(self, data_token):
        self._data_token = data_token

    def resolve_asset(self, did, metadata_store_url=None, token_address=None):
        """
        Resolve a DID to an URL/DDO or later an internal/external DID.

        :param did: the asset id to resolve, this is part of the ocean
            DID did:op:<32 byte value>
        :param metadata_store_url: str the url of the metadata store
        :param token_address: str the address of the DataToken smart contract

        :return string: DDO of the resolved DID
        :return None: if the DID cannot be resolved
        :raises OceanDIDNotFound: if no DID can be found to resolve.
        """
        assert (
            metadata_store_url or token_address
        ), f"One of metadata_store_url or token_address is required."

        metadata_url = metadata_store_url
        if not metadata_store_url and token_address:
            metadata_url = self._data_token(token_address).get_metadata_url()

        logger.debug(f"found did {did} -> url={metadata_url}")
        return AquariusProvider.get_aquarius(metadata_url).get_asset_ddo(did)
