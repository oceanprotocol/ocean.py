#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Defines NamedTuples `PoolData`, `FixedData`,
`DispenserData`, `Operations`"""
from enum import Enum
from typing import List, NamedTuple

PoolData = NamedTuple(
    "PoolData",
    [("ss_params", List[int]), ("swap_fees", List[int]), ("addresses", List[str])],
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
        ("with_mint", bool),
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

Stakes = NamedTuple(
    "Stakes",
    [
        ("pool_address", str),
        ("token_amount_in", int),
        ("min_pool_amount_out", int),
    ],
)

ProviderFees = NamedTuple(
    "ProviderFees",
    [
        ("provider_fee_address", str),
        ("provider_fee_token", str),
        ("provider_fee_amount", int),
        ("v", str),
        ("r", str),
        ("s", str),
        ("valid_until", int),
        ("provider_data", bytes),
    ],
)

ConsumeFees = NamedTuple(
    "ConsumeFees",
    [
        ("consumer_market_fee_address", str),
        ("consumer_market_fee_token", str),
        ("consumer_market_fee_amount", int),
    ],
)

OrderData = NamedTuple(
    "OrderData",
    [
        ("token_address", str),
        ("consumer", str),
        ("service_index", int),
        ("provider_fees", ProviderFees),
        ("consume_fees", ConsumeFees),
    ],
)

OrderParams = NamedTuple(
    "OrderParams",
    [
        ("consumer", str),
        ("service_index", int),
        ("provider_fees", ProviderFees),
        ("consume_fees", ConsumeFees),
    ],
)

MetadataProof = NamedTuple(
    "MetadataProof",
    [("validator_address", str), ("v", int), ("r", bytes), ("s", bytes)],
)
