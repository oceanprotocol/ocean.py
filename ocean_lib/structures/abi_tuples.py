#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Defines NamedTuples `Stakes`, `OrderData`, `Operations`"""
from enum import Enum
from typing import NamedTuple


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

Stakes = NamedTuple(
    "Stakes",
    [
        ("pool_address", str),
        ("token_amount_in", int),
        ("min_pool_amount_out", int),
    ],
)

OrderData = NamedTuple(
    "OrderData",
    [
        ("token_address", str),
        ("consumer", str),
        ("service_index", int),
        ("provider_fees", tuple),
        ("consume_fees", tuple),
    ],
)


MetadataProof = NamedTuple(
    "MetadataProof",
    [("validator_address", str), ("v", int), ("r", bytes), ("s", bytes)],
)
