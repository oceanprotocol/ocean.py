#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import ecies
import pytest
from requests.exceptions import InvalidURL
from requests.models import Response
from web3.main import Web3

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.ddo import DDO
from ocean_lib.data_provider.base import DataServiceProviderBase, urljoin
from ocean_lib.data_provider.data_encryptor import DataEncryptor
from ocean_lib.data_provider.data_service_provider import DataServiceProvider as DataSP
from ocean_lib.data_provider.fileinfo_provider import FileInfoProvider
from ocean_lib.example_config import DEFAULT_PROVIDER_URL
from ocean_lib.exceptions import DataProviderException, OceanEncryptAssetUrlsError
from ocean_lib.http_requests.requests_session import get_requests_session
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.services.service import Service
from tests.resources.ddo_helpers import (
    get_first_service_by_type,
    get_registered_asset_with_access_service,
)
from tests.resources.mocks.http_client_mock import (
    TEST_SERVICE_ENDPOINTS,
    HttpClientEmptyMock,
    HttpClientEvilMock,
    HttpClientNiceMock,
)


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


@pytest.mark.unit
def test_initialize_fails():
    """Tests failures of initialize endpoint."""
    mock_service = Service(
        service_id="some_service_id",
        service_type="some_service_type",
        service_endpoint="http://mock/",
        datatoken="some_dt",
        files="some_files",
        timeout=0,
    )
    with pytest.raises(
        InvalidURL, match=f"InvalidURL {mock_service.service_endpoint}."
    ):
        DataSP.initialize(
            "some_did",
            mock_service,
            "some_consumer_address",
            userdata={"test_dict_key": "test_dict_value"},
        )

    mock_service.service_endpoint = DEFAULT_PROVIDER_URL
    with pytest.raises(
        DataProviderException,
        match=f"Failed to get a response for request: initializeEndpoint={DataSP.build_initialize_endpoint(mock_service.service_endpoint)[1]}",
    ) as err:
        DataSP.initialize(
            "some_did",
            mock_service,
            "some_consumer_address",
            userdata={"test_dict_key": "test_dict_value"},
        )
    assert err.value.args[0].startswith(
        "Failed to get a response for request: initializeEndpoint"
    )


@pytest.mark.unit
def test_start_compute_job_fails_empty(consumer_wallet):
    """Tests failures of compute job from endpoint with empty response."""
    mock_service = Service(
        service_id="some_service_id",
        service_type="compute",
        service_endpoint="http://mock/",
        datatoken="some_dt",
        files="some_files",
        timeout=0,
        compute_values=dict(),
    )

    mock_ddo = DDO()
    with pytest.raises(
        InvalidURL, match=f"InvalidURL {mock_service.service_endpoint}."
    ):
        DataSP.start_compute_job(
            dataset_compute_service=mock_service,
            consumer=consumer_wallet,
            dataset=ComputeInput(mock_ddo, mock_service, "tx_id"),
            compute_environment="some_env",
            algorithm=ComputeInput(DDO(), mock_service, "tx_id"),
        )
    mock_service.service_endpoint = DEFAULT_PROVIDER_URL
    with pytest.raises(
        DataProviderException, match="The dataset.documentId field is required."
    ):
        DataSP.start_compute_job(
            dataset_compute_service=mock_service,
            consumer=consumer_wallet,
            dataset=ComputeInput(DDO(), mock_service, "tx"),
            compute_environment="some_env",
            algorithm=ComputeInput(DDO(), mock_service, "tx"),
        )


@pytest.mark.unit
def test_send_compute_request_failure(with_evil_client, provider_wallet):
    """Tests failure of compute request from endpoint with non-200 response."""
    with pytest.raises(Exception):
        DataSP._send_compute_request(
            "post", "some_did", "some_job_id", "http://mock/", provider_wallet
        )


@pytest.mark.unit
def test_compute_job_result_fails(provider_wallet):
    """Tests failure of compute job starting."""

    mock_service = Service(
        service_id="some_service_id",
        service_type="some_service_type",
        service_endpoint="http://mock",
        datatoken="some_dt",
        files="some_files",
        timeout=0,
        compute_values=dict(),
    )
    with pytest.raises(
        InvalidURL, match=f"InvalidURL {mock_service.service_endpoint}."
    ):
        DataSP.compute_job_result("some_job_id", 0, mock_service, provider_wallet)


