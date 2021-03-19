#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import os
import pytest

from ocean_lib.config_provider import ConfigProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.btoken import BToken #BToken is ERC20
from ocean_lib.ocean.deploy import deploy_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import get_web3_connection_provider
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider
    
@pytest.mark.nosetup_all  # disable call to conftest.py::setup_all()
def test1():
    #ocean instance
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    Web3Provider.init_web3(provider=get_web3_connection_provider(config.network_url))
    ContractHandler.set_artifacts_path(config.artifacts_path)
    
    ocean = Ocean(config)
    OCEAN_address_before = ocean.OCEAN_address
    
    #deploy, distribute, etc
    deploy_fake_OCEAN()

    #test: OCEAN address should have changed
    OCEAN_address_after = ocean.OCEAN_address
    assert OCEAN_address_before != OCEAN_address_after
    
    #test: TEST_PRIVATE_KEY{1,2} should each hold OCEAN
    wallet1 = Wallet(ocean.web3, private_key=os.getenv('TEST_PRIVATE_KEY1'))
    wallet2 = Wallet(ocean.web3, private_key=os.getenv('TEST_PRIVATE_KEY2'))
    
    OCEAN_after = BToken(ocean.OCEAN_address)
    assert OCEAN_after.balanceOf(wallet1.address) > 0
    assert OCEAN_after.balanceOf(wallet2.address) > 0
    

