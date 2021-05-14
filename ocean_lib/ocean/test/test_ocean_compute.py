#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
from datetime import datetime

from ocean_lib.assets.utils import create_checksum, create_publisher_trusted_algorithms
from ocean_lib.config import Config
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.ocean_compute import OceanCompute
from tests.resources.ddo_helpers import (
    get_registered_algorithm_ddo,
    wait_for_ddo,
    get_registered_ddo_with_compute_service,
)
from tests.resources.helper_functions import get_publisher_wallet


def test_build_cluster_attributes():
    data_provider = DataServiceProvider()
    config = Ocean.config
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


def test_build_container_attributes():
    data_provider = DataServiceProvider()
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)
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


def test_build_server_attributes():
    data_provider = DataServiceProvider()
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)
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


def test_build_service_provider_attributes():
    data_provider = DataServiceProvider()
    config = Ocean.config
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
    publisher = get_publisher_wallet()
    data_provider = DataServiceProvider()
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo.did)
    assert algorithm_ddo is not None

    privacy_dict = compute.build_service_privacy_attributes(
        trusted_algorithms=[algorithm_ddo.did],
        allow_raw_algorithm=True,
        allow_all_published_algorithms=True,
        allow_network_access=True,
    )

    expected_privacy_dict = {
        "allowRawAlgorithm": True,
        "allowAllPublishedAlgorithms": True,
        "publisherTrustedAlgorithms": create_publisher_trusted_algorithms(
            [algorithm_ddo.did], ConfigProvider.get_config().metadata_cache_uri
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


def test_build_service_privacy_attributes_no_trusted_algos():
    data_provider = DataServiceProvider()
    config = Ocean.config
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
    data_provider = DataServiceProvider()
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo.did)
    assert algorithm_ddo is not None

    privacy_dict = compute.build_service_privacy_attributes(
        trusted_algorithms=[algorithm_ddo.did],
        allow_raw_algorithm=True,
        allow_all_published_algorithms=True,
        allow_network_access=True,
    )

    expected_privacy_dict = {
        "allowRawAlgorithm": True,
        "allowAllPublishedAlgorithms": True,
        "publisherTrustedAlgorithms": create_publisher_trusted_algorithms(
            [algorithm_ddo.did], ConfigProvider.get_config().metadata_cache_uri
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


def test_create_compute_service_descriptor(publisher_ocean_instance):
    publisher = get_publisher_wallet()
    data_provider = DataServiceProvider()
    config = Config()
    compute = OceanCompute(config=config, data_provider=data_provider)

    algorithm_ddo = get_registered_algorithm_ddo(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, algorithm_ddo.did)
    assert algorithm_ddo is not None

    privacy_dict = compute.build_service_privacy_attributes(
        trusted_algorithms=[algorithm_ddo.did],
        allow_raw_algorithm=True,
        allow_all_published_algorithms=True,
        allow_network_access=True,
    )

    expected_privacy_dict = {
        "allowRawAlgorithm": True,
        "allowAllPublishedAlgorithms": True,
        "publisherTrustedAlgorithms": create_publisher_trusted_algorithms(
            [algorithm_ddo.did], ConfigProvider.get_config().metadata_cache_uri
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
    assert compute_attributes, "Compute attributes do not exist."
    assert isinstance(compute_attributes, dict), "compute_attributes is not a dict."

    compute_descriptor = compute.create_compute_service_descriptor(compute_attributes)
    assert compute_descriptor, "Compute descriptor is None."
    assert isinstance(compute_descriptor, tuple), "Compute descriptor is not a tuple."
    assert compute_descriptor[0] == "compute", "Type is not compute."
    assert (
        compute_descriptor[1]["attributes"] == compute_attributes
    ), "compute_attributes do not match compute descriptor ones."


def test_get_service_endpoint(publisher_ocean_instance):
    publisher = get_publisher_wallet()
    data_provider = DataServiceProvider()
    options_dict = {"resources": {"provider.url": "http://localhost:8030"}}
    config = Config(options_dict=options_dict)
    compute = OceanCompute(config, data_provider)

    ddo = get_registered_ddo_with_compute_service(publisher_ocean_instance, publisher)
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert ddo is not None, "DDO is not found in cache."

    service_endpoint = compute._get_service_endpoint(ddo.did)
    assert service_endpoint, "The service endpoint is None."
    assert isinstance(service_endpoint, tuple), "The service endpoint is not a tuple."
    assert (
        service_endpoint[0] == "GET"
    ), "The http method of compute status job must be GET."
    assert (
        service_endpoint[1] == data_provider.build_compute_endpoint()[1]
    ), "Different URLs for compute status job."
