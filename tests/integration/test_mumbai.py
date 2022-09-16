import os
import pytest
import requests

from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import networkToChainId
from ocean_lib.web3_internal.wallet import Wallet

    
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
block_confirmations = 0

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
    print(f"config.block_confirmations = {config.block_confirmations.value}")
    print(f"config.metadata_cache_uri = '{config.metadata_cache_uri}'")
    print(f"config.provider_url = '{config.provider_url}'")

    # Create Ocean instance
    ocean = Ocean(config)
    web3 = ocean.web3

    # Create Alice's wallet
    alice_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
    alice_wallet = Wallet(web3, alice_private_key, config.block_confirmations, config.transaction_timeout)
    print(f"alice_wallet.address = '{alice_wallet.address}'")

    # Create Bob's wallet
    bob_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY2')
    bob_wallet = Wallet(web3, bob_private_key, config.block_confirmations, config.transaction_timeout)
    print(f"bob_wallet.address = '{bob_wallet.address}'")

    # Get gas price (in Gwei) from Polygon gas station
    gas_price = requests.get('https://gasstation-mumbai.matic.today/v2').json()['fast']['maxFee']

    # Simplest possible tx: Alice send Bob some fake MATIC
    bob_eth_before = web3.eth.get_balance(bob_wallet.address)
    nonce = web3.eth.getTransactionCount(alice_wallet.address)
    tx = {'nonce': nonce,
          'gasPrice': web3.toWei(gas_price, 'gwei'),
          'gas': 21000, #a standard ETH transfer needs 21K gas
          'chainId': networkToChainId("mumbai"),
          'to': bob_wallet.address,
          'from' : alice_wallet.address,
          'value': web3.toWei(0.001, 'ether'),
          }
    signed_tx = web3.eth.account.sign_transaction(tx, alice_wallet.private_key)
    print("Do a send-Ether tx...")
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print("Wait for send-Ether tx to complete...")
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    bob_eth_after = web3.eth.get_balance(bob_wallet.address)
    assert bob_eth_after > bob_eth_before
    
    # Super-simple Ocean tx: Alice publish data NFT
    import pdb; pdb.set_trace()
    print("Do an Ocean tx, and wait for it to complete...")
    data_nft = ocean.create_data_nft('My NFT1', 'NFT1', alice_wallet)
    assert data_nft.symbol() == 'NFT1'

