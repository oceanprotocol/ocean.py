#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from web3 import Web3

from ocean_lib.ocean import util
from ocean_lib.ocean.util import get_address_of_type, get_ocean_token_address


@pytest.mark.unit
def test_get_ocean_token_address(config):
    addresses = util.get_contracts_addresses(config)
    assert addresses
    assert isinstance(addresses, dict)
    assert "Ocean" in addresses

    address = get_ocean_token_address(config)
    assert Web3.isChecksumAddress(address), "It is not a checksum token address."
    assert address == Web3.toChecksumAddress(addresses["Ocean"])


@pytest.mark.unit
def test_get_address_by_type(config):
    addresses = util.get_contracts_addresses(config)

    address = get_address_of_type(config, "Ocean")
    assert Web3.isChecksumAddress(address), "It is not a checksum token address."
    assert address == Web3.toChecksumAddress(addresses["Ocean"])


@pytest.mark.unit
def test_get_address_of_type_failure(config):
    with pytest.raises(KeyError):
        get_address_of_type(config, "", "non-existent-key")
