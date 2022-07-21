from xmlrpc.client import ResponseError
import pytest
import os
from requests.exceptions import InvalidURL

from ocean_lib.storage_provider.storage_provider import StorageProvider as SP
from ocean_lib.http_requests.requests_session import get_requests_session
from ocean_lib.exceptions import StorageProviderException

from tests.resources.mocks.http_client_mock import (
    HttpClientEmptyMock,
    HttpClientEvilMock,
    HttpClientNiceMock,
)


def test_set_requests_session():
    """Tests that a custom http client can be set on the DataServiceProvider."""
    os.environ["IPFS_GATEWAY"] = "https://api.web3.storage/upload"
    sp = SP()
    requests_session = HttpClientNiceMock()
    sp.set_requests_session(requests_session)
    assert isinstance(sp.get_requests_session(), HttpClientNiceMock)


@pytest.mark.unit
def test_upload_fails():

    gateway = "https://api.web3.storage/upload"
    os.environ["IPFS_GATEWAY"] = gateway
    os.environ["STORAGE_TOKEN"] = "thisIsNotAnAPIKey"
    sp = SP()

    http_client = HttpClientNiceMock()
    sp.set_requests_session(http_client)
    response = sp.upload("")

    assert response.status_code == 200

    http_client = HttpClientEvilMock()
    sp.set_requests_session(http_client)

    with pytest.raises(StorageProviderException):
        sp.upload("")

    http_client = HttpClientEmptyMock()
    sp.set_requests_session(http_client)

    with pytest.raises(StorageProviderException):
        sp.upload("")


@pytest.mark.unit
def test_download_fails():

    gateway = "https://api.web3.storage/upload"
    os.environ["IPFS_GATEWAY"] = gateway
    os.environ["STORAGE_TOKEN"] = "thisIsNotAnAPIKey"
    sp = SP()

    cid = "32df345ds65432w934009df4qpx12gh83wd5"

    http_client = HttpClientNiceMock()
    sp.set_requests_session(http_client)
    response = sp.download(cid)

    assert response.status_code == 200

    http_client = HttpClientEvilMock()
    sp.set_requests_session(http_client)

    with pytest.raises(StorageProviderException):
        sp.download(cid)

    http_client = HttpClientEmptyMock()
    sp.set_requests_session(http_client)

    with pytest.raises(StorageProviderException):
        sp.download(cid)


@pytest.mark.integration
def test_get_gateway_uri():
    """Tests extraction of base URLs from various inputs."""

    with pytest.raises(StorageProviderException):
        # no gateway env set
        del os.environ["IPFS_GATEWAY"]
        sp = SP()

    gateway = "https://api.web3.storage/upload"
    os.environ["IPFS_GATEWAY"] = gateway
    sp = SP()

    assert SP.is_valid_gateway(gateway)
    assert SP.get_gateway_uri(gateway) == gateway
    assert (
        SP.get_gateway_uri("https://api.estuary.tech/content/add")
        == "https://api.estuary.tech/content/add"
    )
    assert (
        SP.get_gateway_uri("https://shuttle-5.estuary.tech/content/add")
        == "https://shuttle-5.estuary.tech/content/add"
    )

    with pytest.raises(InvalidURL):
        SP.get_gateway_uri("https://shuttle-6.estuary.tech/content/add")

    assert not SP.is_valid_gateway("thisIsNotAGateway")
    with pytest.raises(InvalidURL):
        SP.get_gateway_uri("thisIsNotAGateway")

    with pytest.raises(InvalidURL):
        # valid URL, but not reachable
        sp.get_gateway_uri("http://api.estuary.tech")

    with pytest.raises(InvalidURL):
        sp.get_gateway_uri("//")


@pytest.mark.unit
def test_get_gateway_type():
    """Tests extraction of gateway type from various inputs."""
    gateway = "https://api.web3.storage/upload"
    assert SP.get_gateway_type(gateway) == "web3.storage"
    assert SP.get_gateway_type("https://api.estuary.tech/content/add") == "estuary.tech"
    assert (
        SP.get_gateway_type("https://shuttle-5.estuary.tech/content/add")
        == "estuary.tech"
    )

    with pytest.raises(InvalidURL):
        SP.get_gateway_type("https://api.someother.storage/upload")
