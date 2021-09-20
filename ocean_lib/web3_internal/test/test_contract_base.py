#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from enforce_typing import enforce_types
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet
from web3.contract import ContractCaller


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


def test_name_is_None(web3):
    with pytest.raises(AssertionError):
        # self.name will become None, triggering the error
        ContractBase(web3, None)


def test_nochild(web3):
    with pytest.raises(AssertionError):
        ContractBase(web3, None)


def test_main(network, alice_wallet, alice_ocean, dtfactory_address, web3):

    # test super-simple functionality of child
    factory = MyFactory(web3, dtfactory_address)
    factory.createToken("foo_blob", "DT1", "DT1", to_wei(1000), alice_wallet)

    # test attributes
    assert factory.name == "DTFactory"
    assert isinstance(factory.contract.caller, ContractCaller)
    assert factory.contract is not None
    assert factory.contract.address == dtfactory_address
    assert ContractBase.to_checksum_address(dtfactory_address) == dtfactory_address

    # test methods
    assert "configured_address" in dir(factory)
    assert factory.contract_name == "DTFactory"
    assert factory.address == dtfactory_address
    assert factory.events
    assert str(factory) == f"{factory.contract_name} @ {factory.address}"
    assert (
        "createToken" in factory.function_names
    ), "The function createToken from the contract does not exist."
    assert "getCurrentTokenCount" in factory.function_names
    assert "getTokenTemplate" in factory.function_names
    assert not factory.is_tx_successful("nohash")
    with pytest.raises(ValueError):
        assert factory.get_event_signature("noevent")

    assert factory.subscribe_to_event("TokenCreated", 30, None) is None
    assert factory.get_event_argument_names("TokenCreated") == ()
    block = web3.eth.block_number
    block_confirmations = alice_ocean.config.block_confirmations.value
    assert (
        len(
            factory.get_event_logs(
                "TokenCreated",
                block - block_confirmations,
                block - block_confirmations,
                None,
            )
        )
        == 1
    ), "The token was not created."
    log = factory.get_event_log(
        "TokenCreated", block - block_confirmations, block - block_confirmations, None
    )
    assert len(log) == 1, "The token was not created."
    assert log[0]["event"] == "TokenCreated"
    assert log[0]["address"] == dtfactory_address

    with pytest.raises(TypeError):
        ContractBase.getLogs(None)


def test_static_functions(web3):
    assert (
        ContractBase.get_tx_receipt(web3, "nohash") is None
    ), "The transaction receipt exists for the wrong hash."


def test_gas_price(web3, alice_wallet, dtfactory_address, monkeypatch):
    monkeypatch.setenv("GAS_PRICE", "1")
    factory = MyFactory(web3, dtfactory_address)
    assert factory.createToken(
        "foo_blob", "DT1", "DT1", to_wei(1000), alice_wallet
    ), "The token could not be created by configuring the gas price env var."
