#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.common.agreements.service_types import ServiceTypes
from tests.resources.ddo_helpers import (
    get_registered_algorithm_ddo,
    get_registered_ddo_with_compute_service,
    wait_for_ddo,
)
from tests.resources.helper_functions import get_publisher_wallet


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


def test_trusted_algorithms(publisher_ocean_instance, config):
    """Tests if the trusted algorithms list is returned correctly."""
    publisher = get_publisher_wallet()
    provider_uri = config.provider_url

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo.did)
    assert algorithm_ddo is not None

    ddo = get_registered_ddo_with_compute_service(
        publisher_ocean_instance,
        publisher,
        provider_uri=provider_uri,
        trusted_algorithms=[algorithm_ddo.did],
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
