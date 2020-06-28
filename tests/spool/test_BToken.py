from src.spool_py import BToken
from src.util import util

def test1(network, alice_context, alice_view, bob_context, bob_view,
          OCEAN_address):
    assert alice_view.OCEAN() > 10.0
    assert bob_view.OCEAN() > 10.0

    btoken = BToken.BToken(alice_context, OCEAN_address)

    assert btoken.symbol() == 'OCEAN'
    assert btoken.decimals() == 18
    assert btoken.balanceOfSelf_base() > util.OCEANtoBase(10.0)
    
    assert btoken.balanceOf_base(bob_context.address) > util.OCEANtoBase(10.0)

    assert btoken.allowanceFromSelf_base(bob_context.address) == 0
    btoken.approve(bob_context.address, int(1e18))
    assert btoken.allowanceFromSelf_base(bob_context.address) == int(1e18)

    #alice sends all her OCEAN to Bob, then Bob sends it back
    alice_OCEAN = btoken.balanceOf_base(alice_context.address)
    bob_OCEAN = btoken.balanceOf_base(bob_context.address)
    btoken.transfer(bob_context.address, alice_OCEAN)
    assert btoken.balanceOf_base(alice_context.address) == 0
    assert btoken.balanceOf_base(bob_context.address) == (alice_OCEAN+bob_OCEAN)
    
    btoken_bob = BToken.BToken(bob_context, OCEAN_address)
    btoken_bob.transfer(alice_context.address, alice_OCEAN)
    assert btoken.balanceOf_base(alice_context.address) == alice_OCEAN
    assert btoken.balanceOf_base(bob_context.address) == bob_OCEAN
    
