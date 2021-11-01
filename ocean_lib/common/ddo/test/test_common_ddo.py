#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
    Test did_lib
"""
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.common.ddo.ddo import DDO
from ocean_lib.common.did import DID
from tests.resources.ddo_helpers import get_resource_path, get_sample_ddo
from tests.resources.helper_functions import get_publisher_wallet

TEST_SERVICE_TYPE = "ocean-meta-storage"
TEST_SERVICE_URL = "http://localhost:8005"


def test_creating_ddo_from_scratch():
    """Tests creating a DDO from scratch."""
    # create an empty ddo
    ddo = DDO()
    assert ddo.did is None
    assert ddo.asset_id is None
    assert ddo.created is not None, "DDO has not been created."

    did = DID.did({"0": "0x99999999999999999"})
    ddo.did = did
    assert ddo.did == did

    ddo.add_service(TEST_SERVICE_TYPE, TEST_SERVICE_URL)

    pub_acc = get_publisher_wallet()

    ddo.add_proof({"checksum": "test"}, pub_acc)
    ddo_text_proof = ddo.as_text()
    assert ddo_text_proof


def test_ddo_dict():
    """Tests DDO creation from dictionary."""
    sample_ddo_path = get_resource_path("ddo", "ddo_sample_algorithm.json")
    assert sample_ddo_path.exists(), f"{sample_ddo_path} does not exist!"

    ddo1 = DDO(json_filename=sample_ddo_path)
    assert ddo1.did == "did:op:8d1b4d73e7af4634958f071ab8dfe7ab0df14019"

    ddo1.add_proof({"checksum": "test"}, get_publisher_wallet())

    ddo_dict = ddo1.as_dictionary()
    assert ddo_dict["publicKey"][0]["id"] == ddo1.did
    assert ddo_dict["publicKey"][0]["owner"] == get_publisher_wallet().address
    assert ddo_dict["publicKey"][0]["type"] == "EthereumECDSAKey"

    assert ddo_dict["authentication"][0] == {
        "type": "RsaSignatureAuthentication2018",
        "publicKey": ddo1.did,
    }


def test_find_service():
    """Tests finding a DDO service by index."""
    ddo = get_sample_ddo("ddo_algorithm.json")
    service = ddo.get_service_by_index(0)
    assert service and service.type == ServiceTypes.METADATA, (
        "Failed to find service by integer " "id."
    )
    service = ddo.get_service_by_index(3)
    assert not service

    service = ddo.get_service(ServiceTypes.METADATA)
    assert service and service.type == ServiceTypes.METADATA, (
        "Failed to find service by id using " "" "service " "type."
    )
    assert service.index == 0, "index not as expected."
