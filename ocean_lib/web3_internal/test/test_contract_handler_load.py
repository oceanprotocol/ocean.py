#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_lib.web3_internal.web3helper import Web3Helper
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

@pytest.mark.nosetup_all 
def test_disable_setup_all_1(monkeypatch):
    """Test that conftest::setup_all() was *not* called due to decorator"""
    c = ConfigProvider()
    assert ConfigProvider._config is None
    assert Web3Provider._web3 is None
    assert ContractHandler._contracts == dict()
    assert ContractHandler.artifacts_path is None

def test_disable_setup_all_2(monkeypatch):
    """Test that setup_all() *was* called, since no decorator to disable"""
    assert ConfigProvider._config is not None
    assert Web3Provider._web3 is not None
    assert ContractHandler._contracts != dict()
    assert ContractHandler.artifacts_path is not None

@pytest.mark.nosetup_all #disable call to conftest.py::setup_all()
def test_issue185(monkeypatch):
    #disable envvars that imports may have brought in
    import os
            
    if os.getenv('CONFIG_FILE'):
        monkeypatch.delenv('CONFIG_FILE')
    assert os.getenv('CONFIG_FILE') is None, "can't have CONFIG_FILE envvar set"


    if os.getenv('ARTIFACTS_PATH'):
        monkeypatch.delenv('ARTIFACTS_PATH')
    assert os.getenv('ARTIFACTS_PATH') is None, "can't have ARTIFACTS_PATH envvar set"
    
    #rest of test
    from ocean_lib.ocean.ocean import Ocean
    from ocean_lib.web3_internal.wallet import Wallet
    
    private_key = os.getenv('TEST_PRIVATE_KEY1')
    config = {'network': os.getenv('NETWORK_URL')}
    ocean = Ocean(config)

    print("create wallet: begin")
    wallet = Wallet(ocean.web3, private_key=private_key)
    print(f"create wallet: done. Its address is {wallet.address}")

    print("create datatoken: begin.")
    datatoken = ocean.create_data_token("Dataset name", "dtsymbol", from_wallet=wallet) 

