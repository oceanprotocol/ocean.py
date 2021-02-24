#  Copyright 2021 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_lib.web3_internal.contract_handler import ContractHandler

_NETWORK = "ganache"

def test_get_contracts_addresses__empty_path():
    assert ContractHandler.get_contracts_addresses(
        _NETWORK, address_file=None) is None
    
def test_get_contracts_addresses__nonexistent_path():    
    ContractHandler.get_contracts_addresses(
        _NETWORK, address_file="/bin/foo/bar/tralala") is None

def test_get_contracts_addresses__custom_network(tmp_path):
    #tmp_path:pathlib.Path is special pytest feature

    #create & fill test file
    d = tmp_path / "subdir"
    d.mkdir()
    address_file = d / "address.json"
    address_file.write_text('{"my_custom_network" : "myvals"}')

    #the main test
    network_addresses = ContractHandler.get_contracts_addresses(
        network="my_custom_network", address_file=address_file)
    assert network_addresses == "myvals"

def test_get_contracts_addresses__use_network_alias(tmp_path):
    #tmp_path:pathlib.Path is special pytest feature

    assert ContractHandler.network_alias == {"ganache" : "development"}

    #create & fill test file
    d = tmp_path / "subdir"
    d.mkdir()
    address_file = d / "address.json"
    address_file.write_text('{"development" : "myvals"}') #not "ganache"

    #the main test
    network_addresses = ContractHandler.get_contracts_addresses(
        network="ganache", address_file=address_file)
    assert network_addresses == "myvals"

