#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from web3.gas_strategies.time_based import fast_gas_price_strategy

from ocean_lib.ocean.util import get_web3
from ocean_lib.web3_internal.constants import ENV_GAS_PRICE, ENV_MAX_GAS_PRICE
from ocean_lib.web3_internal.utils import (
    generate_multi_value_hash,
    get_chain_id,
    get_gas_price,
    prepare_prefixed_hash,
    get_chain_id_from_url,
)


@pytest.mark.unit
def test_get_chain_id(web3):
    assert get_chain_id(web3) == 8996


@pytest.mark.unit
def test_generate_multi_value_hash(alice_address, alice_private_key):
    with pytest.raises(AssertionError):
        generate_multi_value_hash(["more", "types", "than"], ["values"])

    expected = "0x88a01ece43955f72807bbe1969921b7f6d7c01413fc08bf795c9f6ee04bb0d60"
    assert alice_private_key == os.getenv("TEST_PRIVATE_KEY1")
    assert alice_address == "0x02354A1F160A3fd7ac8b02ee91F04104440B28E7"
    tested = generate_multi_value_hash(["address"], [alice_address]).hex()
    assert tested == expected, "The tested address is not the expected one."


@pytest.mark.unit
def test_prepare_fixed_hash():
    expected = "0x5662cc8481d004c9aff44f15f3ed133dd54f9cfba0dbf850f69b1cbfc50145bf"
    assert (
        prepare_prefixed_hash("0x0").hex() == expected
    ), "The address is not the expected one."


@pytest.mark.unit
def test_gas_scaling_factor(web3, monkeypatch):
    monkeypatch.setenv("GAS_SCALING_FACTOR", "5.0")
    gas_price1 = web3.eth.gas_price
    gas_price_with_scaling = get_gas_price(web3, tx=dict())
    assert gas_price_with_scaling["gasPrice"] == gas_price1 * 5

    web3.eth.set_gas_price_strategy(fast_gas_price_strategy)
    gas_price2 = web3.eth.generate_gas_price()

    monkeypatch.delenv("GAS_SCALING_FACTOR")
    polygon_web3 = get_web3("https://polygon-rpc.com")
    polygon_gas = polygon_web3.eth.gas_price
    assert polygon_gas > gas_price2

    monkeypatch.setenv(ENV_GAS_PRICE, "30000")
    gas_price_with_scaling = get_gas_price(web3, tx=dict())
    assert gas_price_with_scaling["gasPrice"] == 30000

    monkeypatch.setenv(ENV_GAS_PRICE, "30000")
    monkeypatch.setenv(ENV_MAX_GAS_PRICE, "80000")
    gas_price_with_scaling = get_gas_price(web3, tx=dict())
    assert gas_price_with_scaling["gasPrice"] == 30000


def test_chain_id_from_url(config):
    chain_id = get_chain_id_from_url(config["RPC_URL"])
    assert isinstance(chain_id, int)
    assert chain_id == 8996
