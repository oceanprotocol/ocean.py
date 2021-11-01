#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
    Test did
"""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import secrets

import pytest
from ocean_lib.assets.did import (
    DID,
    OCEAN_PREFIX,
    did_parse,
    did_to_id,
    did_to_id_bytes,
    id_to_did,
)
from web3 import Web3

TEST_SERVICE_TYPE = "ocean-meta-storage"
TEST_SERVICE_URL = "http://localhost:8005"


def test_did():
    """Tests various DID functions."""
    assert DID.did({"0": "0x123"}).startswith(OCEAN_PREFIX)
    assert len(DID.did({"0": "0x123"})) - len(OCEAN_PREFIX) == 64
    _id = did_to_id(DID.did({"0": "0x123"}))
    assert not _id.startswith("0x"), "id portion of did should not have a 0x prefix."


def test_did_parse():
    """Tests DID parsing."""
    test_id = "%s" % secrets.token_hex(32)
    valid_did = "did:op:{0}".format(test_id)

    with pytest.raises(TypeError):
        did_parse(None)

    # test invalid in bytes
    with pytest.raises(TypeError):
        assert did_parse(valid_did.encode())


def test_id_to_did():
    """Tests id to did conversion."""
    test_id = "%s" % secrets.token_hex(32)
    valid_did_text = "did:op:{}".format(test_id)
    assert id_to_did(test_id) == valid_did_text

    # accept hex string from Web3 py
    assert id_to_did(Web3.toHex(hexstr=test_id)) == valid_did_text

    # accepts binary value
    assert id_to_did(Web3.toBytes(hexstr=test_id)) == valid_did_text

    with pytest.raises(TypeError):
        id_to_did(None)

    with pytest.raises(TypeError):
        id_to_did({"bad": "value"})

    assert id_to_did("") == "did:op:0"


def test_did_to_id():
    """Tests did to id conversion."""
    did = DID.did({"0": "0x123"})
    _id = did_to_id(did)
    assert _id is not None and len(_id) == 64, ""

    test_id = "%s" % secrets.token_hex(32)
    assert did_to_id(f"{OCEAN_PREFIX}{test_id}") == test_id
    assert did_to_id("did:op1:011") == "011"
    assert did_to_id("did:op:0") == "0"
    with pytest.raises(ValueError):
        did_to_id(OCEAN_PREFIX)

    assert did_to_id(f"{OCEAN_PREFIX}AB*&$#") == "AB", ""


def test_did_to_bytes():
    """Tests did to bytes conversion."""
    id_test = secrets.token_hex(32)
    did_test = "did:op:{}".format(id_test)
    id_bytes = Web3.toBytes(hexstr=id_test)

    assert did_to_id_bytes(did_test) == id_bytes
    assert did_to_id_bytes(id_bytes) == id_bytes

    with pytest.raises(ValueError):
        assert did_to_id_bytes(id_test) == id_bytes

    with pytest.raises(ValueError):
        assert did_to_id_bytes("0x" + id_test)

    with pytest.raises(ValueError):
        did_to_id_bytes("did:opx:Somebadtexstwithnohexvalue0x123456789abcdecfg")

    with pytest.raises(ValueError):
        did_to_id_bytes("")

    with pytest.raises(TypeError):
        did_to_id_bytes(None)

    with pytest.raises(TypeError):
        did_to_id_bytes({})

    with pytest.raises(TypeError):
        did_to_id_bytes(42)


def test_create_did():
    """Tests did creation."""
    proof = {
        "type": "DDOIntegritySignature",
        "created": "2016-02-08T16:02:20Z",
        "creator": "0x00Bd138aBD70e2F00903268F3Db08f2D25677C9e",
        "signatureValue": "0xc9eeb2b8106e…6abfdc5d1192641b",
        "checksum": {
            "0": "0x52b5c93b82dd9e7ecc3d9fdf4755f7f69a54484941897dc517b4adfe3bbc3377",
            "1": "0x999999952b5c93b82dd9e7ecc3d9fdf4755f7f69a54484941897dc517b4adfe3",
        },
    }
    did = DID.did(proof["checksum"])
    assert (
        did == "did:op:138fccf336883ae6312c9b8b375745a90be369454080e90985fb3e314ab0df25"
    )
