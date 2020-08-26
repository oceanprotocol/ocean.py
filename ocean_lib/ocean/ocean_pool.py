import logging

from ocean_lib.models import balancer_constants
from ocean_lib.models.btoken import BToken
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.bpool import BPool
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger(__name__)


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

    def __init__(self, ocean_token_address: str, bfactory_address: str):
        self.ocean_address = ocean_token_address
        self.bfactory_address = bfactory_address

    def create(self,
               data_token_address: str,
               data_token_amount: float,
               OCEAN_amount: float,
               from_wallet: Wallet,
               data_token_weight: float=balancer_constants.INIT_WEIGHT_DT,
               swap_fee: float=balancer_constants.DEFAULT_SWAP_FEE
               ) -> BPool:
        """
        Create a new pool with bound datatoken and OCEAN token then finalize it.
        The pool will have publicSwap enabled and swap fee is set
        to `balancer_constants.DEFAULT_SWAP_FEE`.
        Balances of both data tokens and OCEAN tokens must be sufficient in the
        `from_wallet`, otherwise this will fail.

        :param data_token_address: str address of the DataToken contract
        :param data_token_amount: float amount of initial liquidity of data tokens
        :param OCEAN_amount: float amount of initial liquidity of OCEAN tokens
        :param from_wallet: Wallet instance of pool owner
        :param data_token_weight: float weight of the data token to be set in the new pool must be >= 1 & <= 9
        :param swap_fee: float the fee taken by the pool on each swap transaction
        :return: BPool instance
        """

        bfactory = BFactory(self.bfactory_address)
        pool_address = bfactory.newBPool(from_wallet)
        pool = BPool(pool_address)
        logger.debug(f'pool created with address {pool_address}.')

        assert 1 <= data_token_weight <= 9
        base_weight = 10.0 - data_token_weight

        # Must approve datatoken and Ocean tokens to the new pool as spender
        dt = DataToken(data_token_address)
        dt.approve_tokens(pool_address, data_token_amount, from_wallet)
        ot = DataToken(self.ocean_address)
        ot.approve_tokens(pool_address, OCEAN_amount, from_wallet)

        tx_id = pool.setup(
            data_token_address,
            to_base_18(data_token_amount),
            to_base_18(data_token_weight),
            self.ocean_address,
            to_base_18(OCEAN_amount),
            to_base_18(base_weight),
            to_base_18(swap_fee),
            from_wallet
        )
        logger.debug(f'create pool completed: poolAddress={pool_address}, pool setup TxId={tx_id}')

        return pool

    @staticmethod
    def get(pool_address: str) -> BPool:
        return BPool(pool_address)

    def get_token_address(self, pool_address: str) -> str:
        """Returns the address of this pool's datatoken."""
        assert self._is_valid_pool(pool_address)
        pool = BPool(pool_address)
        tokens = pool.getCurrentTokens()
        return tokens[0] if tokens[0] != self.ocean_address else tokens[1]

    def get_OCEAN_address(self) -> str:
        return self.ocean_address

    # ============================================================
    # to simplify balancer flows. These methods are here because
    # BPool doesn't know (and shouldn't know) OCEAN_address and _DT_address
    def add_data_token_liquidity(self, pool_address: str, amount_base: int, from_wallet: Wallet) -> str:
        """
        Add `amount_base` number of data tokens to the pool `pool_address`. In return the wallet owner
        will get a number of pool shares/tokens

        The pool has a datatoken and OCEAN token. This function can be used to add liquidity of only
        the datatoken. To add liquidity of the OCEAN token, use the `add_OCEAN_liquidity` function.

        :param pool_address: str address of pool contract
        :param amount_base: number of data tokens to add to this pool
        :param from_wallet: Wallet instance of the owner of data tokens
        :return: str transaction id/hash
        """
        return self._add_liquidity(
            pool_address, self.get_token_address(pool_address), amount_base, from_wallet
        )

    def add_OCEAN_liquidity(self, pool_address: str, amount_base: int, from_wallet: Wallet) -> str:
        """
        Add `amount_base` number of OCEAN tokens to the pool `pool_address`. In return the wallet owner
        will get a number of pool shares/tokens

        :param pool_address: str address of pool contract
        :param amount_base: number of data tokens to add to this pool
        :param from_wallet: Wallet instance of the owner of data tokens
        :return: str transaction id/hash
        """
        return self._add_liquidity(
            pool_address, self.ocean_address, amount_base, from_wallet
        )

    def _add_liquidity(self, pool_address: str, token_address: str,
                       amount_base: int, from_wallet: Wallet) -> str:
        assert amount_base >= 0
        if amount_base == 0:
            return ''

        pool = BPool(pool_address)
        token = BToken(token_address)
        assert token.balanceOf(from_wallet.address) >= amount_base, \
            f'Insufficient funds, {amount_base} tokens are required of token address {token_address}, ' \
            f'but only a balance of {token.balanceOf(from_wallet.address)} is available.'

        token.approve(pool_address, amount_base, from_wallet)

        pool_amount = pool.joinswapExternAmountIn(
            token_address,
            amount_base,
            0,
            from_wallet
        )
        return pool_amount

    def remove_data_token_liquidity(self, pool_address: str, amount_base: int,
                                    max_pool_shares_base: int, from_wallet: Wallet) -> str:
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
        dt_address = self.get_token_address(pool_address)
        return self._remove_liquidity(
            pool_address, dt_address, amount_base, max_pool_shares_base, from_wallet
        )

    def remove_OCEAN_liquidity(self, pool_address: str, amount_base: int,
                               max_pool_shares_base: int, from_wallet: Wallet) -> str:
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
            pool_address, self.ocean_address, amount_base, max_pool_shares_base, from_wallet
        )

    def _remove_liquidity(self, pool_address: str, token_address: str, amount_base: int,
                          max_pool_shares_base: int, from_wallet: Wallet) -> str:
        assert amount_base >= 0
        if amount_base == 0:
            return ''

        assert max_pool_shares_base > 0, f''

        pool = BPool(pool_address)
        if pool.balanceOf(from_wallet.address) == 0:
            return ''

        return pool.exitswapExternAmountOut(token_address, amount_base, max_pool_shares_base, from_wallet)

    def buy_data_tokens(self, pool_address: str, amount_base: int,
                        max_OCEAN_amount_base: int, from_wallet: Wallet) -> str:
        """
        Buy data tokens from this pool, paying `max_OCEAN_amount_base` of OCEAN tokens.
        If total spent <= max_OCEAN_amount_base.
        - Caller is spending OCEAN tokens, and receiving `amount_base` DataTokens
        - OCEAN tokens are going into pool, DataTokens are going out of pool

        The transaction fails if total spent exceeds `max_OCEAN_amount_base`.

        :param pool_address: str address of pool contract
        :param amount_base: int number of data tokens to add to this pool in *base*
        :param max_OCEAN_amount_base:
        :param from_wallet:
        :return: str transaction id/hash
        """
        ocean_tok = BToken(self.ocean_address)
        ocean_tok.approve(pool_address, max_OCEAN_amount_base, from_wallet)

        dtoken_address = self.get_token_address(pool_address)
        pool = BPool(pool_address)
        return pool.swapExactAmountOut(
            tokenIn_address=self.ocean_address,  # entering pool
            maxAmountIn_base=max_OCEAN_amount_base,  # ""
            tokenOut_address=dtoken_address,  # leaving pool
            tokenAmountOut_base=amount_base,  # ""
            maxPrice_base=2 ** 255,  # here we limit by max_num_OCEAN, not price
            from_wallet=from_wallet,
        )

    def sell_data_tokens(self, pool_address: str, amount_base: int,
                         min_OCEAN_amount_base: int, from_wallet: Wallet) -> str:
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
        dtoken_address = self.get_token_address(pool_address)
        dt = BToken(dtoken_address)
        dt.approve(pool_address, amount_base, from_wallet=from_wallet)

        pool = BPool(pool_address)
        return pool.swapExactAmountIn(
            tokenIn_address=dtoken_address,  # entering pool
            tokenAmountIn_base=amount_base,  # ""
            tokenOut_address=self.ocean_address,  # leaving pool
            minAmountOut_base=min_OCEAN_amount_base,  # ""
            maxPrice_base=2 ** 255,  # here we limit by max_num_OCEAN, not price
            from_wallet=from_wallet,
        )

    def get_token_price_base(self, pool_address: str) -> int:
        """

        :param pool_address: str the address of the pool contract
        :return: int price of data token in terms of OCEAN tokens
        """
        dtoken_address = self.get_token_address(pool_address)
        pool = BPool(pool_address)
        return pool.getSpotPrice(
            tokenIn_address=self.ocean_address,
            tokenOut_address=dtoken_address
        )

    def add_liquidity_finalized(
            self, pool_address: str, bpt_amount_base: int, max_data_token_amount_base: int,
            max_OCEAN_amount_base: int, from_wallet: Wallet) -> str:
        """
        Add liquidity to a pool that's been finalized.
        Buy bpt_amount_base tokens from the pool, spending DataTokens and OCEAN tokens
        as needed and up to the specified maximum amounts.

        :param pool_address: str address of pool contract
        :param bpt_amount_base: int number of pool shares to receive for adding the liquidity
        :param max_data_token_amount_base: int maximum amount of Data tokens to go into the pool
        :param max_OCEAN_amount_base: int maximum amount of OCEAN tokens to go into the pool
        :param from_wallet: Wallet instance
        :return: str transaction id/hash
        """
        assert self._is_valid_pool(pool_address)
        dt_address = self.get_token_address(pool_address)
        dt = BToken(dt_address)
        dt.approve(pool_address, max_data_token_amount_base, from_wallet=from_wallet)

        OCEAN = BToken(self.ocean_address)
        OCEAN.approve(pool_address, max_OCEAN_amount_base, from_wallet=from_wallet)

        pool = BPool(pool_address)
        return pool.joinPool(
            bpt_amount_base,
            [max_data_token_amount_base, max_OCEAN_amount_base],
            from_wallet=from_wallet
        )

    def _is_valid_pool(self, pool_address) -> bool:
        pool = BPool(pool_address)
        if pool.getNumTokens() != 2:
            return False

        # dt should be 0th token, OCEAN should be 1st token
        if pool.getCurrentTokens()[1] != self.ocean_address:
            return False
        return True
