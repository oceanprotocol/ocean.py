#  Copyright 2021 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import copy

import pytest
from ocean_lib.web3_internal.contract_handler import ContractHandler
from web3.contract import ConciseContract
from web3.exceptions import InvalidAddress

_NETWORK = "ganache"

# ======================================================================
# test get_contracts_addresses() - local file


def test_get_contracts_addresses__bad_path1():
    addresses = ContractHandler.get_contracts_addresses(_NETWORK, address_file=None)
    assert addresses is None


def test_get_contracts_addresses__bad_path2():
    addresses = ContractHandler.get_contracts_addresses(
        _NETWORK, address_file="/bin/foo/bar/tralala"
    )
    assert addresses is None


def test_get_contracts_addresses__good_path_custom_network(tmp_path):
    # tmp_path:pathlib.Path is special pytest feature

    # create & fill test file
    d = tmp_path / "subdir"
    d.mkdir()
    address_file = d / "address.json"
    address_file.write_text('{"my_custom_network" : "myvals"}')

    # the main test
    addresses = ContractHandler.get_contracts_addresses(
        network="my_custom_network", address_file=address_file
    )
    assert addresses == "myvals"


def test_get_contracts_addresses__good_path_use_network_alias(tmp_path):
    assert ContractHandler.network_alias == {"ganache": "development"}

    # create & fill test file
    d = tmp_path / "subdir"
    d.mkdir()
    address_file = d / "address.json"
    address_file.write_text('{"development" : "myvals"}')  # not "ganache"

    # the main test
    addresses = ContractHandler.get_contracts_addresses(
        network="ganache", address_file=address_file
    )
    assert addresses == "myvals"


# ======================================================================
# test get_contracts_addresses() - remote file specified by url


def test_get_contracts_addresses__good_url_but_not_json():
    # the url exists, but content isn't structured for json
    address_file = "https://raw.githubusercontent.com/oceanprotocol/ocean.py/master/READMEs/developers.md"
    addresses = ContractHandler.get_contracts_addresses(
        network="rinkeby", address_file=address_file
    )
    assert addresses is None


def test_get_contracts_addresses__bad_url():
    address_file = "https://foobar"
    addresses = ContractHandler.get_contracts_addresses(
        network="rinkeby", address_file=address_file
    )
    assert addresses is None


def test_get_contracts_addresses__good_url_json_ready(remote_address_file):
    # get data from the actual 'contracts' repo
    addresses = ContractHandler.get_contracts_addresses(
        network="rinkeby", address_file=remote_address_file
    )
    assert addresses["DTFactory"][:2] == "0x"


def test_get_contracts_addresses__example_config(network, example_config):
    # ensure we're testing locally
    assert network in ["ganache", "development"]

    # do we get addresses for every contract?
    addresses = ContractHandler.get_contracts_addresses(
        network, example_config.address_file
    )
    assert set(addresses.keys()) == set(
        ["DTFactory", "BFactory", "FixedRateExchange", "Metadata", "Ocean"]
    )

    # are address values sane?
    for address in addresses.values():
        assert address[0:2] == "0x"


# ======================================================================
# test ABIs & artifacts


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


def test_get_unhappy_path():
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


def test_load__name_only():
    assert "DTFactory" not in ContractHandler._contracts

    contract = ContractHandler._load("DTFactory")

    assert ContractHandler._contracts["DTFactory"] == contract


def test_load__name_and_address(network, example_config):
    assert "DTFactory" not in ContractHandler._contracts

    addresses = ContractHandler.get_contracts_addresses(
        network, example_config.address_file
    )
    target_address = addresses["DTFactory"]
    contract = ContractHandler._load("DTFactory", target_address)

    assert ContractHandler._contracts["DTFactory"] == contract
