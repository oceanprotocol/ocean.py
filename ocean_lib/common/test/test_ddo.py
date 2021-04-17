#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
    Test did_lib
"""
import json

import pytest
from ocean_lib.common.agreements.service_agreement import ServiceAgreement, ServiceTypes
from ocean_lib.common.agreements.service_factory import (
    ServiceDescriptor,
    ServiceFactory,
)
from ocean_lib.common.ddo.ddo import DDO
from ocean_lib.common.ddo.public_key_base import PublicKeyBase
from ocean_lib.common.ddo.public_key_rsa import (
    PUBLIC_KEY_TYPE_ETHEREUM_ECDSA,
    PUBLIC_KEY_TYPE_RSA,
)
from ocean_lib.common.did import DID
from tests.resources.ddo_helpers import get_resource_path, get_sample_ddo
from tests.resources.helper_functions import get_publisher_wallet

TEST_SERVICE_TYPE = "ocean-meta-storage"
TEST_SERVICE_URL = "http://localhost:8005"


def _get_sample_ddo(name):
    sample_ddo_path = get_resource_path("ddo", name)
    assert sample_ddo_path.exists(), f"{sample_ddo_path} does not exist!"
    with open(sample_ddo_path) as f:
        sample_ddo_json_dict = json.load(f)

    return sample_ddo_json_dict


def test_creating_ddo_from_scratch():
    # create an empty ddo
    ddo = DDO()
    assert ddo.did is None
    assert ddo.asset_id is None
    assert ddo.created is not None

    did = DID.did({"0": "0x99999999999999999"})
    ddo.assign_did(did)
    assert ddo.did == did

    ddo.add_service(TEST_SERVICE_TYPE, TEST_SERVICE_URL)

    pub_acc = get_publisher_wallet()

    # add a proof to the first public_key/authentication
    ddo.add_proof("checksum", pub_acc)
    ddo_text_proof = ddo.as_text()
    assert ddo_text_proof

    assert not ddo.public_keys
    ddo.add_public_key(did, pub_acc.address)
    assert len(ddo.public_keys) == 1
    assert ddo.get_public_key(0) == ddo.public_keys[0]
    with pytest.raises(IndexError):
        ddo.get_public_key(1)

    assert ddo.get_public_key(did) == ddo.public_keys[0]
    assert ddo.get_public_key("0x32233") is None

    assert not ddo.authentications
    ddo.add_authentication(did, "")
    assert len(ddo.authentications) == 1


def test_create_auth_from_json():
    auth = {"publicKey": "0x00000", "type": "auth-type", "nothing": ""}
    assert DDO.create_authentication_from_json(auth) == {
        "publicKey": "0x00000",
        "type": "auth-type",
    }
    with pytest.raises(ValueError):
        DDO.create_authentication_from_json({"type": "auth-type"})


def test_create_public_key_from_json():
    pkey = {"id": "pkeyid", "type": "keytype", "owner": "0x00009"}
    pub_key_inst = DDO.create_public_key_from_json(pkey)
    assert isinstance(pub_key_inst, PublicKeyBase)
    assert pub_key_inst.get_id() == pkey["id"]
    assert pub_key_inst.get_type() == PUBLIC_KEY_TYPE_ETHEREUM_ECDSA
    assert pub_key_inst.get_owner() == pkey["owner"]

    pub_key_inst = DDO.create_public_key_from_json({"type": PUBLIC_KEY_TYPE_RSA})
    assert pub_key_inst.get_id() == ""
    assert pub_key_inst.get_type() == PUBLIC_KEY_TYPE_RSA
    assert pub_key_inst.get_owner() is None


# TODO: repurpose/refurbish: all below
def not_test_load_ddo_json():
    # TODO: Fix
    sample_ddo_json_dict = _get_sample_ddo("ddo_sample1.json")
    sample_ddo_json_string = json.dumps(sample_ddo_json_dict)

    this_ddo = DDO(json_text=sample_ddo_json_string)
    service = this_ddo.get_service(ServiceTypes.METADATA)
    assert service
    assert service.type == ServiceTypes.METADATA
    assert service.attributes
    assert this_ddo.as_dictionary() == sample_ddo_json_dict, (
        f"ddo seems to have changed after being loaded into DDO object: \n"
        f"{this_ddo.as_text()} vs. {sample_ddo_json_string}"
    )


def not_test_ddo_dict():
    sample_ddo_path = get_resource_path("ddo", "ddo_sample1.json")
    assert sample_ddo_path.exists(), f"{sample_ddo_path} does not exist!"

    ddo1 = DDO(json_filename=sample_ddo_path)
    assert len(ddo1.public_keys) == 3
    assert (
        ddo1.did
        == "did:op:0c184915b07b44c888d468be85a9b28253e80070e5294b1aaed81c2f0264e429"
    )


def not_test_find_service():
    ddo = get_sample_ddo()
    service = ddo.get_service_by_index(0)
    assert service and service.type == ServiceTypes.METADATA, (
        "Failed to find service by integer " "id."
    )
    service = ddo.get_service_by_index("0")
    assert service and service.type == ServiceTypes.METADATA, (
        "Failed to find service by str(int)" " id."
    )

    service = ddo.get_service_by_index(3)
    assert service and service.type == ServiceTypes.ASSET_ACCESS, (
        "Failed to find service by " "integer id."
    )
    service = ddo.get_service_by_index("3")
    assert service and service.type == ServiceTypes.ASSET_ACCESS, (
        "Failed to find service by str(" "int) id."
    )

    service = ddo.get_service(ServiceTypes.ASSET_ACCESS)
    assert service and service.type == ServiceTypes.ASSET_ACCESS, (
        "Failed to find service by id " "using service type."
    )
    assert service.index == 3, "index not as expected."

    service = ddo.get_service(ServiceTypes.METADATA)
    assert service and service.type == ServiceTypes.METADATA, (
        "Failed to find service by id using " "" "service " "type."
    )
    assert service.index == 0, "index not as expected."


def not_test_service_factory():
    ddo = DDO(dictionary=_get_sample_ddo("ddo_sample1.json"))
    type_to_service = {s.type: s for s in ddo.services}
    metadata = ddo.metadata

    md_descriptor = ServiceDescriptor.metadata_service_descriptor(
        metadata, type_to_service[ServiceTypes.METADATA].service_endpoint
    )
    access_service = type_to_service[ServiceTypes.ASSET_ACCESS]
    access_descriptor = ServiceDescriptor.access_service_descriptor(
        access_service.attributes, access_service.service_endpoint
    )
    compute_descriptor = ServiceDescriptor.compute_service_descriptor(
        access_service.attributes, access_service.service_endpoint
    )

    services = ServiceFactory.build_services(
        [md_descriptor, access_descriptor, compute_descriptor]
    )
    assert len(services) == 3
    assert services[0].type == ServiceTypes.METADATA
    assert services[1].type == ServiceTypes.ASSET_ACCESS
    assert services[2].type == ServiceTypes.CLOUD_COMPUTE

    assert isinstance(services[1], ServiceAgreement)
    assert isinstance(services[2], ServiceAgreement)
