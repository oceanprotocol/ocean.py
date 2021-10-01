#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from unittest.mock import Mock

import pytest
from ocean_lib.common.http_requests.requests_session import get_requests_session
from ocean_lib.data_provider.data_service_provider import DataServiceProvider as DataSP
from ocean_lib.data_provider.data_service_provider import urljoin
from ocean_lib.exceptions import OceanEncryptAssetUrlsError
from requests.exceptions import InvalidURL
from requests.models import Response
from tests.resources.helper_functions import get_publisher_ocean_instance
from tests.resources.mocks.http_client_mock import (
    HttpClientEmptyMock,
    HttpClientEvilMock,
    HttpClientNiceMock,
)

TEST_SERVICE_ENDPOINTS = {
    "computeDelete": ["DELETE", "/api/v1/services/compute"],
    "computeStart": ["POST", "/api/v1/services/compute"],
    "computeStatus": ["GET", "/api/v1/services/compute"],
    "computeStop": ["PUT", "/api/v1/services/compute"],
    "computeResult": ["GET", "/api/v1/services/computeResult"],
    "download": ["GET", "/api/v1/services/download"],
    "encrypt": ["POST", "/api/v1/services/encrypt"],
    "fileinfo": ["POST", "/api/v1/services/fileinfo"],
    "initialize": ["GET", "/api/v1/services/initialize"],
    "nonce": ["GET", "/api/v1/services/nonce"],
}


@pytest.fixture
def with_evil_client():
    http_client = HttpClientEvilMock()
    DataSP.set_http_client(http_client)
    yield
    DataSP.set_http_client(get_requests_session())


@pytest.fixture
def with_nice_client():
    http_client = HttpClientNiceMock()
    DataSP.set_http_client(http_client)
    yield
    DataSP.set_http_client(get_requests_session())


@pytest.fixture
def with_empty_client():
    http_client = HttpClientEmptyMock()
    DataSP.set_http_client(http_client)
    yield
    DataSP.set_http_client(get_requests_session())


def test_set_http_client(with_nice_client):
    """Tests that a custom http client can be set on the DataServiceProvider."""
    assert isinstance(DataSP.get_http_client(), HttpClientNiceMock)


def test_encryption_fails(with_evil_client):
    """Tests that asset encryption fails with OceanEncryptAssetUrlsError."""
    encrypt_endpoint = "http://mock/encrypt/"
    with pytest.raises(OceanEncryptAssetUrlsError):
        DataSP.encrypt_files_dict(
            [{"some_files": "files"}],
            encrypt_endpoint,
            "some_asset_id",
            "some_publisher_address",
            "some_signature",
        )


def test_nonce_fails(with_evil_client):
    """Tests that nonce retrieved erroneously is set to None."""
    assert DataSP.get_nonce("some_address", "http://localhost:8030") is None


def test_order_requirements_fails(with_evil_client):
    """Tests failure of order requirements from endpoint."""
    assert (
        DataSP.get_order_requirements(
            "some_did",
            "http://mock/",
            "some_consumer_address",
            0,
            "and_service_type",
            "some_token_address",
            userdata={"test_dict_key": "test_dict_value"},
        )
        is None
    )


def test_start_compute_job_fails_empty(with_empty_client):
    """Tests failure of compute job from endpoint with empty response."""
    with pytest.raises(AssertionError):
        DataSP.start_compute_job(
            "some_did",
            "http://mock/",
            "some_consumer_address",
            "some_signature",
            0,
            "some_tx_id",
            algorithm_did="some_algo_did",
        )


def test_start_compute_job_fails_error_response(with_evil_client):
    """Tests failure of compute job from endpoint with non-200 response."""
    with pytest.raises(ValueError):
        DataSP.start_compute_job(
            "some_did",
            "http://mock/",
            "some_consumer_address",
            "some_signature",
            0,
            "some_tx_id",
            algorithm_did="some_algo_did",
        )


def test_send_compute_request_failure(with_evil_client):
    """Tests failure of compute request from endpoint with non-200 response."""
    with pytest.raises(Exception):
        DataSP._send_compute_request(
            "post",
            "some_did",
            "some_job_id",
            "http://mock/",
            "some_consumer_address",
            "some_signature",
        )


def test_compute_job_result(with_nice_client):
    """Tests successful compute job starting."""
    result = DataSP.compute_job_result(
        "some_did",
        "some_job_id",
        "http://mock",
        "some_consumer_address",
        "some_signature",
    )
    assert result == {"good_job": "with_mock"}


def test_delete_job_result(with_nice_client):
    """Tests successful compute job deletion."""
    result = DataSP.delete_compute_job(
        "some_did",
        "some_job_id",
        "http://mock",
        "some_consumer_address",
        "some_signature",
    )
    assert result == {"good_job": "with_mock_delete"}


def test_invalid_file_name():
    """Tests that no filename is returned if attachment headers are found."""
    response = Mock(spec=Response)
    response.headers = {"no_good": "headers at all"}
    assert DataSP._get_file_name(response) is None


def test_expose_endpoints(config):
    """Tests that the DataServiceProvider exposes all service endpoints."""
    service_endpoints = TEST_SERVICE_ENDPOINTS
    provider_uri = DataSP.get_url(config)
    valid_endpoints = DataSP.get_service_endpoints(provider_uri)
    assert len(valid_endpoints) == len(service_endpoints)
    assert [
        valid_endpoints[key] for key in set(service_endpoints) & set(valid_endpoints)
    ]


