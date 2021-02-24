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

def test_get_contracts_addresses__real_path(tmp_path):
    #tmp_path is a pathlib.Path object
    #More info: https://docs.pytest.org/en/stable/tmpdir.html

    #create & fill test file
    d = tmp_path / "sub"
    d.mkdir()
    address_file = d / "address.json"
    file_content = '{"%s" : "my address values"}' % _NETWORK
    address_file.write_text(file_content)

    #the main test
    network_addresses = ContractHandler.get_contracts_addresses(
        _NETWORK, address_file=address_file)
    assert network_addresses == "my address values"

