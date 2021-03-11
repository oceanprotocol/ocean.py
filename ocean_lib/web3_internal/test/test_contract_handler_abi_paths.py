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
    path_before = copy.copy(ContractHandler.artifacts_path)
    assert path_before is not None
    assert ContractHandler._contracts

    ContractHandler.set_artifacts_path(None)  # it should deny this

    assert ContractHandler.artifacts_path == path_before
    assert ContractHandler._contracts  # cache should *not* have reset


def test_set_artifacts_path__deny_change_to_same():
    path_before = copy.copy(ContractHandler.artifacts_path)
    assert path_before is not None
    assert ContractHandler._contracts

    ContractHandler.set_artifacts_path(path_before)

    assert ContractHandler.artifacts_path == path_before
    assert ContractHandler._contracts  # cache should *not* have reset


def test_set_artifacts_path__allow_change():
    path_before = copy.copy(ContractHandler.artifacts_path)
    assert path_before is not None
    assert ContractHandler._contracts

    ContractHandler.set_artifacts_path("new path")

    assert ContractHandler.artifacts_path == "new path"
    assert not ContractHandler._contracts  # cache should have reset


def test_get_unhappy_paths():
    with pytest.raises(TypeError):
        ContractHandler.get("foo name")

    with pytest.raises(TypeError):
        ContractHandler.get("foo name", "foo address")

    with pytest.raises(InvalidAddress):
        ContractHandler.get("DataTokenTemplate", "foo address")


def test_get_and_has__name_only():
    # test get() and has() from name-only queries,
    # which also call _load() and read_abi_from_file()
    contract = ContractHandler.get("DataTokenTemplate")
    assert contract.address[:2] == "0x"
    assert "totalSupply" in str(contract.abi)

    assert ContractHandler.has("DataTokenTemplate")
    assert not ContractHandler.has("foo name")


def test_get_and_has__name_and_address(network, example_config):
    # test get() and has() from (name, address) queries,
    # which also call _load() and read_abi_from_file()
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
    contract_concise = ContractHandler.get_concise_contract("DataTokenTemplate")
    assert isinstance(contract_concise, ConciseContract)


def test_set():
    contract = ContractHandler.get("DataTokenTemplate")
    address = contract.address

    ContractHandler.set("second_name", contract)

    # did it store in (name) key?
    tup = ContractHandler._contracts["second_name"]  # (contract, contract_concise)
    assert len(tup) == 2
    assert tup[0].address == address
    assert isinstance(tup[1], ConciseContract)

    # did it store in (name, address) key?
    tup2 = ContractHandler._contracts[("second_name", address)]
    assert tup2 == tup


def test_load__fail_empty_artifacts_path():
    ContractHandler.artifacts_path = None
    with pytest.raises(AssertionError):
        ContractHandler._load("DTFactory")


def test_load__fail_malformed_eth_address():
    with pytest.raises(InvalidAddress):
        ContractHandler._load("DTFactory", "foo address")


def test_load__fail_wrong_eth_address():
    random_eth_address = "0x0daA8DBE3f6760990c886F37E39A5696A4a911F0"
    with pytest.raises(InvalidAddress):
        ContractHandler._load("DTFactory", random_eth_address)


def test_load__name_only():
    # test load() from name-only query
    assert "DTFactory" not in ContractHandler._contracts

    contract = ContractHandler._load("DTFactory")

    assert ContractHandler._contracts["DTFactory"] == contract


def test_load__name_and_address(network, example_config):
    # test load() from (name, address) query
    addresses = ContractHandler.get_contracts_addresses(
        network, example_config.address_file
    )
    target_address = addresses["DTFactory"]

    tup = ("DTFactory", target_address)

    assert tup not in ContractHandler._contracts

    contract = ContractHandler._load("DTFactory", target_address)

    assert ContractHandler._contracts[tup] == contract


def test_read_abi_from_file__example_config__happy_path(example_config):
    assert "https" not in str(ContractHandler.artifacts_path)

    contract_definition = ContractHandler.read_abi_from_file(
        "DTFactory", ContractHandler.artifacts_path
    )
    assert contract_definition["contractName"] == "DTFactory"
    assert "createToken" in str(contract_definition["abi"])


def test_read_abi_from_file__example_config__bad_contract_name(example_config):
    assert "https" not in str(ContractHandler.artifacts_path)

    base_path = ContractHandler.artifacts_path
    target_filename = os.path.join(base_path, "DTFactoryFOO.json")
    assert not os.path.exists(target_filename)  # should fail due to this

    contract_definition = ContractHandler.read_abi_from_file(
        "DTFactoryFOO", ContractHandler.artifacts_path
    )
    assert contract_definition is None
