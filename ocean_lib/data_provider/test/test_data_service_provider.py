#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
from unittest.mock import Mock

import ecies
import pytest
from ocean_lib.agreements.file_objects import FilesTypeFactory
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.data_provider.data_service_provider import DataServiceProvider as DataSP
from ocean_lib.data_provider.data_service_provider import urljoin
from ocean_lib.exceptions import DataProviderException
from ocean_lib.http_requests.requests_session import get_requests_session
from ocean_lib.models.compute_input import ComputeInput
from requests.exceptions import InvalidURL
from requests.models import Response
from tests.resources.ddo_helpers import create_basics
from tests.resources.helper_functions import (
    deploy_erc721_erc20,
    get_provider_fees,
    get_publisher_ocean_instance,
)
from tests.resources.mocks.http_client_mock import (
    HttpClientEmptyMock,
    HttpClientEvilMock,
    HttpClientNiceMock,
)

TEST_SERVICE_ENDPOINTS = {
    "computeDelete": ["DELETE", "/api/services/compute"],
    "computeStart": ["POST", "/api/services/compute"],
    "computeStatus": ["GET", "/api/services/compute"],
    "computeStop": ["PUT", "/api/services/compute"],
    "computeResult": ["GET", "/api/services/computeResult"],
    "download": ["GET", "/api/services/download"],
    "encrypt": ["POST", "/api/services/encrypt"],
    "decrypt": ["POST", "/api/services/decrypt"],
    "fileinfo": ["POST", "/api/services/fileinfo"],
    "initialize": ["GET", "/api/services/initialize"],
    "nonce": ["GET", "/api/services/nonce"],
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


def test_initialize_fails(with_evil_client):
    """Tests failure of initialize endpoint."""
    with pytest.raises(DataProviderException) as err:
        DataSP.initialize(
            "some_did",
            "service_id",
            "some_consumer_address",
            "http://mock/",
            userdata={"test_dict_key": "test_dict_value"},
        )
    assert err.value.args[0].startswith(
        "Initialize service failed at the initializeEndpoint"
    )


def test_start_compute_job_fails_empty(with_empty_client, consumer_wallet):
    """Tests failure of compute job from endpoint with empty response."""
    with pytest.raises(AssertionError):
        DataSP.start_compute_job(
            service_endpoint="http://mock/",
            consumer=consumer_wallet,
            dataset=ComputeInput("some_did", "some_tx_id", "some_service_id"),
            compute_environment="some_compute_environment",
            algorithm=ComputeInput(
                "another_did", "another_tx_id", "another_service_id"
            ),
        )


def test_start_compute_job_fails_error_response(with_evil_client, consumer_wallet):
    """Tests failure of compute job from endpoint with non-200 response."""
    with pytest.raises(DataProviderException):
        DataSP.start_compute_job(
            service_endpoint="http://mock/",
            consumer=consumer_wallet,
            dataset=ComputeInput("some_did", "some_tx_id", "some_service_id"),
            compute_environment="some_compute_environment",
            algorithm=ComputeInput(
                "another_did", "another_tx_id", "another_service_id"
            ),
        )


def test_send_compute_request_failure(with_evil_client, provider_wallet):
    """Tests failure of compute request from endpoint with non-200 response."""
    with pytest.raises(Exception):
        DataSP._send_compute_request(
            "post", "some_did", "some_job_id", "http://mock/", provider_wallet
        )


def test_compute_job_result(with_nice_client, provider_wallet):
    """Tests successful compute job starting."""
    result = DataSP.compute_job_result(
        "some_did", "some_job_id", "http://mock", provider_wallet
    )
    assert result == {"good_job": "with_mock"}


def test_delete_job_result(with_nice_client, provider_wallet):
    """Tests successful compute job deletion."""
    result = DataSP.delete_compute_job(
        "some_did", "some_job_id", "http://mock", provider_wallet
    )
    assert result == {"good_job": "with_mock_delete"}


def test_encrypt(web3, provider_wallet):
    """Tests successful encrypt job."""
    key = provider_wallet.private_key
    file1_dict = {"type": "url", "url": "https://url.com/file1.csv", "method": "GET"}
    file2_dict = {"type": "url", "url": "https://url.com/file2.csv", "method": "GET"}
    file1 = FilesTypeFactory(file1_dict)
    file2 = FilesTypeFactory(file2_dict)

    # Encrypt file objects
    result = DataSP.encrypt(
        [file1, file2], "http://localhost:8030/api/services/encrypt"
    )
    encrypted_files = result.content.decode("utf-8")
    assert result.status_code == 201
    assert result.headers["Content-type"] == "text/plain"
    assert encrypted_files.startswith("0x")

    if isinstance(encrypted_files, str):
        encrypted_files = web3.toBytes(hexstr=encrypted_files)
    decrypted_document = ecies.decrypt(key, encrypted_files)
    decrypted_document_string = decrypted_document.decode("utf-8")
    assert decrypted_document_string == json.dumps(
        [file1.to_dict(), file2.to_dict()], separators=(",", ":")
    )

    # Encrypt a simple string
    test_string = "hello_world"
    encrypt_result = DataSP.encrypt(
        test_string, "http://localhost:8030/api/services/encrypt"
    )
    encrypted_document = encrypt_result.content.decode("utf-8")
    assert result.status_code == 201
    assert result.headers["Content-type"] == "text/plain"
    assert result.content.decode("utf-8").startswith("0x")

    if isinstance(encrypted_document, str):
        encrypted_document = web3.toBytes(hexstr=encrypted_document)
    decrypted_document = ecies.decrypt(key, encrypted_document)
    decrypted_document_string = decrypted_document.decode("utf-8")
    assert decrypted_document_string == test_string


def test_fileinfo(web3, config, publisher_wallet, publisher_ocean_instance):
    erc721_token, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet
    )
    _, metadata, encrypted_files = create_basics(config, web3, DataSP)

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_token.address,
        deployed_erc20_tokens=[erc20_token],
    )
    access_service = ddo.get_service(ServiceTypes.ASSET_ACCESS)

    fileinfo_result = DataSP.fileinfo(
        ddo.did, access_service.id, DataSP.build_fileinfo(config.provider_url)[1]
    )
    assert fileinfo_result.status_code == 200
    files_info = fileinfo_result.json()
    assert len(files_info) == 2
    for file_index, file in enumerate(files_info):
        assert file["index"] == file_index
        assert file["valid"] is True
        assert file["contentType"] == "text/html"


