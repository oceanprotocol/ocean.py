#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
from datetime import datetime

from ocean_lib.assets.utils import create_checksum
from ocean_lib.config import Config
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
    assert cluster_dict, "Cluster dictionary is None."
    assert isinstance(cluster_dict, dict), "The cluster is not a dict."
    assert (
        "type" in cluster_dict and cluster_dict["type"] == "Kubernetes"
    ), "Type does not belong to the attributes."
    assert (
        "url" in cluster_dict and cluster_dict["url"] == "http://10.0.0.17/my_cluster"
    ), "Url does not belong to the attributes."


def test_build_container_attributes():
    data_provider = DataServiceProvider()
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)
    container_dict = compute.build_container_attributes(
        "node", "best_tag", "entrypoint.exe"
    )
    assert container_dict, "Container dictionary is None."
    assert isinstance(container_dict, dict), "The container is not a dict."
    assert (
        "image" in container_dict and container_dict["image"] == "node"
    ), "Image does not belong to the attributes."
    assert (
        "tag" in container_dict and container_dict["tag"] == "best_tag"
    ), "Tag does not belong to the attributes."
    assert (
        "entrypoint" in container_dict
        and container_dict["entrypoint"] == "entrypoint.exe"
    ), "Entrypoint does not belong to the attributes."


def test_build_server_attributes():
    data_provider = DataServiceProvider()
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)
    server_dict = compute.build_server_attributes(
        "test_server_id_123", "test_server_type", 4, 4, "20", "20", 30
    )
    assert server_dict, "Server dictionary is None."
    assert isinstance(server_dict, dict), "The server is not a dict."
    assert (
        "serverId" in server_dict and server_dict["serverId"] == "test_server_id_123"
    ), "serverId does not belong to the attributes."
    assert (
        "serverType" in server_dict and server_dict["serverType"] == "test_server_type"
    ), "serverType does not belong to the attributes."
    assert (
        "cpu" in server_dict and server_dict["cpu"] == 4
    ), "CPU does not belong to the attributes."
    assert (
        "gpu" in server_dict and server_dict["gpu"] == 4
    ), "GPU does not belong to the attributes."
    assert (
        "memory" in server_dict and server_dict["memory"] == "20"
    ), "Memory does not belong to the attributes."
    assert (
        "disk" in server_dict and server_dict["disk"] == "20"
    ), "Disk does not belong to the attributes."
    assert (
        "maxExecutionTime" in server_dict and server_dict["maxExecutionTime"] == 30
    ), "Execution time does not exist."


