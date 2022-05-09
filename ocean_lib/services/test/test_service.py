#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import patch

import pytest

from ocean_lib.assets.asset import Asset
from ocean_lib.services.service import Service
from tests.resources.ddo_helpers import (
    get_sample_algorithm_ddo,
    get_sample_ddo,
    get_sample_ddo_with_compute_service,
)


@pytest.mark.unit
def test_service():
    """Tests that the get_cost function for ServiceAgreement returns the correct value."""
    ddo_dict = get_sample_ddo()
    service_dict = ddo_dict["services"][0]
    service_dict["additionalInformation"] = {"message": "Sample DDO"}
    sa = Service.from_dict(service_dict)

    assert sa.id == "1"
    assert sa.name == "Download service"
    assert sa.type == "access"
    assert sa.service_endpoint == "https://myprovider.com"
    assert sa.datatoken == "0x123"
    assert sa.additional_information == {"message": "Sample DDO"}

    assert sa.as_dictionary() == {
        "id": "1",
        "type": "access",
        "serviceEndpoint": "https://myprovider.com",
        "datatokenAddress": "0x123",
        "files": "0x0000",
        "timeout": 0,
        "name": "Download service",
        "description": "Download service",
        "additionalInformation": {"message": "Sample DDO"},
    }

    ddo_dict = get_sample_ddo()
    service_dict = ddo_dict["services"][0]
    del service_dict["type"]
    with pytest.raises(IndexError):
        Service.from_dict(service_dict)

    ddo_dict = get_sample_ddo()
    asset = Asset.from_dict(ddo_dict)
    with patch(
        "ocean_lib.services.service.DataServiceProvider.check_asset_file_info"
    ) as mock:
        mock.return_value = False
        assert sa.is_consumable(asset, {}, True) == 2

    with patch(
        "ocean_lib.services.service.DataServiceProvider.check_asset_file_info"
    ) as mock:
        mock.return_value = True
        assert (
            sa.is_consumable(asset, {"type": "address", "value": "0xdddd"}, True) == 3
        )


@pytest.mark.unit
def test_trusted_algo_functions(publisher_ocean_instance):
    algorithm_ddo = get_sample_algorithm_ddo(filename="ddo_algorithm2.json")
    algorithm_ddo.did = "did:op:123"
    algorithm_ddo_v2 = get_sample_algorithm_ddo(filename="ddo_algorithm2.json")
    algorithm_ddo_v2.did = "did:op:1234"
    algorithm_ddo_v3 = get_sample_algorithm_ddo(filename="ddo_algorithm2.json")
    algorithm_ddo_v3.did = "did:op:3333"

    ddo_dict = get_sample_ddo_with_compute_service()
    service_dict = ddo_dict["services"][1]
    compute_service = Service.from_dict(service_dict)
    assert compute_service.type == "compute"

    # remove an existing algorithm to publisher_trusted_algorithms list
    new_publisher_trusted_algorithms = (
        compute_service.remove_publisher_trusted_algorithm(algorithm_ddo.did)
    )

    assert (
        new_publisher_trusted_algorithms is not None
    ), "Remove process of a trusted algorithm failed."
    assert len(new_publisher_trusted_algorithms) == 1

    # remove a trusted algorithm that does not belong to publisher_trusted_algorithms list
    new_publisher_trusted_algorithms = (
        compute_service.remove_publisher_trusted_algorithm(algorithm_ddo_v3.did)
    )
    assert len(new_publisher_trusted_algorithms) == 1


