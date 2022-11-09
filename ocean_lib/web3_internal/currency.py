#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from decimal import ROUND_DOWN, Context, Decimal

from ocean_lib.web3_internal.constants import MAX_UINT256

"""decimal.Context tuned to accomadate MAX_WEI.

* precision=78 because there are 78 digits in MAX_WEI (MAX_UINT256).
  Any lower and decimal operations like quantize throw an InvalidOperation error.
* rounding=ROUND_DOWN (towards 0, aka. truncate) to avoid issue where user
  removes 100% from a pool and transaction fails because it rounds up.
"""
ETHEREUM_DECIMAL_CONTEXT = Context(prec=78, rounding=ROUND_DOWN)


"""ERC20 tokens usually opt for a decimals value of 18, imitating the
relationship between Ether and Wei."""
DECIMALS_18 = 18

"""The minimum possible token amount on Ethereum-compatible blockchains, denoted in wei"""
MIN_WEI = 1

"""The maximum possible token amount on Ethereum-compatible blockchains, denoted in wei"""
MAX_WEI = MAX_UINT256

"""The minimum possible token amount on Ethereum-compatible blockchains, denoted in ether"""
MIN_ETHER = Decimal("0.000000000000000001")

"""The maximum possible token amount on Ethereum-compatible blockchains, denoted in ether"""
MAX_ETHER = Decimal(MAX_WEI).scaleb(-18, context=ETHEREUM_DECIMAL_CONTEXT)
