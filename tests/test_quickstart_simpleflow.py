#!/usr/bin/python3

import os

def test_quickstart_simpleflow(token):

    alice_private_key = os.getenv('OCEAN_PRIVATE_KEY1')
    bob_private_key = os.getenv('OCEAN_PRIVATE_KEY2')
    
    #1. Alice publishes a dataset (= publishes a datatoken
    from ocean_lib import Ocean
    config = {
        'network' : 'development', #see 'brownie network lists'
        'privateKey' : alice_private_key,
    }
    ocean = Ocean.Ocean(config)
    alice_account = ocean.accountFromKey(alice_private_key)
    token = ocean.createDatatoken('localhost:8030')
    dt_address = token.address
    print(dt_address)

    #2. Alice hosts the dataset
    #(FIXME)
    
    #3. Alice mints 100 tokens
    #(FIXME)

    #4. Alice transfers 1 token to Bob
    bob_account = ocean.accountFromKey(bob_private_key)
    token.transfer(bob_account.address, 1)
