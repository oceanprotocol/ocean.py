#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import warnings

import brownie.network
import pytest
from brownie.network import accounts, priority_fee

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.utils import connect_to_network

from . import util


@pytest.mark.integration
def test_ocean_tx__create_data_nft(tmp_path):
    """On Polygon, do a simple Ocean tx: create_data_nft"""
    # setup
    connect_to_network("polygon")
    util.set_aggressive_gas_fees()

    config = util.remote_config_polygon(tmp_path)
    ocean = Ocean(config)

    accounts.clear()
    (alice_wallet, _) = util.get_wallets()
    
    # Do a simple-as-possible test that uses ocean stack, while accounting for gotchas
    util.do_ocean_tx_and_handle_gotchas(ocean, alice_wallet)



