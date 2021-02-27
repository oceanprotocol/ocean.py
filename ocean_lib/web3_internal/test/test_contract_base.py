#  Copyright 2021 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_lib.web3_internal.contract_base import ContractBase


def test1(network, alice_wallet, alice_address, OCEAN_address):
    class MyBToken(ContractBase):
        CONTRACT_NAME = "BToken"

        # super-simple functionality, because our main point here is to
        # test ContractBase itself, not a child class.
        def symbol(self) -> str:
            return self.contract_concise.symbol()

    # does the super-simple functionality work?
    token = MyBToken(OCEAN_address)
    assert token.symbol() == "OCEAN"

    # now test ContractBase itself...

    # FIXME
