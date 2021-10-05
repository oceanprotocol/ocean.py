#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""
Defines NamedTuples `NftCreateData`, `ErcCreateData`, `PoolData`, `FixedData`
"""
from typing import NamedTuple, List

NftCreateData = NamedTuple(
    "NftCreateData", [("name", str), ("symbol", str), ("template_index", int)]
)

ErcCreateData = NamedTuple(
    "ErcCreateData",
    [
        ("template_index", int),
        ("strings", List[str]),
        ("addresses", List[str]),
        ("uints", List[int]),
        ("bytess", bytes),
    ],
)

PoolData = NamedTuple(
    "PoolData",
    [
        ("controller", str),
        ("base_token", str),
        ("ss_params", List[int]),
        ("bt_sender", str),
        ("swap_fees", List[int]),
        ("market_fee_collector", str),
        ("publisher", str),
    ],
)

BPoolData = NamedTuple(
    "BPoolData",
    [
        ("controller", str),
        ("tokens", List[str]),
        ("publisher", str),
        ("ss_params", List[int]),
        ("swap_fees", List[int]),
        ("market_fee_collector", str),
    ],
)

BPoolInitialized = NamedTuple(
    "BPoolInitialized",
    [
        ("controller", str),
        ("factory", str),
        ("swap_fees", List[int]),
        ("public_swap", bool),
        ("finalized", bool),
        ("tokens", List[str]),
        ("fee_collectors", List[str]),
    ],
)

FixedData = NamedTuple(
    "FixedData",
    [
        ("fixed_price_address", str),
        ("base_token", str),
        ("bt_decimals", int),
        ("exchange_rate", int),
        ("owner", str),
        ("market_fee", int),
        ("market_fee_collector", str),
    ],
)
