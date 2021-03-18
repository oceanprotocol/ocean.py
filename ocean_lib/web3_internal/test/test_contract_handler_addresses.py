#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""
This file does tests for method "get_contracts_addresses()", that's all.
"""

import copy
import os

from ocean_lib.web3_internal.contract_handler import ContractHandler

_NETWORK = "ganache"


def test_get_contracts_addresses_empty():
    """Tests that an empty address can not be set on a Contract."""
    addresses = ContractHandler.get_contracts_addresses(_NETWORK, address_file=None)
    assert addresses is None


def test_get_contracts_addresses_bad_path():
    """Tests that a non-existent address can not be set on a Contract."""
    addresses = ContractHandler.get_contracts_addresses(
        _NETWORK, address_file="/bin/foo/bar/tralala"
    )
    assert addresses is None


def test_get_contracts_addresses_good_path_custom_network(tmp_path):
    """Tests that an address with a custom network can be set on a Contract."""
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


def test_get_contracts_addresses_good_path_use_network_alias(tmp_path):
    """Tests that an address with a network alias can be set on a Contract."""
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


def test_get_contracts_addresses_example_config(network, example_config):
    """Tests that an address can be set if using testing config."""
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
