#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
from datetime import datetime

from ocean_lib.assets.utils import create_checksum
from ocean_lib.common.agreements.service_agreement import ServiceAgreement
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.ocean_compute import OceanCompute
from tests.integration.test_compute_flow import process_order
from tests.resources.ddo_helpers import (
    get_registered_algorithm_ddo,
    wait_for_ddo,
    get_registered_ddo_with_compute_service,
)
from tests.resources.helper_functions import get_publisher_wallet


def test_build_cluster_attributes():
    data_provider = DataServiceProvider
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)
    cluster_dict = compute.build_cluster_attributes(
        "Kubernetes", "http://10.0.0.17/my_cluster"
    )
    assert cluster_dict
    assert isinstance(cluster_dict, dict)
    assert "type" in cluster_dict and cluster_dict["type"] == "Kubernetes"
    assert (
        "url" in cluster_dict and cluster_dict["url"] == "http://10.0.0.17/my_cluster"
    )


def test_build_container_attributes():
    data_provider = DataServiceProvider
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)
    container_dict = compute.build_container_attributes(
        "node", "best_tag", "entrypoint.exe"
    )
    assert container_dict
    assert isinstance(container_dict, dict)
    assert "image" in container_dict and container_dict["image"] == "node"
    assert "tag" in container_dict and container_dict["tag"] == "best_tag"
    assert (
        "entrypoint" in container_dict
        and container_dict["entrypoint"] == "entrypoint.exe"
    )


def test_build_server_attributes():
    data_provider = DataServiceProvider
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)
    server_dict = compute.build_server_attributes(
        "123", "foo_server_type", 4, 4, "20", "20", 30
    )
    assert server_dict
    assert isinstance(server_dict, dict)
    assert "serverId" in server_dict and server_dict["serverId"] == "123"
    assert (
        "serverType" in server_dict and server_dict["serverType"] == "foo_server_type"
    )
    assert "cpu" in server_dict and server_dict["cpu"] == 4
    assert "gpu" in server_dict and server_dict["gpu"] == 4
    assert "memory" in server_dict and server_dict["memory"] == "20"
    assert "disk" in server_dict and server_dict["disk"] == "20"
    assert "maxExecutionTime" in server_dict and server_dict["maxExecutionTime"] == 30


def test_build_service_provider_attributes():
    data_provider = DataServiceProvider
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)

    cluster_dict = compute.build_cluster_attributes(
        "Kubernetes", "http://10.0.0.17/my_cluster"
    )
    assert cluster_dict
    assert isinstance(cluster_dict, dict)
    assert "type" in cluster_dict and cluster_dict["type"] == "Kubernetes"
    assert (
        "url" in cluster_dict and cluster_dict["url"] == "http://10.0.0.17/my_cluster"
    )

    container_dict = compute.build_container_attributes(
        "node", "best_tag", "entrypoint.exe"
    )
    assert container_dict
    assert isinstance(container_dict, dict)
    assert "image" in container_dict and container_dict["image"] == "node"
    assert "tag" in container_dict and container_dict["tag"] == "best_tag"
    assert (
        "entrypoint" in container_dict
        and container_dict["entrypoint"] == "entrypoint.exe"
    )

    server_dict = compute.build_server_attributes(
        "123", "foo_server_type", 4, 4, "20", "20", 30
    )
    assert server_dict
    assert isinstance(server_dict, dict)
    assert "serverId" in server_dict and server_dict["serverId"] == "123"
    assert (
        "serverType" in server_dict and server_dict["serverType"] == "foo_server_type"
    )
    assert "cpu" in server_dict and server_dict["cpu"] == 4
    assert "gpu" in server_dict and server_dict["gpu"] == 4
    assert "memory" in server_dict and server_dict["memory"] == "20"
    assert "disk" in server_dict and server_dict["disk"] == "20"
    assert "maxExecutionTime" in server_dict and server_dict["maxExecutionTime"] == 30

    service_provider_dict = compute.build_service_provider_attributes(
        "My Provider", "Unit testing", cluster_dict, container_dict, server_dict
    )
    assert service_provider_dict
    assert isinstance(service_provider_dict, dict)
    assert (
        "type" in service_provider_dict
        and service_provider_dict["type"] == "My Provider"
    )
    assert (
        "description" in service_provider_dict
        and service_provider_dict["description"] == "Unit testing"
    )
    assert "environment" in service_provider_dict
    assert (
        "cluster" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["cluster"] == cluster_dict
    )
    assert (
        "supportedContainers" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["supportedContainers"]
        == container_dict
    )
    assert (
        "supportedServers" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["supportedServers"] == server_dict
    )


