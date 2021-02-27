#  Copyright 2021 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_lib.web3_internal.contract_handler import ContractHandler

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


# ======================================================================
# test ABIs & artifacts

# FIXME
