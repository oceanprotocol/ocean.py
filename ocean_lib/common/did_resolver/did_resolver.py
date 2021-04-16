#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""DID Resolver module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging

from ocean_lib.common.aquarius.aquarius_provider import AquariusProvider
from ocean_lib.common.did import did_to_id_bytes

logger = logging.getLogger("keeper")


class DIDResolver:
    """
    DID Resolver class
    Resolve DID to a URL/DDO.
    """

    def __init__(self, did_registry):
        self._did_registry = did_registry

    def resolve(self, did):
        """
        Resolve a DID to an URL/DDO or later an internal/external DID.

        :param did: 32 byte value or DID string to resolver, this is part of the ocean
            DID did:op:<32 byte value>
        :return string: URL or DDO of the resolved DID
        :return None: if the DID cannot be resolved
        :raises ValueError: if did is invalid
        :raises TypeError: if did has invalid format
        :raises TypeError: on non 32byte value as the DID
        :raises TypeError: on any of the resolved values are not string/DID bytes.
        :raises OceanDIDNotFound: if no DID can be found to resolve.
        """

        did_bytes = did_to_id_bytes(did)
        if not isinstance(did_bytes, bytes):
            raise TypeError("Invalid did: a 32 Byte DID value required.")

        # resolve a DID to a DDO
        url = self.get_resolve_url(did_bytes)
        logger.debug(f"found did {did} -> url={url}")
        return AquariusProvider.get_aquarius(url).get_asset_ddo(did)

    def get_resolve_url(self, did_bytes):
        """Return a did value and value type from the block chain event record using 'did'.

        :param did_bytes: DID, hex-str
        :return url: Url, str
        """
        data = self._did_registry.get_registered_attribute(did_bytes)
        if not (data and data.get("value")):
            return None

        return data["value"]
