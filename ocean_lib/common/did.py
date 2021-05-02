#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""DID Lib to do DID's and DDO's."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import re

from eth_utils import remove_0x_prefix
from ocean_lib.common.utils.utilities import checksum
from web3 import Web3

OCEAN_PREFIX = "did:op:"


class DID:
    """Class representing an asset DID."""

    @staticmethod
    def did(seed):
        """
        Create a did.

        Format of the did:
        did:op:cb36cf78d87f4ce4a784f17c2a4a694f19f3fbf05b814ac6b0b7197163888865

        :param seed: The list of checksums that is allocated in the proof, dict
        :return: Asset did, str.
        """
        return OCEAN_PREFIX + remove_0x_prefix(checksum(seed))


def did_parse(did):
    """
    Parse a DID into it's parts.

    :param did: Asset did, str.
    :return: Python dictionary with the method and the id.
    """
    if not isinstance(did, str):
        raise TypeError(f"Expecting DID of string type, got {did} of {type(did)} type")

    match = re.match("^did:([a-z0-9]+):([a-zA-Z0-9-.]+)(.*)", did)
    if not match:
        raise ValueError(f"DID {did} does not seem to be valid.")

    result = {"method": match.group(1), "id": match.group(2)}

    return result


def id_to_did(did_id, method="op"):
    """Return an Ocean DID from given a hex id."""
    if isinstance(did_id, bytes):
        did_id = Web3.toHex(did_id)

    # remove leading '0x' of a hex string
    if isinstance(did_id, str):
        did_id = remove_0x_prefix(did_id)
    else:
        raise TypeError("did id must be a hex string or bytes")

    # test for zero address
    if Web3.toBytes(hexstr=did_id) == b"":
        did_id = "0"
    return f"did:{method}:{did_id}"


def did_to_id(did):
    """Return an id extracted from a DID string."""
    result = did_parse(did)
    return result["id"] if result and (result["id"] is not None) else None


def did_to_id_bytes(did):
    """
    Return an Ocean DID to it's correspondng hex id in bytes.

    So did:op:<hex>, will return <hex> in byte format
    """
    if isinstance(did, str):
        if re.match("^[0x]?[0-9A-Za-z]+$", did):
            raise ValueError(f"{did} must be a DID not a hex string")
        else:
            did_result = did_parse(did)
            if not did_result:
                raise ValueError(f"{did} is not a valid did")
            if not did_result["id"]:
                raise ValueError(f"{did} is not a valid ocean did")
            id_bytes = Web3.toBytes(hexstr=did_result["id"])
    elif isinstance(did, bytes):
        id_bytes = did
    else:
        raise TypeError(
            f"Unknown did format, expected str or bytes, got {did} of type {type(did)}"
        )
    return id_bytes
