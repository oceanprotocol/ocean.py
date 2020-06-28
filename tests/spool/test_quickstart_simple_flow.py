import sys

from src.ocean_lib import Ocean
from src.util import constants

def test1(network, OCEAN_address,
          alice_private_key, alice_address,
          bob_private_key, bob_address):

    # 1. Alice publishes a dataset (= publishes a datatoken)
    # For now, you're Alice:) Let's proceed.
    config = {
        'network': network,
        'privateKey': alice_private_key
    }
    ocean = Ocean.Ocean(config)
    token = ocean.createDataToken('localhost:8030')
    dt_address = token.getAddress()

    # 2. Alice hosts the dataset
    # Do from console:
    # >> touch /var/mydata/myFolder1/file
    # >> ENV DT="{'0x1234':'/var/mydata/myFolder1'}"
    # >> docker run @oceanprotocol/provider-py -e CONFIG=DT

    # 3. Alice mints 100 tokens
    token.mint(100.0)

    # 4. Alice transfers 1 token to Bob
    token.transfer(bob_address, 1.0)

    # 5. Bob consumes dataset
    # Now, you're Bob:)
    bob_config = {
        'network': network,
        'privateKey': bob_private_key,
    }
    bob_ocean = Ocean.Ocean(bob_config)
    token = bob_ocean.getToken(dt_address)
    _file = token.download()
