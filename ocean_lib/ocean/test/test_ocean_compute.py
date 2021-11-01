#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from datetime import datetime
from unittest.mock import patch

from ocean_lib.assets.trusted_algorithms import create_publisher_trusted_algorithms
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.ocean.ocean_compute import OceanCompute
from tests.resources.ddo_helpers import (
    get_sample_algorithm_ddo,
    get_sample_ddo_with_compute_service,
)
from tests.resources.helper_functions import get_publisher_wallet


def test_build_cluster_attributes(config):
    data_provider = DataServiceProvider
    compute = OceanCompute(config, data_provider=data_provider)
    cluster_dict = compute.build_cluster_attributes(
        "Kubernetes", "http://10.0.0.17/my_cluster"
    )
    expected_cluster_dict = {"type": "Kubernetes", "url": "http://10.0.0.17/my_cluster"}
    assert cluster_dict, "Cluster dictionary is None."
    assert isinstance(cluster_dict, dict), "The cluster is not a dict."
    assert (
        cluster_dict == expected_cluster_dict
    ), "The cluster values are different from the expected ones."


def test_build_container_attributes(config):
    data_provider = DataServiceProvider
    compute = OceanCompute(config, data_provider=data_provider)
    container_dict = compute.build_container_attributes(
        "node", "best_tag", "entrypoint.exe"
    )
    expected_container_dict = {
        "image": "node",
        "tag": "best_tag",
        "entrypoint": "entrypoint.exe",
    }
    assert container_dict, "Container dictionary is None."
    assert isinstance(container_dict, dict), "The container is not a dict."
    assert (
        container_dict == expected_container_dict
    ), "The container values are different from the expected ones."


def test_build_server_attributes(config):
    data_provider = DataServiceProvider
    compute = OceanCompute(config, data_provider=data_provider)
    server_dict = compute.build_server_attributes(
        "test_server_id_123", "test_server_type", 4, 4, "20", "20", 30
    )
    expected_server_dict = {
        "serverId": "test_server_id_123",
        "serverType": "test_server_type",
        "cpu": 4,
        "gpu": 4,
        "memory": "20",
        "disk": "20",
        "maxExecutionTime": 30,
    }
    assert server_dict, "Server dictionary is None."
    assert isinstance(server_dict, dict), "The server is not a dict."
    assert (
        server_dict == expected_server_dict
    ), "The server values are different from the expected ones."


def test_build_service_provider_attributes(config):
    data_provider = DataServiceProvider
    compute = OceanCompute(config=config, data_provider=data_provider)

    cluster_dict = compute.build_cluster_attributes(
        "Kubernetes", "http://10.0.0.17/my_cluster"
    )
    expected_cluster_dict = {"type": "Kubernetes", "url": "http://10.0.0.17/my_cluster"}
    assert cluster_dict, "Cluster dictionary is None."
    assert isinstance(cluster_dict, dict), "The cluster is not a dict."
    assert (
        cluster_dict == expected_cluster_dict
    ), "The cluster values are different from the expected ones."

    container_dict = compute.build_container_attributes(
        "node", "best_tag", "entrypoint.exe"
    )
    expected_container_dict = {
        "image": "node",
        "tag": "best_tag",
        "entrypoint": "entrypoint.exe",
    }
    assert container_dict, "Container dictionary is None."
    assert isinstance(container_dict, dict), "The container is not a dict."
    assert (
        container_dict == expected_container_dict
    ), "The container values are different from the expected ones."

    server_dict = compute.build_server_attributes(
        "test_server_id_123", "test_server_type", 4, 4, "20", "20", 30
    )
    expected_server_dict = {
        "serverId": "test_server_id_123",
        "serverType": "test_server_type",
        "cpu": 4,
        "gpu": 4,
        "memory": "20",
        "disk": "20",
        "maxExecutionTime": 30,
    }
    assert server_dict, "Server dictionary is None."
    assert isinstance(server_dict, dict), "The server is not a dict."
    assert (
        server_dict == expected_server_dict
    ), "The server values are different from the expected ones."

    service_provider_dict = compute.build_service_provider_attributes(
        "My Provider", "Unit testing", cluster_dict, container_dict, server_dict
    )
    expected_service_provider_dict = {
        "type": "My Provider",
        "description": "Unit testing",
        "environment": {
            "cluster": cluster_dict,
            "supportedContainers": container_dict,
            "supportedServers": server_dict,
        },
    }
    assert service_provider_dict, "Provider server is None."
    assert isinstance(service_provider_dict, dict), "Provider server is not a dict."
    assert (
        service_provider_dict == expected_service_provider_dict
    ), "The service provider is not the expected one."