@pytest.mark.unit
def test_utilitary_functions_for_trusted_algorithm_publishers(publisher_ocean_instance):
    """Tests adding/removing trusted algorithms in the DDO metadata."""
    ddo = Asset.from_dict(get_sample_ddo_with_compute_service())
    compute_service = ddo.services[1]
    assert compute_service.type == "compute"

    addr1 = publisher_ocean_instance.web3.eth.account.create().address
    compute_service.compute_values["publisherTrustedAlgorithmPublishers"] = [addr1]

    addr2 = publisher_ocean_instance.web3.eth.account.create().address
    # add a new trusted algorithm to the publisher_trusted_algorithms list
    new_publisher_trusted_algo_publishers = (
        compute_service.add_publisher_trusted_algorithm_publisher(addr2)
    )

    assert (
        new_publisher_trusted_algo_publishers is not None
    ), "Added a new trusted algorithm failed. The list is empty."
    assert len(new_publisher_trusted_algo_publishers) == 2

    # add an existing algorithm to publisher_trusted_algorithms list
    new_publisher_trusted_algo_publishers = (
        compute_service.add_publisher_trusted_algorithm_publisher(addr2.upper())
    )
    assert len(new_publisher_trusted_algo_publishers) == 2

    # remove an existing algorithm to publisher_trusted_algorithms list
    new_publisher_trusted_algo_publishers = (
        compute_service.remove_publisher_trusted_algorithm_publisher(addr2.upper())
    )

    assert len(new_publisher_trusted_algo_publishers) == 1

    addr3 = publisher_ocean_instance.web3.eth.account.create().address
    # remove a trusted algorithm that does not belong to publisher_trusted_algorithms list
    new_publisher_trusted_algo_publishers = (
        compute_service.remove_publisher_trusted_algorithm_publisher(addr3)
    )
    assert len(new_publisher_trusted_algo_publishers) == 1


@pytest.mark.unit
def test_inexistent_removals():
    ddo_dict = get_sample_ddo_with_compute_service()
    del ddo_dict["services"][1]["compute"]["publisherTrustedAlgorithms"]
    ddo = Asset.from_dict(ddo_dict)
    compute_service = ddo.services[1]

    with pytest.raises(
        ValueError, match="Algorithm notadid is not in trusted algorithms"
    ):
        compute_service.remove_publisher_trusted_algorithm("notadid")

    ddo_dict = get_sample_ddo_with_compute_service()
    del ddo_dict["services"][1]["compute"]["publisherTrustedAlgorithmPublishers"]
    ddo = Asset.from_dict(ddo_dict)
    compute_service = ddo.services[1]

    with pytest.raises(
        ValueError, match="Publisher notadid is not in trusted algorithm publishers"
    ):
        compute_service.remove_publisher_trusted_algorithm_publisher("notadid")


@pytest.mark.unit
def test_utilitary_functions_for_trusted_algorithms(publisher_ocean_instance):
    """Tests adding/removing trusted algorithms in the DDO metadata."""
    algorithm_ddo = get_sample_algorithm_ddo(filename="ddo_algorithm2.json")
    algorithm_ddo.did = "did:op:123"
    algorithm_ddo_v2 = get_sample_algorithm_ddo(filename="ddo_algorithm2.json")
    algorithm_ddo_v2.did = "did:op:1234"
    algorithm_ddo_v3 = get_sample_algorithm_ddo(filename="ddo_algorithm2.json")
    algorithm_ddo_v3.did = "did:op:3333"

    ddo = Asset.from_dict(
        get_sample_ddo_with_compute_service("ddo_v4_with_compute_service2.json")
    )

    publisher_trusted_algorithms = [algorithm_ddo.generate_trusted_algorithms()]
    assert len(publisher_trusted_algorithms) == 1
    compute_service = ddo.services[1]
    assert compute_service.type == "compute"
    assert (
        compute_service.compute_values["publisherTrustedAlgorithms"]
        == publisher_trusted_algorithms
    )

    new_publisher_trusted_algorithms = compute_service.add_publisher_trusted_algorithm(
        algorithm_ddo_v2,
    )

    assert (
        new_publisher_trusted_algorithms is not None
    ), "Added a new trusted algorithm failed. The list is empty."
    assert len(new_publisher_trusted_algorithms) == 2

    new_publisher_trusted_algorithms = compute_service.add_publisher_trusted_algorithm(
        algorithm_ddo
    )
    assert new_publisher_trusted_algorithms is not None
    for trusted_algorithm in publisher_trusted_algorithms:
        assert (
            trusted_algorithm["did"] == algorithm_ddo.did
        ), "Added a different algorithm besides the existing ones."
    assert len(new_publisher_trusted_algorithms) == 2


@pytest.mark.unit
def test_add_trusted_algorithm_no_compute_service(publisher_ocean_instance):
    """Tests if the DDO has or not a compute service."""
    algorithm_ddo = get_sample_algorithm_ddo("ddo_algorithm2.json")
    algorithm_ddo.did = "did:op:0x666"

    ddo = Asset.from_dict(get_sample_ddo())
    access_service = ddo.services[0]
    assert access_service.type == "access"

    with pytest.raises(AssertionError, match="Service is not compute type"):
        access_service.add_publisher_trusted_algorithm(algorithm_ddo)
