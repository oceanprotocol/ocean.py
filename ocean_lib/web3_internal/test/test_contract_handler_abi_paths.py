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


def test_set_artifacts_path__deny_change_to_empty():
    """Tests can not set empty artifacts path."""
    path_before = copy.copy(ContractHandler.artifacts_path)
    assert path_before is not None
    assert ContractHandler._contracts

    ContractHandler.set_artifacts_path(None)  # it should deny this

    assert ContractHandler.artifacts_path == path_before
    assert ContractHandler._contracts  # cache should *not* have reset


def test_set_artifacts_path__deny_change_to_same():
    """Tests can not set unchanged artifacts path."""
    path_before = copy.copy(ContractHandler.artifacts_path)
    assert path_before is not None
    assert ContractHandler._contracts

    ContractHandler.set_artifacts_path(path_before)

    assert ContractHandler.artifacts_path == path_before
    assert ContractHandler._contracts  # cache should *not* have reset


def test_set_artifacts_path__allow_change():
    """Tests that a correct artifacts path can be set (happy flow)."""
    path_before = copy.copy(ContractHandler.artifacts_path)
    assert path_before is not None
    assert ContractHandler._contracts

    ContractHandler.set_artifacts_path("new path")

    assert ContractHandler.artifacts_path == "new path"
    assert not ContractHandler._contracts  # cache should have reset


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
    assert contract.address[:2] == "0x"
    assert "totalSupply" in str(contract.abi)

    assert ContractHandler.has("DataTokenTemplate")
    assert not ContractHandler.has("foo name")


def test_get_and_has__name_and_address(network, example_config):
    """Tests get() and has() from (name, address) queries, which also call _load() and read_abi_from_file()."""
    addresses = ContractHandler.get_contracts_addresses(
        network, example_config.address_file
    )
    target_address = addresses["DTFactory"]

    contract = ContractHandler.get("DTFactory", target_address)
    assert "createToken" in str(contract.abi)
    assert contract.address == addresses["DTFactory"]

    assert ContractHandler.has("DTFactory", target_address)
    assert not ContractHandler.has("foo name", "foo address")
    assert not ContractHandler.has("foo name", contract.address)
    assert not ContractHandler.has("DTFactory", "foo address")


def test_get_concise_contract():
    """Tests that a concise contract can be retrieved from a DataTokenTemplate."""
    contract_concise = ContractHandler.get_concise_contract("DataTokenTemplate")
    assert isinstance(contract_concise, ConciseContract)


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


def test_load__fail_empty_artifacts_path():
    """Tests that an empty artifacts path can not be loaded."""
    ContractHandler.artifacts_path = None
    with pytest.raises(AssertionError):
        ContractHandler._load("DTFactory")


def test_load__fail_malformed_eth_address():
    """Tests that an invalid ETH addres makes the Contract unloadable."""
    with pytest.raises(InvalidAddress):
        ContractHandler._load("DTFactory", "foo address")


def test_load__fail_wrong_eth_address():
    """Tests that a different ETH address from the Contract makes it unloadable."""
    random_eth_address = "0x0daA8DBE3f6760990c886F37E39A5696A4a911F0"
    with pytest.raises(InvalidAddress):
        ContractHandler._load("DTFactory", random_eth_address)


def test_load__name_only():
    """Tests load() from name-only query."""
    assert "DTFactory" not in ContractHandler._contracts

    contract = ContractHandler._load("DTFactory")
    assert ContractHandler._contracts["DTFactory"] == contract


def test_load__name_and_address(network, example_config):
    """Tests load() from (name, address) query."""
    addresses = ContractHandler.get_contracts_addresses(
        network, example_config.address_file
    )
    target_address = addresses["DTFactory"]

    test_tuple = ("DTFactory", target_address)

    assert test_tuple not in ContractHandler._contracts

    contract = ContractHandler._load("DTFactory", target_address)

    assert ContractHandler._contracts[test_tuple] == contract


def test_read_abi_from_file__example_config__happy_path(example_config):
    """Tests a correct reading of abi from file (happy path)."""
    assert "https" not in str(ContractHandler.artifacts_path)

    contract_definition = ContractHandler.read_abi_from_file(
        "DTFactory", ContractHandler.artifacts_path
    )
    assert contract_definition["contractName"] == "DTFactory"
    assert "createToken" in str(contract_definition["abi"])


def test_read_abi_from_file__example_config__bad_contract_name(example_config):
    """Tests an incorrect reading of abi from file (sad path)."""
    assert "https" not in str(ContractHandler.artifacts_path)

    base_path = ContractHandler.artifacts_path
    target_filename = os.path.join(base_path, "DTFactoryFOO.json")
    assert not os.path.exists(target_filename)  # should fail due to this

    contract_definition = ContractHandler.read_abi_from_file(
        "DTFactoryFOO", ContractHandler.artifacts_path
    )
    assert contract_definition is None
