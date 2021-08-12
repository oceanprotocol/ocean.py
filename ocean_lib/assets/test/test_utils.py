#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.assets.utils import (
    add_publisher_trusted_algorithm,
    add_publisher_trusted_algorithm_publisher,
    create_publisher_trusted_algorithms,
    generate_trusted_algo_dict,
    remove_publisher_trusted_algorithm,
    remove_publisher_trusted_algorithm_publisher,
)
from tests.resources.ddo_helpers import (
    get_registered_algorithm_ddo,
    get_registered_ddo_with_compute_service,
    wait_for_ddo,
)
from tests.resources.helper_functions import get_publisher_wallet


def test_utilitary_functions_for_trusted_algorithms(publisher_ocean_instance):
    """Tests adding/removing trusted algorithms in the DDO metadata."""
    publisher = get_publisher_wallet()

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo.did)
    assert algorithm_ddo is not None, "Algorithm DDO is not found in cache."

    algorithm_ddo_v2 = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo_v2.did)
    assert algorithm_ddo_v2 is not None, "Algorithm DDO is not found in cache."

    algorithm_ddo_v3 = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo_v3.did)
    assert algorithm_ddo_v3 is not None, "Algorithm DDO is not found in cache."

    ddo = get_registered_ddo_with_compute_service(
        publisher_ocean_instance, publisher, trusted_algorithms=[algorithm_ddo.did]
    )
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert ddo is not None, "DDO is not found in cache."

    publisher_trusted_algorithms = create_publisher_trusted_algorithms(
        [algorithm_ddo.did], publisher_ocean_instance.config.metadata_cache_uri
    )
    assert len(publisher_trusted_algorithms) == 1

    # add a new trusted algorithm to the publisher_trusted_algorithms list
    new_publisher_trusted_algorithms = add_publisher_trusted_algorithm(
        ddo, algorithm_ddo_v2.did, publisher_ocean_instance.config.metadata_cache_uri
    )

    assert (
        new_publisher_trusted_algorithms is not None
    ), "Added a new trusted algorithm failed. The list is empty."
    assert len(new_publisher_trusted_algorithms) == 2

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


def test_add_trusted_algorithm_no_compute_service(publisher_ocean_instance, metadata):
    """Tests if the DDO has or not a compute service."""
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo.did)
    assert algorithm_ddo is not None, "Algorithm DDO is not found in cache."

    ddo = publisher_ocean_instance.assets.create(metadata_copy, publisher)
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert ddo is not None, "DDO is not found in cache."

    create_publisher_trusted_algorithms(
        [algorithm_ddo.did], publisher_ocean_instance.config.metadata_cache_uri
    )

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
    publisher = get_publisher_wallet()
    ddo = get_registered_ddo_with_compute_service(
        publisher_ocean_instance, publisher, trusted_algorithm_publishers=["0xabc"]
    )
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert ddo is not None, "DDO is not found in cache."

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
