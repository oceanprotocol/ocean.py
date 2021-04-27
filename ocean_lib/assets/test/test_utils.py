#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.assets.utils import (
    add_publisher_trusted_algorithm,
    create_publisher_trusted_algorithms,
    remove_publisher_trusted_algorithm,
    generate_trusted_algo_dict,
)
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.common.ddo.ddo import DDO
from tests.resources.ddo_helpers import (
    get_registered_algorithm_ddo,
    get_registered_ddo_with_compute_service,
    wait_for_ddo,
    get_resource_path,
)
from tests.resources.helper_functions import get_publisher_wallet


def test_utilitary_functions_for_trusted_algorithms(publisher_ocean_instance):
    """Tests adding/removing trusted algorithms in the DDO metadata."""
    publisher = get_publisher_wallet()

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo.did)
    assert algorithm_ddo is not None

    algorithm_ddo_v2 = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo_v2.did)
    assert algorithm_ddo_v2 is not None

    algorithm_ddo_v3 = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo_v3.did)
    assert algorithm_ddo_v3 is not None

    ddo = get_registered_ddo_with_compute_service(
        publisher_ocean_instance, publisher, trusted_algorithms=[algorithm_ddo.did]
    )
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert ddo is not None

    publisher_trusted_algorithms = create_publisher_trusted_algorithms(
        [algorithm_ddo.did], publisher_ocean_instance.config.metadata_cache_uri
    )

    # add a new trusted algorithm to the publisher_trusted_algorithms list
    new_publisher_trusted_algorithms = add_publisher_trusted_algorithm(
        ddo.did,
        algorithm_ddo_v2.did,
        publisher_ocean_instance.config.metadata_cache_uri,
    )

    assert new_publisher_trusted_algorithms is not None
    assert len(new_publisher_trusted_algorithms) > len(publisher_trusted_algorithms)

    # add an existing algorithm to publisher_trusted_algorithms list
    new_publisher_trusted_algorithms = add_publisher_trusted_algorithm(
        ddo.did, algorithm_ddo.did, publisher_ocean_instance.config.metadata_cache_uri
    )
    assert new_publisher_trusted_algorithms is not None
    for _, trusted_algorithm in enumerate(publisher_trusted_algorithms):
        assert trusted_algorithm["did"] == algorithm_ddo.did
    assert len(new_publisher_trusted_algorithms) == len(publisher_trusted_algorithms)

    # remove an existing algorithm to publisher_trusted_algorithms list
    new_publisher_trusted_algorithms = remove_publisher_trusted_algorithm(
        ddo.did, algorithm_ddo.did, publisher_ocean_instance.config.metadata_cache_uri
    )

    assert new_publisher_trusted_algorithms is not None
    assert len(new_publisher_trusted_algorithms) < len(publisher_trusted_algorithms)

    # remove a trusted algorithm that does not belong to publisher_trusted_algorithms list
    new_publisher_trusted_algorithms = remove_publisher_trusted_algorithm(
        ddo.did,
        algorithm_ddo_v3.did,
        publisher_ocean_instance.config.metadata_cache_uri,
    )

    assert new_publisher_trusted_algorithms is not None
    for trusted_algorithm in publisher_trusted_algorithms:
        assert trusted_algorithm["did"] != algorithm_ddo_v3.did
    assert len(new_publisher_trusted_algorithms) == len(publisher_trusted_algorithms)


def test_add_trusted_algorithm_no_compute_service(publisher_ocean_instance, metadata):
    """Tests if the DDO has or not a compute service."""
    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo.did)
    assert algorithm_ddo is not None

    ddo = publisher_ocean_instance.assets.create(metadata_copy, publisher)
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert ddo is not None

    create_publisher_trusted_algorithms(
        [algorithm_ddo.did], publisher_ocean_instance.config.metadata_cache_uri
    )

    with pytest.raises(AssertionError):
        add_publisher_trusted_algorithm(
            ddo.did,
            algorithm_ddo.did,
            publisher_ocean_instance.config.metadata_cache_uri,
        )


def test_fail_generate_trusted_algo_dict():
    """Tests if all the parameters for generating a trusted algorithm dict are None and if teh scope of this function
    throws an AssertionError."""
    try:
        _ = generate_trusted_algo_dict(None, None, None)
    except AssertionError as err:
        proposed_err = AssertionError(
            "Either ddo, either did and metadata_cache_uri are None."
        )
        assert isinstance(err, type(proposed_err))
        assert err.args == proposed_err.args