@pytest.mark.unit
def test_delete_job_result(provider_wallet):
    """Tests a failure & a success of compute job deletion."""
    mock_service = Service(
        service_id="some_service_id",
        service_type="some_service_type",
        service_endpoint="http://mock/",
        datatoken="some_dt",
        files="some_files",
        timeout=0,
        compute_values=dict(),
    )

    # Failure of compute job deletion.
    with pytest.raises(
        InvalidURL, match=f"InvalidURL {mock_service.service_endpoint}."
    ):
        DataSP.delete_compute_job(
            "some_did", "some_job_id", mock_service, provider_wallet
        )

    # Success of compute job deletion.
    mock_service.service_endpoint = DEFAULT_PROVIDER_URL
    DataSP.delete_compute_job("some_did", "some_job_id", mock_service, provider_wallet)


@pytest.mark.integration
def test_encrypt(provider_wallet, file1, file2):
    """Tests successful encrypt job."""
    key = provider_wallet.private_key
    # Encrypt file objects
    res = {"files": [file1.to_dict(), file2.to_dict()]}
    result = DataEncryptor.encrypt(res, DEFAULT_PROVIDER_URL, 8996)
    encrypted_files = result.content.decode("utf-8")
    assert result.status_code == 201
    assert result.headers["Content-type"] == "text/plain"
    assert encrypted_files.startswith("0x")

    if isinstance(encrypted_files, str):
        encrypted_files = Web3.toBytes(hexstr=encrypted_files)
    decrypted_document = ecies.decrypt(key, encrypted_files)
    decrypted_document_string = decrypted_document.decode("utf-8")
    assert decrypted_document_string == json.dumps(res, separators=(",", ":"))

    # Encrypt a simple string
    test_string = "hello_world"
    encrypt_result = DataEncryptor.encrypt(test_string, DEFAULT_PROVIDER_URL, 8996)
    encrypted_document = encrypt_result.content.decode("utf-8")
    assert result.status_code == 201
    assert result.headers["Content-type"] == "text/plain"
    assert result.content.decode("utf-8").startswith("0x")

    if isinstance(encrypted_document, str):
        encrypted_document = Web3.toBytes(hexstr=encrypted_document)
    decrypted_document = ecies.decrypt(key, encrypted_document)
    decrypted_document_string = decrypted_document.decode("utf-8")
    assert decrypted_document_string == test_string


@pytest.mark.integration
def test_fileinfo_and_initialize(publisher_wallet, publisher_ocean, ocean_address):
    """Test both fileinfo and initialize to avoid publishing 2 assets."""
    _, _, ddo = get_registered_asset_with_access_service(
        publisher_ocean, publisher_wallet, more_files=True
    )

    access_service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)

    fileinfo_result = FileInfoProvider.fileinfo(
        ddo.did, access_service, with_checksum=True
    )
    assert fileinfo_result.status_code == 200
    files_info = fileinfo_result.json()
    assert len(files_info) == 2
    for file_index, file in enumerate(files_info):
        assert file["index"] == file_index
        assert file["checksum"]
        assert file["valid"] is True
        matches = "text/plain" if file_index == 0 else "text/xml"
        assert file["contentType"] == matches

    initialize_result = DataSP.initialize(
        did=ddo.did,
        service=access_service,
        consumer_address=publisher_wallet.address,
    )
    assert initialize_result
    assert initialize_result.status_code == 200
    response_json = initialize_result.json()
    assert response_json["providerFee"]["providerFeeAmount"] == "0"
    assert response_json["providerFee"]["providerFeeToken"] == ocean_address


@pytest.mark.unit
def test_invalid_file_name():
    """Tests that no filename is returned if attachment headers are found."""
    response = Mock(spec=Response)
    response.headers = {"no_good": "headers at all"}
    assert DataSP._get_file_name(response) is None


@pytest.mark.integration
def test_expose_endpoints():
    """Tests that the DataServiceProvider exposes all service endpoints."""
    service_endpoints = TEST_SERVICE_ENDPOINTS
    provider_uri = DEFAULT_PROVIDER_URL
    valid_endpoints = DataSP.get_service_endpoints(provider_uri)
    assert len(valid_endpoints) == len(service_endpoints)
    assert [
        valid_endpoints[key] for key in set(service_endpoints) & set(valid_endpoints)
    ]


