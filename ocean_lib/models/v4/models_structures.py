#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Defines NamedTuples `NftCreateData`, `ErcCreateData`, `PoolData`, `BPoolData`, `BPoolInitialized`, `FixedData`,
`DispenserData`, `Operations`"""
from typing import NamedTuple, List
from enum import Enum

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
        ("bytess", List[bytes]),
    ],
)

PoolData = NamedTuple(
    "PoolData",
    [
        ("ss_params", List[int]),
        ("swap_fees", List[int]),
        ("addresses", List[str]),
    ],
)

BPoolData = NamedTuple(
    "BPoolData",
    [
        ("tokens", List[str]),
        ("ss_params", List[int]),
        ("swap_fees", List[int]),
        ("addresses", List[str]),
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

NewDataTokenCreated = NamedTuple(
    "NewDataTokenCreated",
    [
        ("data_token", str),
        ("base_token", str),
        ("pool_address", str),
        ("publisher_address", str),
        ("ss_params", List[int]),
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

DispenserData = NamedTuple(
    "DispenserData",
    [
        ("dispenser_address", str),
        ("data_token", str),
        ("max_tokens", int),
        ("max_balance", int),
        ("owner", str),
        ("allowed_swapper", str),
    ],
)


class OperationType(Enum):
    SwapExactIn = 0
    SwapExactOut = 1
    FixedRate = 2
    Dispenser = 3


Operations = NamedTuple(
    "Operations",
    [
        ("exchange_id", bytes),
        ("source", str),
        ("operation", OperationType),
        ("token_in", str),
        ("amounts_in", int),
        ("token_out", str),
        ("amounts_out", int),
        ("max_price", int),
    ],
)
