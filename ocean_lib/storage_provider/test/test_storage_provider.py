import pytest
import os

from ocean_lib.storage_provider.storage_provider import StorageProvider as SP
from ocean_lib.exceptions import StorageProviderException

EVIL_API_KEY = 'evil_api_key'
EVIL_STORAGE_URL = 'evil_storage_url'
NICE_STORAGE_URL = 'https://shuttle-5.estuary.tech/content/add'

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

# @pytest.mark.unit
def test_evil_api_key(with_evil_api_key, with_nice_storage_url):
    store = SP(with_nice_storage_url)
    os.environ["STORAGE_TOKEN"] = with_evil_api_key

    with pytest.raises(
        StorageProviderException, match=f"StorageProviderException:"
    ):
        SP.store("hello.txt")
    