@pytest.mark.integration
def test_c2d_environments():
    """Tests that the test ocean-compute env exists on the DataServiceProvider."""
    provider_uri = DEFAULT_PROVIDER_URL
    c2d_envs = DataSP.get_c2d_environments(provider_uri, 8996)
    c2d_env_ids = [elem["id"] for elem in c2d_envs]
    assert "ocean-compute" in c2d_env_ids, "ocean-compute env not found."


@pytest.mark.integration
def test_provider_address():
    """Tests that a provider address exists on the DataServiceProvider."""
    provider_uri = DEFAULT_PROVIDER_URL
    provider_address = DataSP.get_provider_address(provider_uri, 8996)
    assert provider_address, "Failed to get provider address."

    assert DataSP.get_provider_address("not a url", 8996) is None


@pytest.mark.integration
def test_get_root_uri():
    """Tests extraction of base URLs from various inputs."""
    uri = "https://v4.provider.mainnet.oceanprotocol.com"
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


@pytest.mark.integration
def test_build_endpoint():
    """Tests that service endpoints are correctly built from URL and service name."""

    def get_service_endpoints(_provider_uri=None):
        _endpoints = TEST_SERVICE_ENDPOINTS.copy()
        _endpoints.update({"newEndpoint": ["GET", "/api/services/newthing"]})
        return _endpoints

    original_func = DataServiceProviderBase.get_service_endpoints
    DataServiceProviderBase.get_service_endpoints = get_service_endpoints

    endpoints = get_service_endpoints()
    uri = "http://localhost:8030"
    method, endpnt = DataSP.build_endpoint("newEndpoint", provider_uri=uri)
    assert endpnt == urljoin(uri, endpoints["newEndpoint"][1])

    uri = "http://localhost:8030/api/services/newthing"
    method, endpnt = DataSP.build_endpoint("download", provider_uri=uri)
    assert method == endpoints["download"][0]
    assert endpnt == urljoin(DataSP.get_root_uri(uri), endpoints["download"][1])

    DataSP.get_service_endpoints = original_func


