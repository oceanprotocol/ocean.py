#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from tests.resources.ddo_helpers import (
    get_registered_algorithm_ddo,
    wait_for_ddo,
    get_registered_ddo_with_compute_service,
)
from tests.resources.helper_functions import get_publisher_wallet
from ocean_lib.assets.utils import (
    create_publisher_trusted_algorithms,
    add_publisher_trusted_algorithm,
    remove_publisher_trusted_algorithm,
)


def test_add_trusted_algorithm(publisher_ocean_instance):
    """Tests adding trusted algorithms in the DDO metadata."""
    publisher = get_publisher_wallet()

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    _ = publisher_ocean_instance.assets.resolve(algorithm_ddo.did)
    assert algorithm_ddo is not None

    ddo = get_registered_ddo_with_compute_service(
        publisher_ocean_instance,
        publisher,
        trusted_algorithms=[algorithm_ddo.did],
    )
    _ = publisher_ocean_instance.assets.resolve(ddo.did)
    assert ddo is not None

    publisher_trusted_algorithms = create_publisher_trusted_algorithms(
        [algorithm_ddo.did], publisher_ocean_instance.config.aquarius_url
    )

    new_publisher_trusted_algorithms = add_publisher_trusted_algorithm(
        ddo.did, algorithm_ddo.did, publisher_ocean_instance.config.aquarius_url
    )

    assert new_publisher_trusted_algorithms is not None
    assert len(new_publisher_trusted_algorithms) >= len(publisher_trusted_algorithms)


def test_add_trusted_algorithm_no_compute_service(publisher_ocean_instance, metadata):
    """Handles if the DDO has or not a compute service."""
    publisher = get_publisher_wallet()

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo.did)
    assert algorithm_ddo is not None

    publisher = get_publisher_wallet()
    metadata_copy = metadata.copy()

    ddo = publisher_ocean_instance.assets.create(metadata_copy, publisher)
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert ddo is not None

    create_publisher_trusted_algorithms(
        [algorithm_ddo.did], publisher_ocean_instance.config.aquarius_url
    )

    with pytest.raises(AssertionError):
        add_publisher_trusted_algorithm(
            ddo.did, algorithm_ddo.did, publisher_ocean_instance.config.aquarius_url
        )


def test_remove_trusted_algorithm(publisher_ocean_instance):
    """Tests removing trusted algorithms in the DDO metadata."""
    publisher = get_publisher_wallet()

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    _ = publisher_ocean_instance.assets.resolve(algorithm_ddo.did)
    assert algorithm_ddo is not None

    ddo = get_registered_ddo_with_compute_service(
        publisher_ocean_instance,
        publisher,
        trusted_algorithms=[algorithm_ddo.did],
    )
    _ = publisher_ocean_instance.assets.resolve(ddo.did)
    assert ddo is not None

    publisher_trusted_algorithms = create_publisher_trusted_algorithms(
        [algorithm_ddo.did], publisher_ocean_instance.config.aquarius_url
    )

    new_publisher_trusted_algorithms = remove_publisher_trusted_algorithm(
        ddo.did, algorithm_ddo.did, publisher_ocean_instance.config.aquarius_url
    )

    assert new_publisher_trusted_algorithms is not None
    assert len(new_publisher_trusted_algorithms) <= len(publisher_trusted_algorithms)
