#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3.gas_strategies.time_based import fast_gas_price_strategy

from ocean_lib.web3_internal.constants import ENV_GAS_PRICE, ENV_MAX_GAS_PRICE
from ocean_lib.web3_internal.contract_utils import get_web3
from ocean_lib.web3_internal.utils import get_gas_price


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