def test_build_service_privacy_attributes(publisher_ocean_instance):
    data_provider = DataServiceProvider
    compute = OceanCompute(
        config=publisher_ocean_instance.config, data_provider=data_provider
    )

    algorithm_ddo = get_sample_algorithm_ddo()

    with patch("ocean_lib.assets.trusted_algorithms.resolve_asset") as mock:
        mock.return_value = algorithm_ddo
        privacy_dict = compute.build_service_privacy_attributes(
            trusted_algorithms=[algorithm_ddo.did],
            metadata_cache_uri=publisher_ocean_instance.config.metadata_cache_uri,
            allow_raw_algorithm=True,
            allow_all_published_algorithms=True,
            allow_network_access=True,
        )

        expected_privacy_dict = {
            "allowRawAlgorithm": True,
            "allowAllPublishedAlgorithms": True,
            "publisherTrustedAlgorithms": create_publisher_trusted_algorithms(
                [algorithm_ddo.did], publisher_ocean_instance.config.metadata_cache_uri
            ),
            "allowNetworkAccess": True,
        }

    assert privacy_dict, "Privacy dictionary is None."
    assert isinstance(
        privacy_dict, dict
    ), "Privacy attributes do not form a dictionary."
    assert (
        privacy_dict == expected_privacy_dict
    ), "The privacy dict is not the expected one."


def test_build_service_privacy_attributes_no_trusted_algos(config):
    data_provider = DataServiceProvider
    compute = OceanCompute(config=config, data_provider=data_provider)
    privacy_dict = compute.build_service_privacy_attributes()
    expected_privacy_dict = {
        "allowRawAlgorithm": False,
        "allowAllPublishedAlgorithms": False,
        "publisherTrustedAlgorithms": [],
        "allowNetworkAccess": False,
    }
    assert privacy_dict
    assert isinstance(privacy_dict, dict)
    assert (
        privacy_dict == expected_privacy_dict
    ), "The privacy dict is not the expected one."


