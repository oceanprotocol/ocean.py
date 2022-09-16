import os
import pytest
import requests

from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet

def test_remote_keys():
    """
    These are keys that hold fake MATIC for Mumbai, as needed for tests
     - For CI tests, the values are hold in Github Actions Secrets
     - For any local tests, you can create your own accounts, and then request funds
       from the Mumbai faucet
    """
    alice_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
    bob_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY2')
    assert len(bob_private_key) > 5
    
#this decorator skips ../../conftest.py. Why: we don't want it to turn on on ganache
@pytest.mark.nosetup_all
def test1(tmp_path):
    # Ensure no unwanted envvars
    os.environ.pop("OCEAN_NETWORK_URL", None)
    os.environ.pop("METADATA_CACHE_URI", None)
    os.environ.pop("AQUARIUS_URL", None)
    os.environ.pop("PROVIDER_URL", None)
    
    # Create conf file
    conf_file = tmp_path / "config.ini"
    conf_file.write_text("""
[eth-network]
network = https://rpc-mumbai.maticvigil.com
address.file = ~/.ocean/ocean-contracts/artifacts/address.json

[resources]
metadata_cache_uri = https://v4.aquarius.oceanprotocol.com
provider.url = https://v4.provider.mumbai.oceanprotocol.com
""")
    conf_filename = str(conf_file) #eg '/tmp/pytest-of-trentmc/pytest-1/test10/config.ini'
    assert "/tmp/" in conf_filename
    print(f"config filename = {conf_filename}")

    # Create Config instance
    config = Config(conf_filename)

    # -ensure config is truly remote
    assert "mumbai" in config.network_url
    assert "oceanprotocol.com" in config.metadata_cache_uri
    assert "oceanprotocol.com" in config.provider_url

    print(f"config.network_url = '{config.network_url}'")
    print(f"config.address_file = '{config.address_file}'")
    print(f"config.metadata_cache_uri = '{config.metadata_cache_uri}'")
    print(f"config.provider_url = '{config.provider_url}'")

    # Create Ocean instance
    ocean = Ocean(config)

    # Create Alice's wallet
    alice_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
    alice_wallet = Wallet(ocean.web3, alice_private_key, config.block_confirmations, config.transaction_timeout)
    print(f"alice_wallet.address = '{alice_wallet.address}'")
    
    # Do an an arbitrary simple tx (here, publish data NFT), and test success
    print("Initiating a tx on mumbai...")
    data_nft = ocean.create_data_nft('My NFT1', 'NFT1', alice_wallet)
    assert data_nft.symbol() == 'NFT1'

