#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
    Test did_lib
"""
from ocean_lib.common.agreements.service_agreement import ServiceTypes
from ocean_lib.common.agreements.service_factory import (
    ServiceDescriptor,
    ServiceFactory,
)
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
    ddo.assign_did(did)
    assert ddo.did == did

    ddo.add_service(TEST_SERVICE_TYPE, TEST_SERVICE_URL)

    pub_acc = get_publisher_wallet()

    ddo.add_proof("checksum", pub_acc)
    ddo_text_proof = ddo.as_text()
    assert ddo_text_proof


def test_ddo_dict():
    """Tests DDO creation from dictionary."""
    sample_ddo_path = get_resource_path("ddo", "ddo_sample_algorithm.json")
    assert sample_ddo_path.exists(), f"{sample_ddo_path} does not exist!"

    ddo1 = DDO(json_filename=sample_ddo_path)
    assert ddo1.did == "did:op:8d1b4d73e7af4634958f071ab8dfe7ab0df14019"


def test_find_service():
    """Tests finding a DDO service by index."""
    ddo = get_sample_ddo("ddo_algorithm.json")
    service = ddo.get_service_by_index(0)
    assert service and service.type == ServiceTypes.METADATA, (
        "Failed to find service by integer " "id."
    )
    service = ddo.get_service_by_index("0")
    assert service and service.type == ServiceTypes.METADATA, (
        "Failed to find service by str(int)" " id."
    )

    service = ddo.get_service(ServiceTypes.METADATA)
    assert service and service.type == ServiceTypes.METADATA, (
        "Failed to find service by id using " "" "service " "type."
    )
    assert service.index == 0, "index not as expected."


def test_service_factory():
    """Tests ServiceFactory builds services."""
    ddo = get_sample_ddo("ddo_algorithm.json")
    type_to_service = {s.type: s for s in ddo.services}
    metadata = ddo.metadata

    md_descriptor = ServiceDescriptor.metadata_service_descriptor(
        metadata, type_to_service[ServiceTypes.METADATA].service_endpoint
    )
    services = ServiceFactory.build_services([md_descriptor])
    assert len(services) == 1
    assert services[0].type == ServiceTypes.METADATA
