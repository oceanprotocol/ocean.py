#!/usr/bin/python3

#do *not* import brownie, that's too much dependency here
import configparser
import os

from ocean_lib import Ocean

#note: we could have used @pytest.mark.parametrize, but this hurts our
# ability to run these tests individually
def test_on_development():
    _test_on_network('development')
    
def test_on_rinkeby():
    _test_on_network('rinkeby')
    
def test_mainnet():
    _test_on_network('mainnet')
    
def _test_on_network(network):
    #setup specific to this unit test
    cp = configparser.ConfigParser()
    cp.read(os.path.expanduser('~/ocean.conf'))
    alice_private_key = cp[network]['TEST_PRIVATE_KEY1']
    bob_private_key   = cp[network]['TEST_PRIVATE_KEY2']

    #1. Alice publishes a dataset (= publishes a datatoken)
    config = {
        'network' : network, 
        'privateKey' : alice_private_key,
    }
    ocean = Ocean.Ocean(config)
    token = ocean.createDatatoken('localhost:8030')
    dt_address = token.address
    print(dt_address)

    #2. Alice hosts the dataset
    #(FIXME)
    
    #3. Alice mints 100 tokens
    token.mint(100)

    #4. Alice transfers 1 token to Bob
    token.transfer(bob_account.address, 1)
