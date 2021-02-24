#  Copyright 2021 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_lib.web3_internal.contract_handler import ContractHandler

_NETWORK = "ganache"

def test_get_contracts_addresses__bad_path():
    assert ContractHandler.get_contracts_addresses(
        _NETWORK, address_file=None) is None
    
def test_get_contracts_addresses__bad_path2():    
    ContractHandler.get_contracts_addresses(
        _NETWORK, address_file="/bin/foo/bar/tralala") is None

def test_get_contracts_addresses__good_path_custom_network(tmp_path):
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

def test_get_contracts_addresses__good_path_use_network_alias(tmp_path):
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

def test_get_contracts_addresses__good_url_json_ready(tmp_path):
    #get data from the actual 'contracts' repo
    address_file = "https://raw.githubusercontent.com/oceanprotocol/contracts/master/artifacts/address.json"
    network_addresses = ContractHandler.get_contracts_addresses(
        network="rinkeby", address_file=address_file)
    assert network_addresses["DTFactory"][:2] == "0x"
    
def test_get_contracts_addresses__good_url_but_not_json(tmp_path):
    #the url exists, but content isn't structured for json
    address_file = "https://raw.githubusercontent.com/oceanprotocol/ocean.py/master/READMEs/developers.md"
    assert ContractHandler.get_contracts_addresses(
        network="rinkeby", address_file=address_file) is None
    
def test_get_contracts_addresses__bad_url(tmp_path):
    address_file = "https://foobar"
    assert ContractHandler.get_contracts_addresses(
        network="rinkeby", address_file=address_file) is None
