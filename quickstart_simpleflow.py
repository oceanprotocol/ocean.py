#! ./myenv/bin/python3

#do *not* import brownie, that's too much dependency here
from ocean_lib import Ocean
    
if __name__ == '__main__':  
    network = 'ganache'
    
    #set accounts. For each network, these need ETH with gas.
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
    token = ocean.createToken('localhost:8030')
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
    token = bob_ocean.getToken(dt_address)
    _file = token.download()
