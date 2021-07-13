#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging

from ocean_lib.models.bpool import BPool
from ocean_lib.models.btoken import BToken
from ocean_lib.models.data_token import DataToken
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.wallet import Wallet
from web3.main import Web3

logger = logging.getLogger(__name__)


def add_liquidity(
    web3: Web3,
    pool: BPool,
    liquidity_address: str,
    amount_base: int,
    from_wallet: Wallet,
):
    assert amount_base >= 0
    if amount_base == 0:
        return ""
    token = BToken(web3, liquidity_address)
    assert token.balanceOf(from_wallet.address) >= amount_base, (
        f"Insufficient funds, {amount_base} tokens are required of token address {liquidity_address}, "
        f"but only a balance of {token.balanceOf(from_wallet.address)} is available."
    )

    tx_id = token.approve(pool.address, amount_base, from_wallet)
    r = token.get_tx_receipt(web3, tx_id)
    if not r or r.status != 1:
        return 0

    pool_amount = pool.joinswapExternAmountIn(
        liquidity_address, amount_base, 0, from_wallet
    )
    return pool_amount


def remove_liquidity(
    web3: Web3,
    pool: BPool,
    liquidity_address: str,
    amount_base: int,
    max_pool_shares_base: int,
    from_wallet: Wallet,
) -> str:
    assert amount_base >= 0
    if amount_base == 0:
        return ""

    assert max_pool_shares_base > 0, ""

    if pool.balanceOf(from_wallet.address) == 0:
        return ""

    return pool.exitswapExternAmountOut(
        liquidity_address, amount_base, max_pool_shares_base, from_wallet
    )


def buy_data_tokens(
    web3: Web3,
    pool: BPool,
    dtoken_address: str,
    ocean_address: str,
    amount: float,
    max_OCEAN_amount: float,
    from_wallet: Wallet,
) -> str:
    """
    Buy data tokens from this pool, paying `max_OCEAN_amount_base` of OCEAN tokens.
    If total spent <= max_OCEAN_amount_base.
    - Caller is spending OCEAN tokens, and receiving `amount_base` DataTokens
    - OCEAN tokens are going into pool, DataTokens are going out of pool

    The transaction fails if total spent exceeds `max_OCEAN_amount_base`.

    :param pool_address: str address of pool contract
    :param amount: int number of data tokens to add to this pool in *base*
    :param max_OCEAN_amount:
    :param from_wallet:
    :return: str transaction id/hash
    """
    ocean_tok = DataToken(web3, ocean_address)
    ocean_tok.approve_tokens(pool.address, max_OCEAN_amount, from_wallet, wait=True)

    return pool.swapExactAmountOut(
        tokenIn_address=ocean_address,  # entering pool
        maxAmountIn_base=to_base_18(max_OCEAN_amount),  # ""
        tokenOut_address=dtoken_address,  # leaving pool
        tokenAmountOut_base=to_base_18(amount),  # ""
        maxPrice_base=2 ** 255,  # here we limit by max_num_OCEAN, not price
        from_wallet=from_wallet,
    )


def sell_data_tokens(
    web3: Web3,
    pool: BPool,
    dtoken_address: str,
    ocean_address: str,
    amount_base: int,
    min_OCEAN_amount_base: int,
    from_wallet: Wallet,
) -> str:
    """
    Sell data tokens into this pool, receive `min_OCEAN_amount_base` of OCEAN tokens.
    If total income >= min_OCEAN_amount_base
    - Caller is spending DataTokens, and receiving OCEAN tokens
    - DataTokens are going into pool, OCEAN tokens are going out of pool

    The transaction fails if total income does not reach `min_OCEAN_amount_base`

    :param pool_address: str address of pool contract
    :param amount_base: int number of data tokens to add to this pool in *base*
    :param min_OCEAN_amount_base:
    :param from_wallet:
    :return: str transaction id/hash
    """
    dt = BToken(web3, dtoken_address)
    dt.approve(pool.address, amount_base, from_wallet=from_wallet)

    return pool.swapExactAmountIn(
        tokenIn_address=dtoken_address,  # entering pool
        tokenAmountIn_base=amount_base,  # ""
        tokenOut_address=ocean_address,  # leaving pool
        minAmountOut_base=min_OCEAN_amount_base,  # ""
        maxPrice_base=2 ** 255,  # here we limit by max_num_OCEAN, not price
        from_wallet=from_wallet,
    )
