#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from ocean_lib.web3_internal.contract_handler import ContractHandler
from web3.exceptions import InvalidAddress


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

