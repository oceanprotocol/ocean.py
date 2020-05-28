#!/usr/bin/python3

#do *not* import brownie, that's too much dependency here
import configparser
import os

from ocean_lib import Ocean, constants

#note: we could have used @pytest.mark.parametrize, but this hurts our
# ability to run these tests individually
def test_on_development():
    _test_on_network('development')
    
def test_on_rinkeby():
    _test_on_network('rinkeby')
    
def test_mainnet():
    _test_on_network('mainnet')
    
def _test_on_network(network):
    #choose accounts with ETH, for gas. Needed for rinkeby & mainnet.
    alice_private_key = Ocean.confFileValue(network, 'TEST_PRIVATE_KEY1')
    bob_private_key = Ocean.confFileValue(network, 'TEST_PRIVATE_KEY2')
    bob_address = Ocean.privateKeyToAddress(bob_private_key)

    #1. Alice publishes a dataset (= publishes a datatoken)
    #For now, you're Alice:) Let's proceed.
    config = {
        'network' : network, 
        'privateKey' : alice_private_key
    }
    ocean = Ocean.Ocean(config)
    token = ocean.createDatatoken('localhost:8030')
    dt_address = token.getAddress()
    print(dt_address)

    #2. Alice hosts the dataset
    # Do from console:
    # >> touch /var/mydata/myFolder1/file
    # >> ENV DT="{'0x1234':'/var/mydata/myFolder1'}"
    # >> docker run @oceanprotocol/provider-py -e CONFIG=DT
    
    #3. Alice mints 100 tokens
    token.mint(100)

    #4. Alice transfers 1 token to Bob
    token.transfer(bob_address, 1)

    #5. Bob consumes dataset
    #Now, you're Bob:)
    bob_config = {
        'network' : network,
        'privateKey' : bob_private_key,
    }
    bob_ocean = Ocean.Ocean(bob_config)
    asset = bob_ocean.getAsset(dt_address)
    _file = asset.download(bob_address)
