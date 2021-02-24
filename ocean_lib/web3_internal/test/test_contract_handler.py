#  Copyright 2021 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_lib.web3_internal.contract_handler import ContractHandler

_NETWORK = "ganache"

def test_get_contracts_addresses__empty_address_path():
    assert ContractHandler.get_contracts_addresses(
        _NETWORK, address_file=None) is None
    
def test_get_contracts_addresses__nonexistent_address_path():
    assert ContractHandler.get_contracts_addresses(
        _NETWORK, address_file="not a path") is None
    
    assert ContractHandler.get_contracts_addresses(
        _NETWORK, address_file="/bin/foo/bar/tralala") is None
