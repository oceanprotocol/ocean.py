#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import random
from decimal import Decimal
from math import floor

from ocean_lib.models.bpool import BPool
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.web3_internal.currency import from_wei, to_wei

BPOOL_FUZZING_TESTS_NBR_OF_RUNS = 1


def get_random_max_token_amount_in(
    token_in: Datatoken, bpool: BPool, wallet_address: str
) -> int:
    """Returns a random amount of tokens of token_in that is less than the max_in_ratio_in of the pool and
    less than the balance of the wallet in the token_in"""
    result = floor(
        min(
            token_in.balanceOf(wallet_address),
            to_wei(
                from_wei(bpool.get_max_in_ratio())
                * from_wei(bpool.get_balance(token_in.address))
            ),
        )
        * Decimal(random.uniform(0, 1))
    )

    return result if result > 0 else 1


def get_random_max_token_amount_out(
    token_in: Datatoken, token_out: Datatoken, bpool: BPool, wallet_address: str
) -> int:
    """Returns a random amount of tokens of token_out that is less than the max_out_ratio_out of the pool and
    and less than the maximum amount of token_out that can be purchased by the wallet_address"""
    pool_token_out_balance = bpool.get_balance(token_out.address)
    max_out_ratio = bpool.get_max_out_ratio()
    max_out_ratio_limit = to_wei(
        from_wei(max_out_ratio) * from_wei(pool_token_out_balance)
    )
    result = floor(
        Decimal(random.uniform(0, 1))
        * min(
            bpool.get_amount_out_exact_in(
                token_in.address,
                token_out.address,
                token_in.balanceOf(wallet_address),
                0,
            )[0],
            max_out_ratio_limit,
        )
    )

    return result if result > 0 else 1
