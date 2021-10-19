#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import patch

import pytest
from ocean_lib.assets.did import DID
from ocean_lib.assets.trusted_algorithms import (
    add_publisher_trusted_algorithm,
    add_publisher_trusted_algorithm_publisher,
    create_publisher_trusted_algorithms,
    generate_trusted_algo_dict,
    remove_publisher_trusted_algorithm,
    remove_publisher_trusted_algorithm_publisher,
)
from ocean_lib.common.agreements.service_types import ServiceTypes
from tests.resources.ddo_helpers import (
    get_sample_algorithm_ddo,
    get_sample_ddo,
    get_sample_ddo_with_compute_service,
)


def test_utilitary_functions_for_trusted_algorithms(publisher_ocean_instance):
    """Tests adding/removing trusted algorithms in the DDO metadata."""
    algorithm_ddo = get_sample_algorithm_ddo()
    algorithm_ddo.did = DID.did({"ab": "b"})
    algorithm_ddo_v2 = get_sample_algorithm_ddo()
    algorithm_ddo_v2.did = DID.did({"a": "b"})
    algorithm_ddo_v3 = get_sample_algorithm_ddo()
    algorithm_ddo_v3.did = DID.did({"A": "B"})

    ddo = get_sample_ddo_with_compute_service()

    publisher_trusted_algorithms = create_publisher_trusted_algorithms(
        [algorithm_ddo], publisher_ocean_instance.config.metadata_cache_uri
    )
    assert len(publisher_trusted_algorithms) == 1
    compute_service = ddo.get_service(ServiceTypes.CLOUD_COMPUTE)
    compute_service.main["privacy"][
        "publisherTrustedAlgorithms"
    ] = publisher_trusted_algorithms

    with patch("ocean_lib.assets.trusted_algorithms.resolve_asset") as mock:
        mock.return_value = algorithm_ddo_v2
        # add a new trusted algorithm to the publisher_trusted_algorithms list
        new_publisher_trusted_algorithms = add_publisher_trusted_algorithm(
            ddo,
            algorithm_ddo_v2.did,
            publisher_ocean_instance.config.metadata_cache_uri,
        )

        assert (
            new_publisher_trusted_algorithms is not None
        ), "Added a new trusted algorithm failed. The list is empty."
        assert len(new_publisher_trusted_algorithms) == 2

    with patch("ocean_lib.assets.trusted_algorithms.resolve_asset") as mock:
        mock.return_value = algorithm_ddo
        # add an existing algorithm to publisher_trusted_algorithms list
        new_publisher_trusted_algorithms = add_publisher_trusted_algorithm(
            ddo, algorithm_ddo.did, publisher_ocean_instance.config.metadata_cache_uri
        )
        assert new_publisher_trusted_algorithms is not None
        for trusted_algorithm in publisher_trusted_algorithms:
            assert (
                trusted_algorithm["did"] == algorithm_ddo.did
            ), "Added a different algorithm besides the existing ones."
        assert len(new_publisher_trusted_algorithms) == 2

    # remove an existing algorithm to publisher_trusted_algorithms list
    new_publisher_trusted_algorithms = remove_publisher_trusted_algorithm(
        ddo, algorithm_ddo.did, publisher_ocean_instance.config.metadata_cache_uri
    )

    assert (
        new_publisher_trusted_algorithms is not None
    ), "Remove process of a trusted algorithm failed."
    assert len(new_publisher_trusted_algorithms) == 1

    # remove a trusted algorithm that does not belong to publisher_trusted_algorithms list
    new_publisher_trusted_algorithms = remove_publisher_trusted_algorithm(
        ddo, algorithm_ddo_v3.did, publisher_ocean_instance.config.metadata_cache_uri
    )
    assert len(new_publisher_trusted_algorithms) == 1


def test_add_trusted_algorithm_no_compute_service(publisher_ocean_instance):
    """Tests if the DDO has or not a compute service."""
    algorithm_ddo = get_sample_algorithm_ddo()
    algorithm_ddo.did = DID.did({"ab": "b"})

    ddo = get_sample_ddo()
    with pytest.raises(AssertionError):
        add_publisher_trusted_algorithm(
            ddo, algorithm_ddo.did, publisher_ocean_instance.config.metadata_cache_uri
        )


def test_fail_generate_trusted_algo_dict():
    """Tests if generate_trusted_algo_dict throws an AssertionError when all parameters are None."""
    with pytest.raises(TypeError):
        generate_trusted_algo_dict(None, None)


def test_utilitary_functions_for_trusted_algorithm_publishers(publisher_ocean_instance):
    """Tests adding/removing trusted algorithms in the DDO metadata."""
    ddo = get_sample_ddo_with_compute_service()
    compute_service = ddo.get_service(ServiceTypes.CLOUD_COMPUTE)
    compute_service.main["privacy"]["publisherTrustedAlgorithmPublishers"] = ["0xabc"]

    # add a new trusted algorithm to the publisher_trusted_algorithms list
    new_publisher_trusted_algo_publishers = add_publisher_trusted_algorithm_publisher(
        ddo, "0x123", publisher_ocean_instance.config.metadata_cache_uri
    )

    assert (
        new_publisher_trusted_algo_publishers is not None
    ), "Added a new trusted algorithm failed. The list is empty."
    assert len(new_publisher_trusted_algo_publishers) == 2

    # add an existing algorithm to publisher_trusted_algorithms list
    new_publisher_trusted_algo_publishers = add_publisher_trusted_algorithm_publisher(
        ddo, "0xAbC", publisher_ocean_instance.config.metadata_cache_uri
    )
    assert len(new_publisher_trusted_algo_publishers) == 2

    # remove an existing algorithm to publisher_trusted_algorithms list
    new_publisher_trusted_algo_publishers = (
        remove_publisher_trusted_algorithm_publisher(
            ddo, "0xABC", publisher_ocean_instance.config.metadata_cache_uri
        )
    )

    assert len(new_publisher_trusted_algo_publishers) == 1

    # remove a trusted algorithm that does not belong to publisher_trusted_algorithms list
    new_publisher_trusted_algo_publishers = (
        remove_publisher_trusted_algorithm_publisher(
            ddo, "0xaaaa", publisher_ocean_instance.config.metadata_cache_uri
        )
    )
    assert len(new_publisher_trusted_algo_publishers) == 1
