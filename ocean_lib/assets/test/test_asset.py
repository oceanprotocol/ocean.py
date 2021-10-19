#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.assets.asset import V3Asset
from ocean_lib.assets.did import DID
from ocean_lib.common.agreements.service_types import ServiceTypes
from tests.resources.ddo_helpers import (
    get_registered_algorithm_ddo,
    get_registered_ddo_with_compute_service,
    get_resource_path,
    get_sample_ddo,
    wait_for_ddo,
)
from tests.resources.helper_functions import get_publisher_wallet

TEST_SERVICE_TYPE = "ocean-meta-storage"
TEST_SERVICE_URL = "http://localhost:8005"


def test_values(publisher_ocean_instance, metadata):
    """Tests if the DDO has the address for the data token given by 'values' property."""
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()

    ddo = publisher_ocean_instance.assets.create(metadata_copy, publisher)
    wait_for_ddo(publisher_ocean_instance, ddo.did)

    ddo_values = ddo.values
    assert ddo_values is not None
    for key, value in ddo_values.items():
        assert key == "dataToken"
        assert value.startswith("0x")
        assert ddo_values[key] is not None


def test_trusted_algorithms(publisher_ocean_instance):
    """Tests if the trusted algorithms list is returned correctly."""
    publisher = get_publisher_wallet()

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo.did)
    assert algorithm_ddo is not None

    ddo = get_registered_ddo_with_compute_service(
        publisher_ocean_instance, publisher, trusted_algorithms=[algorithm_ddo.did]
    )
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert ddo is not None

    trusted_algorithms = ddo.get_trusted_algorithms()
    service = ddo.get_service(ServiceTypes.CLOUD_COMPUTE)
    privacy_dict = service.attributes["main"].get("privacy")
    assert privacy_dict

    assert trusted_algorithms is not None
    assert len(trusted_algorithms) >= 1
    for index, trusted_algorithm in enumerate(trusted_algorithms):
        assert trusted_algorithm["did"] == algorithm_ddo.did
        assert "filesChecksum" and "containerSectionChecksum" in trusted_algorithm
        assert (
            trusted_algorithm["filesChecksum"]
            == privacy_dict["publisherTrustedAlgorithms"][index]["filesChecksum"]
        )
        assert (
            trusted_algorithm["containerSectionChecksum"]
            == privacy_dict["publisherTrustedAlgorithms"][index][
                "containerSectionChecksum"
            ]
        )
        assert (
            trusted_algorithm["did"]
            == privacy_dict["publisherTrustedAlgorithms"][index]["did"]
        )


def test_creating_asset_from_scratch():
    """Tests creating an Asset from scratch."""
    # create an empty ddo
    ddo = V3Asset()
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

    ddo1 = V3Asset(json_filename=sample_ddo_path)
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
