from ocean_lib.spool_py import BToken
from ocean_lib.ocean import util
from web3 import Web3

def test1(network,
          alice_wallet, alice_address,
          bob_wallet, bob_address,
          OCEAN_address):
    web3 = Web3(util.get_web3_provider(network))
    btoken = BToken.BToken(web3, OCEAN_address)

    assert btoken.symbol() == 'OCEAN'
    assert btoken.decimals() == 18
    assert btoken.balanceOf_base(alice_address) > util.toBase18(10.0)
    assert btoken.balanceOf_base(bob_address) > util.toBase18(10.0)

    assert btoken.allowance_base(alice_address, bob_address) == 0
    btoken.approve(bob_address, int(1e18), from_wallet=alice_wallet)
    assert btoken.allowance_base(alice_address, bob_address) == int(1e18)

    #alice sends all her OCEAN to Bob, then Bob sends it back
    alice_OCEAN = btoken.balanceOf_base(alice_address)
    bob_OCEAN = btoken.balanceOf_base(bob_address)
    btoken.transfer(bob_address, alice_OCEAN, from_wallet=alice_wallet)
    assert btoken.balanceOf_base(alice_address) == 0
    assert btoken.balanceOf_base(bob_address) == (alice_OCEAN+bob_OCEAN)
    
    btoken.transfer(alice_address, alice_OCEAN, from_wallet=bob_wallet)
    assert btoken.balanceOf_base(alice_address) == alice_OCEAN
    assert btoken.balanceOf_base(bob_address) == bob_OCEAN
    
