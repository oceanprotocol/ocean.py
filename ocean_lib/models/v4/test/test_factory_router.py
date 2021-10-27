#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from web3 import exceptions

from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.factory_router import FactoryRouter
from ocean_lib.models.v4.bfactory import BFactory
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.web3_internal.constants import (
    ZERO_ADDRESS,
    ERC721_FACTORY_ADDRESS,
    ERC721_TEMPLATE,
    
    
)
from tests.resources.helper_functions import (
    get_publisher_wallet,
    get_consumer_wallet,
    get_another_consumer_wallet,
)

def test_confirm_ocean_added_to_mapping(web3):
    # deploy factoury router
    #poolTemplate = BFactory(web3=web3,address=web3.eth.accounts[0]).new_bpool(from_wallet=web3.eth.accounts[0])
    
    factory_router = FactoryRouter(web3=web3,address=ERC721_TEMPLATE)
    #deployed = factory_router.deploy()
    #print(deployed)
    assert 0
