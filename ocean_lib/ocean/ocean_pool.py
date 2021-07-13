#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging

from enforce_typing import enforce_types
from ocean_lib.exceptions import VerifyTxFailed
from ocean_lib.models import balancer_constants
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.bpool import BPool
from ocean_lib.models.btoken import BToken
from ocean_lib.models.data_token import DataToken
from ocean_lib.ocean.util import from_base_18, to_base_18
from ocean_lib.web3_internal.wallet import Wallet
from web3.main import Web3

logger = logging.getLogger(__name__)


def add_liquidity(web3, pool: BPool, liquidity_address, amount_base, from_wallet):
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


def get_token_address(web3, pool, ocean_address):
    tokens = pool.getCurrentTokens()
    return tokens[0] if tokens[0] != ocean_address else tokens[1]


@enforce_types
class OceanPool:

    """
    This pool is based on the Balancer protocol contracts with slight
    modifications (https://github.com/balancer-labs). This class wraps the main
    functionality needed to support publishing Data Tokens trading pools.

    A pool here always has OCEAN tokens on one end and some DataToken on the other end.
    This allows the DataToken owner or any DataToken holder to create a pool for trading
    the data token vs. OCEAN tokens. As a result all functions here assume the pool
    has only two tokens and one of the tokens is always the OCEAN token.

    Note that the OCEAN token address is supplied to the init method. The Ocean instance
    reads the OCEAN token address from the `address_file` config option (see Config.py).

    """

    def __init__(self, web3: Web3, ocean_token_address: str):
        """Initialises Ocean Pool."""
        self.web3 = web3
        self.ocean_address = ocean_token_address

    # ============================================================
    # to simplify balancer flows. These methods are here because
    # BPool doesn't know (and shouldn't know) OCEAN_address and _DT_address
    def remove_data_token_liquidity(
        self,
        pool_address: str,
        amount_base: int,
        max_pool_shares_base: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Remove `amount_base` number of data tokens from the pool `pool_address`. The wallet owner
        will get that amount of data tokens. At the same time a number of pool shares/tokens up to
        `max_pool_shares_base` will be taken from the caller's wallet and given back to the pool.

        :param pool_address: str address of pool contract
        :param amount_base: int number of data tokens to add to this pool in *base*
        :param max_pool_shares_base: int maximum number of pool shares as a cost for the withdrawn data tokens
        :param from_wallet: Wallet instance of the owner of data tokens
        :return: str transaction id/hash
        """
        bpool = BPool(self.web3, pool_address)
        tokens = bpool.getCurrentTokens()
        token_address = tokens[0] if tokens[0] != self.ocean_address else tokens[1]

        return self._remove_liquidity(
            pool_address, token_address, amount_base, max_pool_shares_base, from_wallet
        )

    def remove_OCEAN_liquidity(
        self,
        pool_address: str,
        amount_base: int,
        max_pool_shares_base: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Remove `amount_base` number of OCEAN tokens from the pool `pool_address`. The wallet owner
        will get that amount of OCEAN tokens. At the same time a number of pool shares/tokens up to
        `max_pool_shares_base` will be taken from the caller's wallet and given back to the pool.

        :param pool_address: str address of pool contract
        :param amount_base: int number of data tokens to add to this pool in *base*
        :param max_pool_shares_base: int maximum number of pool shares as a cost for the withdrawn data tokens
        :param from_wallet: Wallet instance of the owner of data tokens
        :return: str transaction id/hash
        """
        return self._remove_liquidity(
            pool_address,
            self.ocean_address,
            amount_base,
            max_pool_shares_base,
            from_wallet,
        )

    def _remove_liquidity(
        self,
        pool_address: str,
        token_address: str,
        amount_base: int,
        max_pool_shares_base: int,
        from_wallet: Wallet,
    ) -> str:
        assert amount_base >= 0
        if amount_base == 0:
            return ""

        assert max_pool_shares_base > 0, ""

        pool = BPool(self.web3, pool_address)
        if pool.balanceOf(from_wallet.address) == 0:
            return ""

        return pool.exitswapExternAmountOut(
            token_address, amount_base, max_pool_shares_base, from_wallet
        )

    def buy_data_tokens(
        self,
        pool_address: str,
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
        ocean_tok = DataToken(self.web3, self.ocean_address)
        ocean_tok.approve_tokens(pool_address, max_OCEAN_amount, from_wallet, wait=True)

        bpool = BPool(self.web3, pool_address)
        tokens = bpool.getCurrentTokens()
        dtoken_address = tokens[0] if tokens[0] != self.ocean_address else tokens[1]
        pool = BPool(self.web3, pool_address)
        return pool.swapExactAmountOut(
            tokenIn_address=self.ocean_address,  # entering pool
            maxAmountIn_base=to_base_18(max_OCEAN_amount),  # ""
            tokenOut_address=dtoken_address,  # leaving pool
            tokenAmountOut_base=to_base_18(amount),  # ""
            maxPrice_base=2 ** 255,  # here we limit by max_num_OCEAN, not price
            from_wallet=from_wallet,
        )

    def sell_data_tokens(
        self,
        pool_address: str,
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
        bpool = BPool(self.web3, pool_address)
        tokens = bpool.getCurrentTokens()
        dtoken_address = tokens[0] if tokens[0] != self.ocean_address else tokens[1]

        dt = BToken(self.web3, dtoken_address)
        dt.approve(pool_address, amount_base, from_wallet=from_wallet)

        pool = BPool(self.web3, pool_address)
        return pool.swapExactAmountIn(
            tokenIn_address=dtoken_address,  # entering pool
            tokenAmountIn_base=amount_base,  # ""
            tokenOut_address=self.ocean_address,  # leaving pool
            minAmountOut_base=min_OCEAN_amount_base,  # ""
            maxPrice_base=2 ** 255,  # here we limit by max_num_OCEAN, not price
            from_wallet=from_wallet,
        )