def test_create_compute_service_attributes(publisher_ocean_instance):
    publisher = get_publisher_wallet()
    data_provider = DataServiceProvider
    config = publisher_ocean_instance.config
    compute = OceanCompute(config=config, data_provider=data_provider)

    algorithm_ddo = get_sample_algorithm_ddo()

    with patch("ocean_lib.assets.trusted_algorithms.resolve_asset") as mock:
        mock.return_value = algorithm_ddo
        privacy_dict = compute.build_service_privacy_attributes(
            trusted_algorithms=[algorithm_ddo.did],
            metadata_cache_uri=config.metadata_cache_uri,
            allow_raw_algorithm=True,
            allow_all_published_algorithms=True,
            allow_network_access=True,
        )

        expected_privacy_dict = {
            "allowRawAlgorithm": True,
            "allowAllPublishedAlgorithms": True,
            "publisherTrustedAlgorithms": create_publisher_trusted_algorithms(
                [algorithm_ddo.did], config.metadata_cache_uri
            ),
            "allowNetworkAccess": True,
        }

    assert privacy_dict, "Privacy dictionary is None."
    assert isinstance(
        privacy_dict, dict
    ), "Privacy attributes do not form a dictionary."
    assert (
        privacy_dict == expected_privacy_dict
    ), "The privacy dict is not the expected one."

    cluster_dict = compute.build_cluster_attributes(
        "Kubernetes", "http://10.0.0.17/my_cluster"
    )
    expected_cluster_dict = {"type": "Kubernetes", "url": "http://10.0.0.17/my_cluster"}
    assert cluster_dict, "Cluster dictionary is None."
    assert isinstance(cluster_dict, dict), "The cluster is not a dict."
    assert (
        cluster_dict == expected_cluster_dict
    ), "The cluster values are different from the expected ones."

    container_dict = compute.build_container_attributes(
        "node", "best_tag", "entrypoint.exe"
    )
    expected_container_dict = {
        "image": "node",
        "tag": "best_tag",
        "entrypoint": "entrypoint.exe",
    }
    assert container_dict, "Container dictionary is None."
    assert isinstance(container_dict, dict), "The container is not a dict."
    assert (
        container_dict == expected_container_dict
    ), "The container values are different from the expected ones."

    server_dict = compute.build_server_attributes(
        "test_server_id_123", "test_server_type", 4, 4, "20", "20", 30
    )
    expected_server_dict = {
        "serverId": "test_server_id_123",
        "serverType": "test_server_type",
        "cpu": 4,
        "gpu": 4,
        "memory": "20",
        "disk": "20",
        "maxExecutionTime": 30,
    }
    assert server_dict, "Server dictionary is None."
    assert isinstance(server_dict, dict), "The server is not a dict."
    assert (
        server_dict == expected_server_dict
    ), "The server values are different from the expected ones."

    service_provider_dict = compute.build_service_provider_attributes(
        "My Provider", "Unit testing", cluster_dict, container_dict, server_dict
    )
    expected_service_provider_dict = {
        "type": "My Provider",
        "description": "Unit testing",
        "environment": {
            "cluster": cluster_dict,
            "supportedContainers": container_dict,
            "supportedServers": server_dict,
        },
    }
    assert service_provider_dict, "Provider server is None."
    assert isinstance(service_provider_dict, dict), "Provider server is not a dict."
    assert (
        service_provider_dict == expected_service_provider_dict
    ), "The service provider is not the expected one."

    compute_attributes = compute.create_compute_service_attributes(
        30,
        publisher.address,
        (datetime.utcnow().replace(microsecond=0).isoformat() + "Z"),
        service_provider_dict,
        privacy_dict,
    )

    expected_compute_attributes = {
        "main": {
            "name": "dataAssetComputingServiceAgreement",
            "creator": publisher.address,
            "datePublished": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "cost": 1.0,
            "timeout": 30,
            "provider": service_provider_dict,
            "privacy": privacy_dict,
        }
    }

    assert compute_attributes, "Compute attributes do not exist."
    assert isinstance(compute_attributes, dict), "compute_attributes is not a dict."
    assert (
        compute_attributes == expected_compute_attributes
    ), "The compute attributes are not the expected ones."


def test_get_service_endpoint():
    data_provider = DataServiceProvider
    options_dict = {"resources": {"provider.url": "http://localhost:8030"}}
    config = Config(options_dict=options_dict)
    compute = OceanCompute(config, data_provider)

    ddo = get_sample_ddo_with_compute_service()
    compute_service = ddo.get_service(ServiceTypes.CLOUD_COMPUTE)
    compute_service.service_endpoint = "http://localhost:8030"

    with patch("ocean_lib.ocean.ocean_compute.resolve_asset") as mock:
        mock.return_value = ddo
        service_endpoint = compute._get_service_endpoint(ddo.did)

    assert service_endpoint, "The service endpoint is None."
    assert isinstance(service_endpoint, tuple), "The service endpoint is not a tuple."
    assert (
        service_endpoint[0] == "GET"
    ), "The http method of compute status job must be GET."
    assert (
        service_endpoint[1]
        == data_provider.build_compute_endpoint(config.provider_url)[1]
    ), "Different URLs for compute status job."
