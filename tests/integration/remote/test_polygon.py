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
def test_ocean_tx__create(tmp_path, monkeypatch):
    """On Polygon, do a simple Ocean tx: create"""
    monkeypatch.delenv("ADDRESS_FILE")
    # setup
    connect_to_network("polygon-main")

    config = get_config_dict("polygon-main")
    ocean = Ocean(config)

    accounts.clear()
    (alice_wallet, _) = util.get_wallets()

    # Do a simple-as-possible test that uses ocean stack, while accounting for gotchas
    util.do_ocean_tx_and_handle_gotchas(ocean, alice_wallet)
