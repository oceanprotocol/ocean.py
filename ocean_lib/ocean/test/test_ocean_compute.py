#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.ocean_compute import OceanCompute


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