def test_initialize(web3, config, publisher_wallet, publisher_ocean_instance):
    erc721_token, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet
    )
    _, metadata, encrypted_files = create_basics(config, web3, DataSP)
    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_token.address,
        deployed_erc20_tokens=[erc20_token],
    )
    access_service = ddo.get_service(ServiceTypes.ASSET_ACCESS)

    initialize_result = DataSP.initialize(
        did=ddo.did,
        service_id=access_service.id,
        consumer_address=publisher_wallet.address,
        service_endpoint=DataSP.build_initialize_endpoint(config.provider_url)[1],
    )
    assert initialize_result
    assert initialize_result.status_code == 200
    response_json = initialize_result.json()
    assert response_json["providerFee"] == get_provider_fees()


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
        DataSP.get_root_uri("http://localhost:8030/api/services/")
        == "http://localhost:8030"
    )
    assert DataSP.get_root_uri("http://localhost:8030/api") == "http://localhost:8030"
    assert (
        DataSP.get_root_uri("http://localhost:8030/services")
        == "http://localhost:8030/services"
    )
    assert (
        DataSP.get_root_uri("http://localhost:8030/services/download")
        == "http://localhost:8030"
    )
    assert (
        DataSP.get_root_uri("http://localhost:8030/api/services")
        == "http://localhost:8030"
    )
    assert (
        DataSP.get_root_uri("http://localhost:8030/api/services/")
        == "http://localhost:8030"
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
        _endpoints.update({"newEndpoint": ["GET", "/api/services/newthing"]})
        return _endpoints

    original_func = DataSP.get_service_endpoints
    DataSP.get_service_endpoints = get_service_endpoints

    endpoints = get_service_endpoints()
    uri = "http://localhost:8030"
    method, endpnt = DataSP.build_endpoint("newEndpoint", provider_uri=uri)
    assert endpnt == urljoin(uri, endpoints["newEndpoint"][1])

    uri = "http://localhost:8030/api/services/newthing"
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


def test_check_single_file_info():
    assert DataSP.check_single_file_info(
        {"url": "http://www.google.com", "type": "url"},
        provider_uri="http://172.15.0.4:8030",
    )
    assert not DataSP.check_single_file_info(
        {"url": "http://www.google.com"}, provider_uri="http://172.15.0.4:8030"
    )
    assert not DataSP.check_single_file_info({}, provider_uri="http://172.15.0.4:8030")
