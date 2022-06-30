import pytest
import os

from ocean_lib.storage_provider.storage_provider import StorageProvider as SP
from ocean_lib.http_requests.requests_session import get_requests_session
from ocean_lib.exceptions import StorageProviderException

from tests.resources.mocks.http_client_mock import (
    TEST_SERVICE_ENDPOINTS,
    HttpClientEmptyMock,
    HttpClientEvilMock,
    HttpClientNiceMock,
)

EVIL_API_KEY = 'evil_api_key'
EVIL_STORAGE_URL = 'evil_storage_url'
NICE_STORAGE_URL = 'https://shuttle-5.estuary.tech/content/add'


@pytest.fixture
def with_evil_client():
    requests_session = HttpClientEvilMock()
    SP.set_requests_session(requests_session)
    yield
    SP.set_requests_session(get_requests_session())


@pytest.fixture
def with_nice_client():
    requests_session = HttpClientNiceMock()
    SP.set_requests_session(requests_session)
    yield
    SP.set_requests_session(get_requests_session())


@pytest.fixture
def with_empty_client():
    requests_session = HttpClientEmptyMock()
    SP.set_requests_session(requests_session)
    yield
    SP.set_requests_session(get_requests_session())


def test_set_requests_session(with_nice_client):
    """Tests that a custom http client can be set on the DataServiceProvider."""
    assert isinstance(SP.get_requests_session(), HttpClientNiceMock)


@pytest.fixture
def with_evil_storage_url():
    config = {
    'network' : 'https://rinkeby.infura.io/v3/d163c48816434b0bbb3ac3925d6c6c80',
    'BLOCK_CONFIRMATIONS': 0,
    'address.file': '~/.ocean/ocean-contracts/artifacts/address.json',
    'metadata_cache_uri' : 'https://aquarius.oceanprotocol.com',
    'provider.url' : 'http://172.15.0.4:8030',
    'PROVIDER_ADDRESS': '0x00bd138abd70e2f00903268f3db08f2d25677c9e',
    'downloads.path': 'consume-downloads',
    'storage.url': EVIL_STORAGE_URL
    }

    return config


@pytest.fixture
def with_nice_storage_url():
    config = {
    'network' : 'https://rinkeby.infura.io/v3/d163c48816434b0bbb3ac3925d6c6c80',
    'BLOCK_CONFIRMATIONS': 0,
    'address.file': '~/.ocean/ocean-contracts/artifacts/address.json',
    'metadata_cache_uri' : 'https://aquarius.oceanprotocol.com',
    'provider.url' : 'http://172.15.0.4:8030',
    'PROVIDER_ADDRESS': '0x00bd138abd70e2f00903268f3db08f2d25677c9e',
    'downloads.path': 'consume-downloads',
    'storage.url': NICE_STORAGE_URL
    }

    return config

@pytest.fixture
def with_evil_api_key():
    return EVIL_API_KEY

@pytest.mark.unit
def test_evil_api_key(with_evil_api_key, with_nice_storage_url):
    store = SP(with_nice_storage_url)
    os.environ["STORAGE_TOKEN"] = with_evil_api_key

    with pytest.raises(
        StorageProviderException, match=f"StorageProviderException:"
    ):
        store.upload("hello.txt")

@pytest.mark.unit
def test_evil_url(with_evil_storage_url):
    with pytest.raises(
        IndexError, match=f"IndexError: list index out of range:"
    ):
        SP(with_evil_storage_url)
