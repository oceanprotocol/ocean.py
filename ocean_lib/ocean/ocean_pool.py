from ocean_lib.models import balancer_constants
from ocean_lib.models.btoken import BToken
from ocean_lib.models.sfactory import SFactory
from ocean_lib.models.spool import SPool
from ocean_lib.ocean.util import get_sfactory_address
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3helper import Web3Helper


class OceanPool:
    def __init__(self, ocean_token_address: str):
        self.ocean_address = ocean_token_address

    def create_pool(self,
                    dt_address: str,
                    num_dt_base: int,
                    num_OCEAN_base: int,
                    from_wallet: Wallet) -> SPool:
        sfactory_address = get_sfactory_address(Web3Helper.get_network_name())

        sfactory = SFactory(sfactory_address)

        pool_address = sfactory.newSPool(from_wallet)
        pool = SPool(pool_address)
        pool.setPublicSwap(True, from_wallet=from_wallet)
        pool.setSwapFee(balancer_constants.DEFAULT_SWAP_FEE, from_wallet)

        dt = BToken(dt_address)
        assert dt.balanceOf(from_wallet.address) >= num_dt_base, \
            "insufficient DT"
        dt.approve(pool_address, num_dt_base, from_wallet=from_wallet)
        pool.bind(dt_address, num_dt_base, balancer_constants.INIT_WEIGHT_DT,
                  from_wallet)

        OCEAN = BToken(self.ocean_address)
        assert OCEAN.balanceOf(from_wallet.address) >= num_OCEAN_base, \
            "insufficient OCEAN"
        OCEAN.approve(pool_address, num_OCEAN_base, from_wallet)
        pool.bind(self.ocean_address, num_OCEAN_base,
                  balancer_constants.INIT_WEIGHT_OCEAN, from_wallet)

        return pool

    def get_pool(self, pool_address: str) -> SPool:
        return SPool(pool_address)

    # ============================================================
    # to simplify balancer flows. These methods are here because
    # SPool doesn't know (and shouldn't know) OCEAN_address and _DT_address
    def addLiquidity(self, pool_address: str,
                     num_dt_base: int, num_OCEAN_base: int,
                     from_wallet: Wallet):
        dt_address = self._dt_address(pool_address)
        self._addLiquidity(pool_address, dt_address, num_dt_base,
                           balancer_constants.INIT_WEIGHT_DT, from_wallet)
        self._addLiquidity(pool_address, self.ocean_address, num_OCEAN_base,
                           balancer_constants.INIT_WEIGHT_OCEAN, from_wallet)

    def _addLiquidity(self, pool_address: str, token_address: str,
                      num_add_base: int, weight_base: int, from_wallet: Wallet):
        assert num_add_base >= 0
        if num_add_base == 0: return

        token = BToken(token_address)
        assert token.balanceOf(from_wallet.address) >= num_add_base, \
            "insufficient funds"

        token.approve(pool_address, num_add_base, from_wallet)

        pool = SPool(pool_address)
        num_before_base = token.balanceOf(pool_address)
        num_after_base = num_before_base + num_add_base
        pool.rebind(token_address, num_after_base, weight_base, from_wallet)

    def remove_liquidity(self, pool_address: str,
                         num_dt_base: int, num_OCEAN_base: int,
                         from_wallet: Wallet):
        dt_address = self._dt_address(pool_address)
        self._remove_liquidity(pool_address, dt_address, num_dt_base,
                               balancer_constants.INIT_WEIGHT_DT, from_wallet)
        self._remove_liquidity(pool_address, self.ocean_address, num_OCEAN_base,
                               balancer_constants.INIT_WEIGHT_OCEAN, from_wallet)

    def _remove_liquidity(self, pool_address: str,
                          token_address: str, num_remove_base: int,
                          weight_base: int, from_wallet: Wallet):
        assert num_remove_base >= 0
        if num_remove_base == 0: return

        token = BToken(token_address)
        num_before_base = token.balanceOf(pool_address)
        num_after_base = num_before_base - num_remove_base
        assert num_after_base >= 0, "tried to remove too much"

        pool = SPool(pool_address)
        pool.rebind(token_address, num_after_base, weight_base, from_wallet)

    def buy_data_tokens(self, pool_address: str,
                        num_dt_base: int, max_num_OCEAN_base: int,
                        from_wallet: Wallet):
        """
        Buy data tokens from this pool, if total spent <= max_num_OCEAN.
        -Caller is spending OCEAN, and receiving DT
        -OCEAN's going into pool, DT's going out of pool
        """
        OCEAN = BToken(self.ocean_address)
        OCEAN.approve(pool_address, max_num_OCEAN_base, from_wallet)

        dt_address = self._dt_address(pool_address)
        pool = SPool(pool_address)
        pool.swapExactAmountOut(
            tokenIn_address=self.ocean_address,  # entering pool
            maxAmountIn_base=max_num_OCEAN_base,  # ""
            tokenOut_address=dt_address,  # leaving pool
            tokenAmountOut_base=num_dt_base,  # ""
            maxPrice_base=2 ** 255,  # here we limit by max_num_OCEAN, not price
            from_wallet=from_wallet,
        )

    def sell_data_tokens(self, pool_address: str,
                         num_dt_base: int, min_num_OCEAN_base: int,
                         from_wallet: Wallet):
        """
        Sell data tokens into this pool, if total income >= min_num_OCEAN
        -Caller is spending DT, and receiving OCEAN
        -DT's going into pool, OCEAN's going out of pool
        """
        dt_address = self._dt_address(pool_address)
        dt = BToken(dt_address)
        dt.approve(pool_address, num_dt_base, from_wallet=from_wallet)

        pool = SPool(pool_address)
        pool.swapExactAmountIn(
            tokenIn_address=dt_address,  # entering pool
            tokenAmountIn_base=num_dt_base,  # ""
            tokenOut_address=self.ocean_address,  # leaving pool
            minAmountOut_base=min_num_OCEAN_base,  # ""
            maxPrice_base=2 ** 255,  # here we limit by max_num_OCEAN, not price
            from_wallet=from_wallet,
        )

    def get_dt_price_base(self, pool_address: str) -> int:
        dt_address = self._dt_address(pool_address)
        pool = SPool(pool_address)
        return pool.getSpotPrice(
            tokenIn_address=self.ocean_address,
            tokenOut_address=dt_address)

    def add_liquidity_finalized(
            self, pool_address: str, num_bpt_base: int, max_num_dt_base: int,
            max_num_OCEAN_base: int, from_wallet: Wallet):
        """Add liquidity to a pool that's been finalized.
        Buy num_BPT tokens from the pool, spending DT and OCEAN as needed"""
        assert self._is_valid_dt_OCEAN_pool(pool_address)
        dt_address = self._dt_address(pool_address)
        dt = BToken(dt_address)
        dt.approve(pool_address, max_num_dt_base, from_wallet=from_wallet)

        OCEAN = BToken(self.ocean_address)
        OCEAN.approve(pool_address, max_num_OCEAN_base, from_wallet=from_wallet)

        pool = SPool(pool_address)
        pool.joinPool(num_bpt_base, [max_num_dt_base, max_num_OCEAN_base],
                      from_wallet=from_wallet)

    def _dt_address(self, pool_address: str) -> str:
        """Returns the address of this pool's datatoken."""
        assert self._is_valid_dt_OCEAN_pool(pool_address)
        pool = SPool(pool_address)
        return pool.getCurrentTokens()[0]

    def _is_valid_dt_OCEAN_pool(self, pool_address) -> bool:
        pool = SPool(pool_address)
        if pool.getNumTokens() != 2:
            return False

        # dt should be 0th token, OCEAN should be 1st token
        if pool.getCurrentTokens()[1] != self.ocean_address:
            return False
        return True
