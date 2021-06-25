#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import copy
import os

import pytest
from ocean_lib.web3_internal.contract_handler import ContractHandler
from web3.contract import ConciseContract
from web3.exceptions import InvalidAddress

_NETWORK = "ganache"


def test_get_unhappy_paths():
    """Test that some erroneous artifacts paths can not be set (sad flows)."""
    with pytest.raises(TypeError):
        ContractHandler.get("foo name")

    with pytest.raises(TypeError):
        ContractHandler.get("foo name", "foo address")

    with pytest.raises(InvalidAddress):
        ContractHandler.get("DataTokenTemplate", "foo address")


def test_get_and_has__name_only():
    """Tests get() and has() from name-only queries, which also call _load() and read_abi_from_file()."""
    contract = ContractHandler.get("DataTokenTemplate")
    assert contract.address[:2] == "0x", "Wrong format for addresses."
    assert "totalSupply" in str(
        contract.abi
    ), "Contract abi does not have totalSupply function."

    assert ContractHandler.has("DataTokenTemplate")
    assert not ContractHandler.has("foo name")


def test_get_and_has__name_and_address(network, example_config):
    """Tests get() and has() from (name, address) queries, which also call _load() and read_abi_from_file()."""
    addresses = ContractHandler.get_contracts_addresses(
        network, example_config.address_file
    )
    target_address = addresses["DTFactory"]

    contract = ContractHandler.get("DTFactory", target_address)
    assert "createToken" in str(
        contract.abi
    ), "Contract abi does not have createToken function."
    assert contract.address == addresses["DTFactory"]

    assert ContractHandler.has("DTFactory", target_address)
    assert not ContractHandler.has("foo name", "foo address")
    assert not ContractHandler.has("foo name", contract.address)
    assert not ContractHandler.has("DTFactory", "foo address")


def test_get_concise_contract():
    """Tests that a concise contract can be retrieved from a DataTokenTemplate."""
    contract_concise = ContractHandler.get_concise_contract("DataTokenTemplate")
    assert isinstance(
        contract_concise, ConciseContract
    ), "The concise contract does have an unknown instance."


def test_set():
    """Tests setting of a DataTokenTemplate on a Contract."""
    contract = ContractHandler.get("DataTokenTemplate")
    address = contract.address

    ContractHandler.set("second_name", contract)

    # result format is a tuple of (contract, contract_concise)
    # did it store in (name) key?
    result = ContractHandler._contracts["second_name"]
    assert len(result) == 2
    assert result[0].address == address
    assert isinstance(result[1], ConciseContract)

    # did it store in (name, address) key?
    result2 = ContractHandler._contracts[("second_name", address)]
    assert result2 == result
