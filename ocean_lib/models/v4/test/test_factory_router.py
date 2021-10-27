#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from web3 import exceptions

from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.factory_router import FactoryRouter
from ocean_lib.web3_internal.contract_utils import get_contracts_addresses
from ocean_lib.models.v4.bfactory import BFactory
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import get_factory_deployer_wallet
from ocean_lib.config import Config
import os
_NETWORK = "ganache"
from ocean_lib.web3_internal.constants import (
    POOL_TEMPLATE_ADDRESS,
    ZERO_ADDRESS,
    ERC721_FACTORY_ADDRESS,
    ERC721_TEMPLATE,
    OCEAN_ADDRESS_V4,
)
from tests.resources.helper_functions import (
    get_publisher_wallet,
    get_consumer_wallet,
    get_another_consumer_wallet,
)


