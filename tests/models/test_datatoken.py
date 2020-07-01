import pytest
from web3 import Web3

from ocean_lib.models.datatoken import DataToken
from ocean_lib.ocean import util
from ocean_lib.ocean.util import toBase18, fromBase18

def test_ERC20(alice_ocean, alice_wallet, alice_address,
               bob_wallet, bob_address):
    token = alice_ocean.create_data_token('foo_blob', from_wallet=alice_wallet)

    assert token.symbol()[:2] == 'DT'
    assert token.decimals() == 18
    assert token.balanceOf_base(alice_address) == 0

    token.mint(alice_address, toBase18(100.0), from_wallet=alice_wallet)
    assert fromBase18(token.balanceOf_base(alice_address)) == 100.0
    
    assert token.allowance_base(alice_address, bob_address) == 0
    token.approve(bob_address, toBase18(1.0), from_wallet=alice_wallet)
    assert token.allowance_base(alice_address, bob_address) == int(1e18)

    token.transfer(bob_address, toBase18(5.0), from_wallet=alice_wallet)
    assert fromBase18(token.balanceOf_base(alice_address)) == 95.0
    assert fromBase18(token.balanceOf_base(bob_address)) == 5.0
    
    token.transfer(alice_address, toBase18(3.0), from_wallet=bob_wallet)
    assert fromBase18(token.balanceOf_base(alice_address)) == 98.0
    assert fromBase18(token.balanceOf_base(bob_address)) == 2.0   

def test_blob(alice_ocean, alice_wallet):
    token = alice_ocean.create_data_token('foo_blob', alice_wallet)
    assert token.blob() == 'foo_blob'

def test_setMinter(alice_ocean,
                   alice_wallet, alice_address,
                   bob_wallet, bob_address):
    ocean = alice_ocean
    token = ocean.create_data_token('foo_blob', from_wallet=alice_wallet)

    #alice is the minter
    token.mint(alice_address, toBase18(10.0), from_wallet=alice_wallet) 
    token.mint(bob_address, toBase18(10.0), from_wallet=alice_wallet)
    with pytest.raises(Exception):
        token.mint(alice_address, toBase18(10.0), from_wallet=bob_wallet)

    #switch minter to bob
    token.setMinter(bob_address, from_wallet=alice_wallet)
    token.mint(alice_address, toBase18(10.0), from_wallet=bob_wallet)
    with pytest.raises(Exception):
        token.mint(alice_address, toBase18(10.0), from_wallet=alice_wallet)
    with pytest.raises(Exception): 
        token.mint(bob_address, toBase18(10.0), from_wallet=alice_wallet)

    #switch minter back to alice
    token.setMinter(alice_address, from_wallet=bob_wallet)
    token.mint(alice_address, toBase18(10.0), from_wallet=alice_wallet) 
    with pytest.raises(Exception):
        token.mint(alice_address, toBase18(10.0), from_wallet=bob_wallet)