def test_c2d_address(config):
    """Tests that a provider address exists on the DataServiceProvider."""
    provider_uri = DataSP.get_url(config)
    c2d_address = DataSP.get_c2d_address(provider_uri)
    assert c2d_address, "Failed to get provider address."


def test_provider_address(config):
    """Tests that a provider address exists on the DataServiceProvider."""
    provider_uri = DataSP.get_url(config)
    provider_address = DataSP.get_provider_address(provider_uri)
    assert provider_address, "Failed to get provider address."


def test_provider_address_with_url():
    """Tests that a URL version of provider address exists on the DataServiceProvider."""
    p_ocean_instance = get_publisher_ocean_instance()
    provider_address = DataSP.get_provider_address(
        DataSP.get_url(p_ocean_instance.config)
    )
    assert provider_address, "Failed to get provider address."
    assert DataSP.get_provider_address("not a url") is None


def test_get_root_uri():
    """Tests extraction of base URLs from various inputs."""
    uri = "https://provider.mainnet.oceanprotocol.com"
    assert DataSP.is_valid_provider(uri)
    assert DataSP.get_root_uri(uri) == uri
    assert DataSP.get_root_uri("http://localhost:8030") == "http://localhost:8030"
    assert (
        DataSP.get_root_uri("http://localhost:8030/api/v1/services/")
        == "http://localhost:8030"
    )
    assert (
        DataSP.get_root_uri("http://localhost:8030/api/v1") == "http://localhost:8030"
    )
    assert (
        DataSP.get_root_uri("http://localhost:8030/services")
        == "http://localhost:8030/services"
    )
    assert (
        DataSP.get_root_uri("http://localhost:8030/services/download")
        == "http://localhost:8030"
    )
    assert (
        DataSP.get_root_uri("http://localhost:8030/api/v2/services")
        == "http://localhost:8030/api/v2/services"
    )
    assert (
        DataSP.get_root_uri("http://localhost:8030/api/v2/services/")
        == "http://localhost:8030/api/v2"
    )

    assert not DataSP.is_valid_provider("thisIsNotAnURL")
    with pytest.raises(InvalidURL):
        DataSP.get_root_uri("thisIsNotAnURL")

    with pytest.raises(InvalidURL):
        # URL is of correct format but unreachable
        DataSP.get_root_uri("http://thisisaurl.but/itshouldnt")

    with pytest.raises(InvalidURL):
        # valid URL, but no provider address
        DataSP.get_root_uri("http://oceanprotocol.com")

    with pytest.raises(InvalidURL):
        DataSP.get_root_uri("//")


def test_build_endpoint():
    """Tests that service endpoints are correctly built from URL and service name."""

    def get_service_endpoints(_provider_uri=None):
        _endpoints = TEST_SERVICE_ENDPOINTS.copy()
        _endpoints.update({"newEndpoint": ["GET", "/api/v1/services/newthing"]})
        return _endpoints

    original_func = DataSP.get_service_endpoints
    DataSP.get_service_endpoints = get_service_endpoints

    endpoints = get_service_endpoints()
    uri = "http://localhost:8030"
    method, endpnt = DataSP.build_endpoint("newEndpoint", provider_uri=uri)
    assert endpnt == urljoin(uri, endpoints["newEndpoint"][1])

    uri = "http://localhost:8030/api/v1/services/newthing"
    method, endpnt = DataSP.build_endpoint("download", provider_uri=uri)
    assert method == endpoints["download"][0]
    assert endpnt == urljoin(DataSP.get_root_uri(uri), endpoints["download"][1])

    DataSP.get_service_endpoints = original_func


def test_build_specific_endpoints(config):
    """Tests that a specific list of agreed endpoints is supported on the DataServiceProvider."""
    endpoints = TEST_SERVICE_ENDPOINTS

    def get_service_endpoints(_provider_uri=None):
        return TEST_SERVICE_ENDPOINTS.copy()

    original_func = DataSP.get_service_endpoints
    DataSP.get_service_endpoints = get_service_endpoints

    provider_uri = DataSP.get_url(config)
    base_uri = DataSP.get_root_uri(config.provider_url)
    assert DataSP.build_download_endpoint(provider_uri)[1] == urljoin(
        base_uri, endpoints["download"][1]
    )
    assert DataSP.build_initialize_endpoint(provider_uri)[1] == urljoin(
        base_uri, endpoints["initialize"][1]
    )
    assert DataSP.build_encrypt_endpoint(provider_uri)[1] == urljoin(
        base_uri, endpoints["encrypt"][1]
    )
    assert DataSP.build_fileinfo(provider_uri)[1] == urljoin(
        base_uri, endpoints["fileinfo"][1]
    )
    assert DataSP.build_compute_endpoint(provider_uri)[1] == urljoin(
        base_uri, endpoints["computeStatus"][1]
    )
    assert DataSP.build_compute_endpoint(provider_uri)[1] == urljoin(
        base_uri, endpoints["computeStart"][1]
    )
    assert DataSP.build_compute_endpoint(provider_uri)[1] == urljoin(
        base_uri, endpoints["computeStop"][1]
    )
    assert DataSP.build_compute_endpoint(provider_uri)[1] == urljoin(
        base_uri, endpoints["computeDelete"][1]
    )

    DataSP.get_service_endpoints = original_func
