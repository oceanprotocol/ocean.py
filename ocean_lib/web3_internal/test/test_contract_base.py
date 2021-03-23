#  Copyright 2021 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import pytest
from enforce_typing import enforce_types

from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.wallet import Wallet
from web3.contract import ConciseContract


@enforce_types
class MyFactory(ContractBase):
    CONTRACT_NAME = "DTFactory"

    # super-simple functionality, because our main point here is to
    # test ContractBase itself, not a child class.
    def createToken(
        self, blob: str, name: str, symbol: str, cap: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "createToken", (blob, name, symbol, cap), from_wallet
        )


def test_name_is_None():
    with pytest.raises(AssertionError):
        # self.name will become None, triggering the error
        ContractBase(None)


def test_bad_abi_path():
    ContractHandler.artifacts_path = ""  # empty value
    with pytest.raises(AssertionError):
        # input abi_path of None will get it to use value in ContractHandler,
        # but since we've forced that empty it should raise an error
        MyFactory(address=None, abi_path=None)


def test_nochild():
    with pytest.raises(AssertionError):
        ContractBase(None)


def test_main(network, alice_wallet, alice_address, dtfactory_address):

    # test super-simple functionality of child
    factory = MyFactory(dtfactory_address)
    factory.createToken("foo_blob", "DT1", "DT1", to_base_18(1000), alice_wallet)

    # test attributes
    assert factory.name == "DTFactory"
    assert isinstance(factory.contract_concise, ConciseContract)
    assert factory.contract is not None
    assert factory.contract.address == dtfactory_address

    # test methods
    assert "configured_address" in dir(factory)
    assert factory.contract_name == "DTFactory"
    assert factory.address == dtfactory_address
    assert factory.events

    # FIXME: still need to test other methods
