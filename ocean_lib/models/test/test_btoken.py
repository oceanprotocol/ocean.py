#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.btoken import BToken
from ocean_lib.web3_internal.currency import to_wei


def test_ERC20(
    network, web3, alice_wallet, alice_address, bob_wallet, bob_address, OCEAN_address
):
    """Tests an OCEAN token approval, allowance and transfers."""
    token = BToken(web3, OCEAN_address)

    token.approve(bob_address, 0, from_wallet=alice_wallet)
    # generating ERC20 Tokens, so the symbol is irrelevant
    assert token.symbol() == "DTT"
    assert token.decimals() == 18
    assert token.balanceOf(alice_address) > to_wei(10)
    assert token.balanceOf(bob_address) > to_wei(10)

    assert token.allowance(alice_address, bob_address) == 0
    token.approve(bob_address, to_wei(1), from_wallet=alice_wallet)
    assert token.allowance(alice_address, bob_address) == to_wei(1)

    # alice sends all her OCEAN to Bob, then Bob sends it back
    alice_OCEAN = token.balanceOf(alice_address)
    bob_OCEAN = token.balanceOf(bob_address)
    token.transfer(bob_address, alice_OCEAN, from_wallet=alice_wallet)
    assert token.balanceOf(alice_address) == 0
    assert token.balanceOf(bob_address) == (alice_OCEAN + bob_OCEAN)

    token.transfer(alice_address, alice_OCEAN, from_wallet=bob_wallet)
    assert token.balanceOf(alice_address) == alice_OCEAN
    assert token.balanceOf(bob_address) == bob_OCEAN
