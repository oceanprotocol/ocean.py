#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from brownie.network import accounts

from ocean_lib.example_config import get_config_dict
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.utils import connect_to_network

from . import util


@pytest.mark.integration
def test_ocean_tx__create_data_nft(tmp_path, monkeypatch):
    """On Polygon, do a simple Ocean tx: create_data_nft"""
    monkeypatch.delenv("ADDRESS_FILE")
    # setup
    connect_to_network("polygon-main")
    util.set_aggressive_gas_fees()

    config = get_config_dict("polygon")
    ocean = Ocean(config)

    accounts.clear()
    (alice_wallet, _) = util.get_wallets()

    # Do a simple-as-possible test that uses ocean stack, while accounting for gotchas
    util.do_ocean_tx_and_handle_gotchas(ocean, alice_wallet)