def test_build_service_privacy_attributes(publisher_ocean_instance):
    publisher = get_publisher_wallet()
    data_provider = DataServiceProvider
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

    assert privacy_dict
    assert isinstance(privacy_dict, dict)
    assert (
        "allowRawAlgorithm" in privacy_dict
        and privacy_dict["allowRawAlgorithm"] == True
    )
    assert (
        "allowAllPublishedAlgorithms" in privacy_dict
        and privacy_dict["allowAllPublishedAlgorithms"] == True
    )
    assert "publisherTrustedAlgorithms" in privacy_dict
    assert (
        privacy_dict["publisherTrustedAlgorithms"][0]["did"]
        and privacy_dict["publisherTrustedAlgorithms"][0]["did"] == algorithm_ddo.did
    )
    assert privacy_dict["publisherTrustedAlgorithms"][0][
        "filesChecksum"
    ] and privacy_dict["publisherTrustedAlgorithms"][0][
        "filesChecksum"
    ] == create_checksum(
        algorithm_ddo.metadata["encryptedFiles"]
        + json.dumps(algorithm_ddo.metadata["main"]["files"], separators=(",", ":"))
    )
    assert privacy_dict["publisherTrustedAlgorithms"][0][
        "containerSectionChecksum"
    ] and privacy_dict["publisherTrustedAlgorithms"][0][
        "containerSectionChecksum"
    ] == create_checksum(
        json.dumps(
            algorithm_ddo.metadata["main"]["algorithm"]["container"],
            separators=(",", ":"),
        )
    )
    assert (
        "allowNetworkAccess" in privacy_dict
        and privacy_dict["allowNetworkAccess"] == True
    )


def test_build_service_privacy_attributes_no_trusted_algos():
    data_provider = DataServiceProvider
    config = Ocean.config
    compute = OceanCompute(config=config, data_provider=data_provider)
    privacy_dict = compute.build_service_privacy_attributes()
    assert privacy_dict
    assert isinstance(privacy_dict, dict)
    assert (
        "allowRawAlgorithm" in privacy_dict
        and privacy_dict["allowRawAlgorithm"] == False
    )
    assert (
        "allowAllPublishedAlgorithms" in privacy_dict
        and privacy_dict["allowAllPublishedAlgorithms"] == False
    )
    assert (
        "publisherTrustedAlgorithms" in privacy_dict
        and privacy_dict["publisherTrustedAlgorithms"] == []
    )
    assert (
        "allowNetworkAccess" in privacy_dict
        and privacy_dict["allowNetworkAccess"] == False
    )