def test_build_service_provider_attributes():
    data_provider = DataServiceProvider()
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)

    cluster_dict = compute.build_cluster_attributes(
        "Kubernetes", "http://10.0.0.17/my_cluster"
    )
    assert cluster_dict, "Cluster dictionary is None."
    assert isinstance(cluster_dict, dict), "The cluster is not a dict."
    assert (
        "type" in cluster_dict and cluster_dict["type"] == "Kubernetes"
    ), "Type does not belong to the attributes."
    assert (
        "url" in cluster_dict and cluster_dict["url"] == "http://10.0.0.17/my_cluster"
    ), "Url does not belong to the attributes."

    container_dict = compute.build_container_attributes(
        "node", "best_tag", "entrypoint.exe"
    )
    assert container_dict, "Container dictionary is None."
    assert isinstance(container_dict, dict), "The container is not a dict."
    assert (
        "image" in container_dict and container_dict["image"] == "node"
    ), "Image does not belong to the attributes."
    assert (
        "tag" in container_dict and container_dict["tag"] == "best_tag"
    ), "Tag does not belong to the attributes."
    assert (
        "entrypoint" in container_dict
        and container_dict["entrypoint"] == "entrypoint.exe"
    ), "Entrypoint does not belong to the attributes."

    server_dict = compute.build_server_attributes(
        "test_server_id_123", "test_server_type", 4, 4, "20", "20", 30
    )
    assert server_dict, "Server dictionary is None."
    assert isinstance(server_dict, dict), "The server is not a dict."
    assert (
        "serverId" in server_dict and server_dict["serverId"] == "test_server_id_123"
    ), "serverId does not belong to the attributes."
    assert (
        "serverType" in server_dict and server_dict["serverType"] == "test_server_type"
    ), "serverType does not belong to the attributes."
    assert (
        "cpu" in server_dict and server_dict["cpu"] == 4
    ), "CPU does not belong to the attributes."
    assert (
        "gpu" in server_dict and server_dict["gpu"] == 4
    ), "GPU does not belong to the attributes."
    assert (
        "memory" in server_dict and server_dict["memory"] == "20"
    ), "Memory does not belong to the attributes."
    assert (
        "disk" in server_dict and server_dict["disk"] == "20"
    ), "Disk does not belong to the attributes."
    assert (
        "maxExecutionTime" in server_dict and server_dict["maxExecutionTime"] == 30
    ), "Execution time does not exist."

    service_provider_dict = compute.build_service_provider_attributes(
        "My Provider", "Unit testing", cluster_dict, container_dict, server_dict
    )
    assert service_provider_dict, "Provider server is None."
    assert isinstance(service_provider_dict, dict), "Provider server is not a dict."
    assert (
        "type" in service_provider_dict
        and service_provider_dict["type"] == "My Provider"
    ), "Type does not exist in provider server dictionary."
    assert (
        "description" in service_provider_dict
        and service_provider_dict["description"] == "Unit testing"
    ), "Description does not belong to the attributes."
    assert (
        "environment" in service_provider_dict
    ), "Environment does not belong to the attributes."
    assert (
        "cluster" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["cluster"] == cluster_dict
    ), "Cluster does not belong to the environment attributes."
    assert (
        "supportedContainers" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["supportedContainers"]
        == container_dict
    ), "Container does not belong to the environment attributes."
    assert (
        "supportedServers" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["supportedServers"] == server_dict
    ), "Server does not belong to the environment attributes."


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

    assert privacy_dict, "Privacy dictionary is None."
    assert isinstance(
        privacy_dict, dict
    ), "Privacy attributes do not form a dictionary."
    assert (
        "allowRawAlgorithm" in privacy_dict
        and privacy_dict["allowRawAlgorithm"] == True
    ), "AllowRawAlgorithm does not belong to the attributes."
    assert (
        "allowAllPublishedAlgorithms" in privacy_dict
        and privacy_dict["allowAllPublishedAlgorithms"] == True
    ), "AllowAllPublishedAlgorithms does not belong to the attributes."
    assert (
        "publisherTrustedAlgorithms" in privacy_dict
    ), "Publisher trusted algorithms do not exist in privacy dict."
    assert (
        privacy_dict["publisherTrustedAlgorithms"][0]["did"]
        and privacy_dict["publisherTrustedAlgorithms"][0]["did"] == algorithm_ddo.did
    ), "The did of the algorithm DDO does not exist."
    assert privacy_dict["publisherTrustedAlgorithms"][0][
        "filesChecksum"
    ] and privacy_dict["publisherTrustedAlgorithms"][0][
        "filesChecksum"
    ] == create_checksum(
        algorithm_ddo.metadata["encryptedFiles"]
        + json.dumps(algorithm_ddo.metadata["main"]["files"], separators=(",", ":"))
    ), "The filesChecksum does not exist."
    assert privacy_dict["publisherTrustedAlgorithms"][0][
        "containerSectionChecksum"
    ] and privacy_dict["publisherTrustedAlgorithms"][0][
        "containerSectionChecksum"
    ] == create_checksum(
        json.dumps(
            algorithm_ddo.metadata["main"]["algorithm"]["container"],
            separators=(",", ":"),
        )
    ), "The cointainerSectionChecksum does not exist."
    assert (
        "allowNetworkAccess" in privacy_dict
        and privacy_dict["allowNetworkAccess"] == True
    ), "AllowNetworkAccess does not belong to the attributes."


