#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.utils.utilities import get_timestamp
from tests.resources.helper_functions import get_publisher_wallet


def test_create_access_service(publisher_ocean_instance):
    """Tests that an access service is correctly created."""
    service = publisher_ocean_instance.services.create_access_service(
        {"a": 1}, "service_endpoint"
    )
    assert service[0] == "access"
    assert service[1]["attributes"] == {"a": 1}
    assert service[1]["serviceEndpoint"] == "service_endpoint"


def test_create_compute_service(publisher_ocean_instance):
    """Tests that a compute service is correctly created.

    Includes cluster, container and server creation."""
    ocn_compute = publisher_ocean_instance.compute

    cluster = ocn_compute.build_cluster_attributes("kubernetes", "/cluster/url")
    container = ocn_compute.build_container_attributes(
        "tensorflow/tensorflow",
        "latest",
        "sha256:cb57ecfa6ebbefd8ffc7f75c0f00e57a7fa739578a429b6f72a0df19315deadc",
    )
    server = ocn_compute.build_server_attributes(
        "1", "xlsize", "16", "0", "128gb", "160gb", 86400
    )
    provider_attributes = ocn_compute.build_service_provider_attributes(
        "Azure",
        "some description of the compute server instance",
        cluster,
        [container],
        [server],
    )
    attributes = ocn_compute.create_compute_service_attributes(
        3600 * 24, get_publisher_wallet().address, get_timestamp(), provider_attributes
    )
    service = publisher_ocean_instance.services.create_compute_service(
        attributes, "http://provider.com:8030"
    )
    assert isinstance(service, tuple) and len(service) == 2
    assert service[0] == ServiceTypes.CLOUD_COMPUTE
    assert isinstance(service[1], dict)
    assert service[1]["attributes"] == attributes
    assert service[1]["serviceEndpoint"] == "http://provider.com:8030"
