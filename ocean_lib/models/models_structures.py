#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Defines NamedTuples `PoolData`, `BPoolData`, `BPoolInitialized`, `FixedData`,
`DispenserData`, `Operations`"""
from enum import Enum
from typing import List, NamedTuple

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
    [("ss_params", List[int]), ("swap_fees", List[int]), ("addresses", List[str])],
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

FixedData = NamedTuple(
    "FixedData",
    [("fixed_price_address", str), ("addresses", List[str]), ("uints", List[int])],
)

DispenserData = NamedTuple(
    "DispenserData",
    [
        ("dispenser_address", str),
        ("max_tokens", int),
        ("max_balance", int),
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
        ("swap_market_fee", int),
        ("market_fee_address", int),
    ],
)

OrderData = NamedTuple(
    "OrderData",
    [
        ("token_address", str),
        ("consumer", str),
        ("service_index", int),
        ("provider_fee_address", str),
        ("provider_fee_token", str),
        ("provider_fee_amount", int),
        ("v", str),
        ("r", str),
        ("s", str),
        ("provider_data", bytes),
    ],
)
