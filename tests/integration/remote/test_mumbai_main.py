#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import random
import time

from brownie.network import accounts

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.utils import connect_to_network

from . import util


def test_nonocean_tx(tmp_path):
    """Do a simple non-Ocean tx on Mumbai. Only use Ocean config"""
    # setup
    connect_to_network("polygon-test")
    util.set_aggressive_gas_fees()

    config = util.remote_config_mumbai(tmp_path)
    ocean = Ocean(config)
    accounts.clear()
    (alice_wallet, bob_wallet) = util.get_wallets()

    # Do a simple-as-possible test that uses ocean stack, while accounting for gotchas
    util.do_nonocean_tx_and_handle_gotchas(ocean, alice_wallet, bob_wallet)


def test_ocean_tx__create_data_nft(tmp_path):
    """On Mumbai, do a simple Ocean tx: create_data_nft"""
    # setup
    connect_to_network("polygon-test")
    util.set_aggressive_gas_fees()

    config = util.remote_config_mumbai(tmp_path)
    ocean = Ocean(config)

    accounts.clear()
    (alice_wallet, _) = util.get_wallets()

    # Do a simple-as-possible test that uses ocean stack, while accounting for gotchas
    util.do_ocean_tx_and_handle_gotchas(ocean, alice_wallet)
