#!/usr/bin/python3

import brownie
from brownie import ERC20Template, Factory
import configparser
import os

from ocean_lib import Ocean

def test_quickstart_simpleflow():
    
    #Config for both Deployment and Quickstart flow
    cp = configparser.ConfigParser()
    cp.read(os.path.expanduser('~/ocean.conf'))
    opf_private_key = cp['private']['OPF_PRIVATE_KEY']
    community_addr = cp['public']['OCEAN_COMMUNITY_ADDRESS']
    
    alice_private_key = cp['private']['TEST_PRIVATE_KEY1']
    bob_private_key   = cp['private']['TEST_PRIVATE_KEY2']

    config = {
        'network' : 'development', #see 'brownie network lists'
        'privateKey' : alice_private_key,
    }

    #==============DEPLOYMENT=======================
    if not brownie.network.is_connected():
        brownie.network.connect(config['network'])
    
    alice_account = Ocean.account(alice_private_key)
    bob_account = Ocean.account(bob_private_key)
    opf_account = Ocean.account(opf_private_key)
    
    ERC20_template = ERC20Template.deploy(
        'Template', 'TEMPLATE', alice_account.address,
        community_addr, {'from': alice_account})
        
    factory = Factory.deploy(
        ERC20_template.address, community_addr, {'from': opf_account})
    
    #==============QUICKSTART FLOW=======================
    #1. Alice publishes a dataset (= publishes a datatoken)
    
    ocean = Ocean.Ocean(config, factory) 
    
    token = ocean.createDatatoken('localhost:8030')
    dt_address = token.address
    print(dt_address)

    #2. Alice hosts the dataset
    #(FIXME)
    
    #3. Alice mints 100 tokens
    import pdb; pdb.set_trace()
    token.mint(alice_account, 100, {'from': alice_account})

    #4. Alice transfers 1 token to Bob
    import pdb; pdb.set_trace()
    token.transfer(bob_account.address, 1, {'from': alice_account})