def test_create_compute_service_attributes(publisher_ocean_instance):
    publisher = get_publisher_wallet()
    data_provider = DataServiceProvider
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

    assert privacy_dict
    assert isinstance(privacy_dict, dict)
    assert (
        "allowRawAlgorithm" in privacy_dict
        and privacy_dict["allowRawAlgorithm"] == True
    )
    assert (
        "allowAllPublishedAlgorithms" in privacy_dict
        and privacy_dict["allowAllPublishedAlgorithms"] == True
    )
    assert "publisherTrustedAlgorithms" in privacy_dict
    assert (
        privacy_dict["publisherTrustedAlgorithms"][0]["did"]
        and privacy_dict["publisherTrustedAlgorithms"][0]["did"] == algorithm_ddo.did
    )
    assert privacy_dict["publisherTrustedAlgorithms"][0][
        "filesChecksum"
    ] and privacy_dict["publisherTrustedAlgorithms"][0][
        "filesChecksum"
    ] == create_checksum(
        algorithm_ddo.metadata["encryptedFiles"]
        + json.dumps(algorithm_ddo.metadata["main"]["files"], separators=(",", ":"))
    )
    assert privacy_dict["publisherTrustedAlgorithms"][0][
        "containerSectionChecksum"
    ] and privacy_dict["publisherTrustedAlgorithms"][0][
        "containerSectionChecksum"
    ] == create_checksum(
        json.dumps(
            algorithm_ddo.metadata["main"]["algorithm"]["container"],
            separators=(",", ":"),
        )
    )
    assert (
        "allowNetworkAccess" in privacy_dict
        and privacy_dict["allowNetworkAccess"] == True
    )

    cluster_dict = compute.build_cluster_attributes(
        "Kubernetes", "http://10.0.0.17/my_cluster"
    )
    assert cluster_dict
    assert isinstance(cluster_dict, dict)
    assert "type" in cluster_dict and cluster_dict["type"] == "Kubernetes"
    assert (
        "url" in cluster_dict and cluster_dict["url"] == "http://10.0.0.17/my_cluster"
    )

    container_dict = compute.build_container_attributes(
        "node", "best_tag", "entrypoint.exe"
    )
    assert container_dict
    assert isinstance(container_dict, dict)
    assert "image" in container_dict and container_dict["image"] == "node"
    assert "tag" in container_dict and container_dict["tag"] == "best_tag"
    assert (
        "entrypoint" in container_dict
        and container_dict["entrypoint"] == "entrypoint.exe"
    )

    server_dict = compute.build_server_attributes(
        "123", "foo_server_type", 4, 4, "20", "20", 30
    )
    assert server_dict
    assert isinstance(server_dict, dict)
    assert "serverId" in server_dict and server_dict["serverId"] == "123"
    assert (
        "serverType" in server_dict and server_dict["serverType"] == "foo_server_type"
    )
    assert "cpu" in server_dict and server_dict["cpu"] == 4
    assert "gpu" in server_dict and server_dict["gpu"] == 4
    assert "memory" in server_dict and server_dict["memory"] == "20"
    assert "disk" in server_dict and server_dict["disk"] == "20"
    assert "maxExecutionTime" in server_dict and server_dict["maxExecutionTime"] == 30

    service_provider_dict = compute.build_service_provider_attributes(
        "My Provider", "Unit testing", cluster_dict, container_dict, server_dict
    )
    assert service_provider_dict
    assert isinstance(service_provider_dict, dict)
    assert (
        "type" in service_provider_dict
        and service_provider_dict["type"] == "My Provider"
    )
    assert (
        "description" in service_provider_dict
        and service_provider_dict["description"] == "Unit testing"
    )
    assert "environment" in service_provider_dict
    assert (
        "cluster" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["cluster"] == cluster_dict
    )
    assert (
        "supportedContainers" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["supportedContainers"]
        == container_dict
    )
    assert (
        "supportedServers" in service_provider_dict["environment"]
        and service_provider_dict["environment"]["supportedServers"] == server_dict
    )

    compute_attributes = compute.create_compute_service_attributes(
        30,
        publisher.address,
        (datetime.utcnow().replace(microsecond=0).isoformat() + "Z"),
        service_provider_dict,
        privacy_dict,
    )

    assert compute_attributes
    assert isinstance(compute_attributes, dict)
    assert "main" in compute_attributes
    assert isinstance(compute_attributes["main"], dict)
    assert (
        "name" in compute_attributes["main"]
        and compute_attributes["main"]["name"] == "dataAssetComputingServiceAgreement"
    )
    assert (
        "creator" in compute_attributes["main"]
        and compute_attributes["main"]["creator"] == publisher.address
    )
    assert (
        "datePublished" in compute_attributes["main"]
        and compute_attributes["main"]["datePublished"]
        == datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    )
    assert "cost" in compute_attributes["main"]
    assert (
        "timeout" in compute_attributes["main"]
        and compute_attributes["main"]["timeout"] == 30
    )
    assert (
        "provider" in compute_attributes["main"]
        and compute_attributes["main"]["provider"] == service_provider_dict
    )
    assert (
        "privacy" in compute_attributes["main"]
        and compute_attributes["main"]["privacy"] == privacy_dict
    )


def test_create_compute_service_descriptor(publisher_ocean_instance):
    publisher = get_publisher_wallet()
    data_provider = DataServiceProvider
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

    assert privacy_dict
    assert isinstance(privacy_dict, dict)

    cluster_dict = compute.build_cluster_attributes(
        "Kubernetes", "http://10.0.0.17/my_cluster"
    )
    assert cluster_dict
    assert isinstance(cluster_dict, dict)

    container_dict = compute.build_container_attributes(
        "node", "best_tag", "entrypoint.exe"
    )
    assert container_dict
    assert isinstance(container_dict, dict)

    server_dict = compute.build_server_attributes(
        "123", "foo_server_type", 4, 4, "20", "20", 30
    )
    assert server_dict
    assert isinstance(server_dict, dict)

    service_provider_dict = compute.build_service_provider_attributes(
        "My Provider", "Unit testing", cluster_dict, container_dict, server_dict
    )
    assert service_provider_dict
    assert isinstance(service_provider_dict, dict)

    compute_attributes = compute.create_compute_service_attributes(
        30,
        publisher.address,
        (datetime.utcnow().replace(microsecond=0).isoformat() + "Z"),
        service_provider_dict,
        privacy_dict,
    )
    assert compute_attributes
    assert isinstance(compute_attributes, dict)

    compute_descriptor = compute.create_compute_service_descriptor(compute_attributes)
    assert compute_descriptor
    assert isinstance(compute_descriptor, tuple)
    assert compute_descriptor[0] == "compute"
    assert compute_descriptor[1]["attributes"] == compute_attributes
