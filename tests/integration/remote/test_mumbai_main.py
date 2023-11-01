#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from ocean_lib.example_config import get_config_dict
from ocean_lib.ocean.ocean import Ocean

from . import util


def _get_mumbai_rpc():
    infura_id = os.getenv("WEB3_INFURA_PROJECT_ID")

    if not infura_id:
        return "https://rpc-mumbai.maticvigil.com"

    return f"https://polygon-mumbai.infura.io/v3/{infura_id}"


def test_nonocean_tx(tmp_path, monkeypatch):
    """Do a simple non-Ocean tx on Mumbai. Only use Ocean config"""
    monkeypatch.delenv("ADDRESS_FILE")
    # setup

    config = get_config_dict(_get_mumbai_rpc())
    ocean = Ocean(config)
    (alice_wallet, bob_wallet) = util.get_wallets()

    # Do a simple-as-possible test that uses ocean stack, while accounting for gotchas
    util.do_nonocean_tx_and_handle_gotchas(ocean, alice_wallet, bob_wallet)


def test_ocean_tx__create(tmp_path, monkeypatch):
    """On Mumbai, do a simple Ocean tx: create"""
    monkeypatch.delenv("ADDRESS_FILE")
    # setup

    config = get_config_dict(_get_mumbai_rpc())
    ocean = Ocean(config)

    (alice_wallet, _) = util.get_wallets()

    # Do a simple-as-possible test that uses ocean stack, while accounting for gotchas
    util.do_ocean_tx_and_handle_gotchas(ocean, alice_wallet)