def test_build_service_privacy_attributes_no_trusted_algos():
    data_provider = DataServiceProvider()
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)
    privacy_dict = compute.build_service_privacy_attributes()
    assert privacy_dict
    assert isinstance(privacy_dict, dict)
    assert (
        "allowRawAlgorithm" in privacy_dict
        and privacy_dict["allowRawAlgorithm"] == False
    ), "The allowRawAlgorithm is set."
    assert (
        "allowAllPublishedAlgorithms" in privacy_dict
        and privacy_dict["allowAllPublishedAlgorithms"] == False
    ), "The allowAllPublishedAlgorithms is set."
    assert (
        "publisherTrustedAlgorithms" in privacy_dict
        and privacy_dict["publisherTrustedAlgorithms"] == []
    ), "The publisher trusted algorithms list is not empty."
    assert (
        "allowNetworkAccess" in privacy_dict
        and privacy_dict["allowNetworkAccess"] == False
    ), "The allowNetworkAccess is set."


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

    assert privacy_dict, "Privacy dictionary is None."
    assert isinstance(
        privacy_dict, dict
    ), "Privacy attributes do not form a dictionary."
    assert (
        "allowRawAlgorithm" in privacy_dict
        and privacy_dict["allowRawAlgorithm"] == True
    ), "AllowRawAlgorithm does not belong to the attributes."
    assert (
        "allowAllPublishedAlgorithms" in privacy_dict
        and privacy_dict["allowAllPublishedAlgorithms"] == True
    ), "AllowAllPublishedAlgorithms does not belong to the attributes."
    assert (
        "publisherTrustedAlgorithms" in privacy_dict
    ), "Publisher trusted algorithms do not exist in privacy dict."
    assert (
        privacy_dict["publisherTrustedAlgorithms"][0]["did"]
        and privacy_dict["publisherTrustedAlgorithms"][0]["did"] == algorithm_ddo.did
    ), "The did of the algorithm DDO does not exist."
    assert privacy_dict["publisherTrustedAlgorithms"][0][
        "filesChecksum"
    ] and privacy_dict["publisherTrustedAlgorithms"][0][
        "filesChecksum"
    ] == create_checksum(
        algorithm_ddo.metadata["encryptedFiles"]
        + json.dumps(algorithm_ddo.metadata["main"]["files"], separators=(",", ":"))
    ), "The filesChecksum does not exist."
    assert privacy_dict["publisherTrustedAlgorithms"][0][
        "containerSectionChecksum"
    ] and privacy_dict["publisherTrustedAlgorithms"][0][
        "containerSectionChecksum"
    ] == create_checksum(
        json.dumps(
            algorithm_ddo.metadata["main"]["algorithm"]["container"],
            separators=(",", ":"),
        )
    ), "The cointainerSectionChecksum does not exist."
    assert (
        "allowNetworkAccess" in privacy_dict
        and privacy_dict["allowNetworkAccess"] == True
    ), "AllowNetworkAccess does not belong to the attributes."

    cluster_dict = compute.build_cluster_attributes(
        "Kubernetes", "http://10.0.0.17/my_cluster"
    )
    assert cluster_dict, "Cluster dictionary is None."
    assert isinstance(cluster_dict, dict), "The cluster is not a dict."
    assert (
        "type" in cluster_dict and cluster_dict["type"] == "Kubernetes"
    ), "Type does not belong to the attributes."
    assert (
        "url" in cluster_dict and cluster_dict["url"] == "http://10.0.0.17/my_cluster"
    ), "Url does not belong to the attributes."

    container_dict = compute.build_container_attributes(
        "node", "best_tag", "entrypoint.exe"
    )
    assert container_dict, "Container dictionary is None."
    assert isinstance(container_dict, dict), "The container is not a dict."
    assert (
        "image" in container_dict and container_dict["image"] == "node"
    ), "Image does not belong to the attributes."
    assert (
        "tag" in container_dict and container_dict["tag"] == "best_tag"
    ), "Tag does not belong to the attributes."
    assert (
        "entrypoint" in container_dict
        and container_dict["entrypoint"] == "entrypoint.exe"
    ), "Entrypoint does not belong to the attributes."

    server_dict = compute.build_server_attributes(
        "test_server_id_123", "test_server_type", 4, 4, "20", "20", 30
    )
    assert server_dict, "Server dictionary is None."
    assert isinstance(server_dict, dict), "The server is not a dict."
    assert (
        "serverId" in server_dict and server_dict["serverId"] == "test_server_id_123"
    ), "serverId does not belong to the attributes."
    assert (
        "serverType" in server_dict and server_dict["serverType"] == "test_server_type"
    ), "serverType does not belong to the attributes."
    assert (
        "cpu" in server_dict and server_dict["cpu"] == 4
    ), "CPU does not belong to the attributes."
    assert (
        "gpu" in server_dict and server_dict["gpu"] == 4
    ), "GPU does not belong to the attributes."
    assert (
        "memory" in server_dict and server_dict["memory"] == "20"
    ), "Memory does not belong to the attributes."
    assert (
        "disk" in server_dict and server_dict["disk"] == "20"
    ), "Disk does not belong to the attributes."
    assert (
        "maxExecutionTime" in server_dict and server_dict["maxExecutionTime"] == 30
    ), "Execution time does not exist."

    service_provider_dict = compute.build_service_provider_attributes(
        "My Provider", "Unit testing", cluster_dict, container_dict, server_dict
    )
    assert service_provider_dict, "Provider server is None."
    assert isinstance(service_provider_dict, dict), "Provider server is not a dict."
    assert (
        "type" in service_provider_dict
        and service_provider_dict["type"] == "My Provider"
    ), "Type does not exist in provider server dictionary."
    assert (
        "description" in service_provider_dict
        and service_provider_dict["description"] == "Unit testing"
    ), "Description does not belong to the attributes."
    assert (
        "environment" in service_provider_dict
    ), "Environment does not belong to the attributes."
    assert (
        "cluster" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["cluster"] == cluster_dict
    ), "Cluster does not belong to the environment attributes."
    assert (
        "supportedContainers" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["supportedContainers"]
        == container_dict
    ), "Container does not belong to the environment attributes."
    assert (
        "supportedServers" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["supportedServers"] == server_dict
    ), "Server does not belong to the environment attributes."

    compute_attributes = compute.create_compute_service_attributes(
        30,
        publisher.address,
        (datetime.utcnow().replace(microsecond=0).isoformat() + "Z"),
        service_provider_dict,
        privacy_dict,
    )

    assert compute_attributes, "Compute attributes do not exist."
    assert isinstance(compute_attributes, dict), "compute_attributes is not a dict."
    assert (
        "main" in compute_attributes
    ), "Main does not belong to compute attributes dict."
    assert isinstance(compute_attributes["main"], dict), "Main is not a dict."
    assert (
        "name" in compute_attributes["main"]
        and compute_attributes["main"]["name"] == "dataAssetComputingServiceAgreement"
    ), "Name does not belong to main dict or has a different value."
    assert (
        "creator" in compute_attributes["main"]
        and compute_attributes["main"]["creator"] == publisher.address
    ), "Creator does not belong to main dict or has a different value."
    assert (
        "datePublished" in compute_attributes["main"]
        and compute_attributes["main"]["datePublished"]
        == datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    ), "Published date does not belong to main dict or has a different value."
    assert "cost" in compute_attributes["main"], "Cost does not belong to main dict."
    assert (
        "timeout" in compute_attributes["main"]
        and compute_attributes["main"]["timeout"] == 30
    ), "Timeout does not belong to main dict or has a different value."
    assert (
        "provider" in compute_attributes["main"]
        and compute_attributes["main"]["provider"] == service_provider_dict
    ), "Provider does not belong to main dict or has a different value."
    assert (
        "privacy" in compute_attributes["main"]
        and compute_attributes["main"]["privacy"] == privacy_dict
    ), "Privacy does not belong to main dict or has a different value."


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

    assert privacy_dict, "Privacy dictionary is None."
    assert isinstance(
        privacy_dict, dict
    ), "Privacy attributes do not form a dictionary."

    cluster_dict = compute.build_cluster_attributes(
        "Kubernetes", "http://10.0.0.17/my_cluster"
    )
    assert cluster_dict, "Cluster dictionary is None."
    assert isinstance(cluster_dict, dict), "The cluster is not a dict."

    container_dict = compute.build_container_attributes(
        "node", "best_tag", "entrypoint.exe"
    )
    assert container_dict, "Container dictionary is None."
    assert isinstance(container_dict, dict), "The container is not a dict."

    server_dict = compute.build_server_attributes(
        "test_server_id_123", "test_server_type", 4, 4, "20", "20", 30
    )
    assert server_dict, "Server dictionary is None."
    assert isinstance(server_dict, dict), "The server is not a dict."

    service_provider_dict = compute.build_service_provider_attributes(
        "My Provider", "Unit testing", cluster_dict, container_dict, server_dict
    )
    assert service_provider_dict, "Provider server is None."
    assert isinstance(service_provider_dict, dict), "Provider server is not a dict."

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