@pytest.mark.integration
def test_build_specific_endpoints():
    """Tests that a specific list of agreed endpoints is supported on the DataServiceProvider."""
    endpoints = TEST_SERVICE_ENDPOINTS

    def get_service_endpoints(_provider_uri=None):
        return TEST_SERVICE_ENDPOINTS.copy()

    original_func = DataSP.get_service_endpoints
    DataSP.get_service_endpoints = get_service_endpoints

    provider_uri = DEFAULT_PROVIDER_URL
    base_uri = DataSP.get_root_uri(DEFAULT_PROVIDER_URL)
    assert DataSP.build_download_endpoint(provider_uri)[1] == urljoin(
        base_uri, endpoints["download"][1]
    )
    assert DataSP.build_initialize_endpoint(provider_uri)[1] == urljoin(
        base_uri, endpoints["initialize"][1]
    )
    assert DataSP.build_initialize_compute_endpoint(provider_uri)[1] == urljoin(
        base_uri, endpoints["initializeCompute"][1]
    )
    assert (
        DataSP.build_encrypt_endpoint(provider_uri, 8996)[1]
        == urljoin(base_uri, endpoints["encrypt"][1]) + "?chainId=8996"
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


@pytest.mark.integration
def test_check_single_file_info():
    assert DataSP.check_single_file_info(
        {"url": "http://www.google.com", "type": "url"},
        provider_uri="http://172.15.0.4:8030",
    )
    assert not DataSP.check_single_file_info(
        {"url": "http://www.google.com"}, provider_uri="http://172.15.0.4:8030"
    )
    assert not DataSP.check_single_file_info({}, provider_uri="http://172.15.0.4:8030")


@pytest.mark.unit
def test_encrypt_failure():
    """Tests encrypt failures."""
    http_client = HttpClientEvilMock()
    DataEncryptor.set_http_client(http_client)

    with pytest.raises(OceanEncryptAssetUrlsError):
        DataEncryptor.encrypt({}, DEFAULT_PROVIDER_URL, 8996)

    http_client = HttpClientEmptyMock()
    DataSP.set_http_client(http_client)

    with pytest.raises(DataProviderException):
        DataEncryptor.encrypt({}, DEFAULT_PROVIDER_URL, 8996)

    DataSP.set_http_client(get_requests_session())


@pytest.mark.unit
def test_fileinfo_failure():
    """Tests successful fileinfo failures."""
    service = Mock(spec=Service)
    service.service_endpoint = "http://172.15.0.4:8030"
    service.id = "abc"

    http_client = HttpClientEvilMock()
    DataSP.set_http_client(http_client)

    with pytest.raises(DataProviderException):
        FileInfoProvider.fileinfo("0xabc", service)

    http_client = HttpClientEmptyMock()
    DataSP.set_http_client(http_client)

    with pytest.raises(DataProviderException):
        FileInfoProvider.fileinfo("0xabc", service)

    DataSP.set_http_client(get_requests_session())


@pytest.mark.unit
def test_initialize_failure():
    """Tests initialize failures."""
    service = Mock(spec=Service)
    service.service_endpoint = "http://172.15.0.4:8030"
    service.id = "abc"

    http_client = HttpClientEvilMock()
    DataSP.set_http_client(http_client)

    with pytest.raises(DataProviderException):
        DataSP.initialize("0xabc", service, "0x")

    http_client = HttpClientEmptyMock()
    DataSP.set_http_client(http_client)

    with pytest.raises(DataProviderException):
        DataSP.initialize("0xabc", service, "0x")

    DataSP.set_http_client(get_requests_session())


@pytest.mark.unit
def test_initialize_compute_failure():
    """Tests initialize_compute failures."""
    service = Mock(spec=Service)
    service.service_endpoint = "http://172.15.0.4:8030"
    service.id = "abc"

    ddo = Mock(spec=DDO)
    ddo.did = "0x0"
    compute_input = ComputeInput(ddo, service)

    http_client = HttpClientEvilMock()
    DataSP.set_http_client(http_client)
    valid_until = int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp())

    with pytest.raises(
        DataProviderException, match="request failed at the initializeComputeEndpoint"
    ):
        DataSP.initialize_compute(
            [compute_input.as_dictionary()],
            compute_input.as_dictionary(),
            service.service_endpoint,
            "0x0",
            "test",
            valid_until,
        )

    http_client = HttpClientEmptyMock()
    DataSP.set_http_client(http_client)

    with pytest.raises(DataProviderException, match="Failed to get a response"):
        DataSP.initialize_compute(
            [compute_input.as_dictionary()],
            compute_input.as_dictionary(),
            service.service_endpoint,
            "0x0",
            "test",
            valid_until,
        )

    DataSP.set_http_client(get_requests_session())


@pytest.mark.unit
def test_job_result_failure():
    """Tests compute job result failures."""
    service = Mock(spec=Service)
    service.service_endpoint = "http://172.15.0.4:8030"
    service.id = "abc"

    wallet = Mock()
    wallet.address = "none"
    wallet.private_key = os.getenv("TEST_PRIVATE_KEY1")

    http_client = HttpClientEvilMock()
    DataSP.set_http_client(http_client)

    with pytest.raises(DataProviderException):
        DataSP.compute_job_result("0xabc", 0, service, wallet)

    http_client = HttpClientEmptyMock()
    DataSP.set_http_client(http_client)

    with pytest.raises(DataProviderException):
        DataSP.compute_job_result("0xabc", 0, service, wallet)

    DataSP.set_http_client(get_requests_session())


@pytest.mark.unit
def test_check_asset_failure():
    """Tests check_asset_file_info failures."""
    assert DataSP.check_asset_file_info("", "", DEFAULT_PROVIDER_URL) is False

    http_client = HttpClientEvilMock()
    DataSP.set_http_client(http_client)

    assert DataSP.check_asset_file_info("test", "", DEFAULT_PROVIDER_URL) is False

    http_client = HttpClientEmptyMock()
    DataSP.set_http_client(http_client)

    assert DataSP.check_asset_file_info("test", "", DEFAULT_PROVIDER_URL) is False

    DataSP.set_http_client(get_requests_session())
