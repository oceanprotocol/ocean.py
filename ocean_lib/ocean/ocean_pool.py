#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from decimal import Decimal

from enforce_typing import enforce_types
from ocean_lib.exceptions import InsufficientBalance, VerifyTxFailed
from ocean_lib.models import balancer_constants
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.bpool import BPool
from ocean_lib.models.btoken import BToken
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.web3_internal.currency import from_wei, to_wei
from ocean_lib.web3_internal.wallet import Wallet
from scipy.interpolate import interp1d
from web3.main import Web3

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

    POOL_INFO_FLAGS = {
        "datatokenInfo",
        "price",
        "reserve",
        "shares",
        "shareHolders",
        "liquidity",
        "creator",
        "dtHolders",
    }

    @enforce_types
    def __init__(
        self,
        web3: Web3,
        ocean_token_address: str,
        bfactory_address: str,
        dtfactory_address: str,
    ) -> None:
        """Initialises Ocean Pool."""
        self.web3 = web3
        self.ocean_address = ocean_token_address
        self.bfactory_address = bfactory_address
        self.dtfactory_address = dtfactory_address

    @enforce_types
    def create(
        self,
        data_token_address: str,
        data_token_amount: int,
        OCEAN_amount: int,
        from_wallet: Wallet,
        data_token_weight: int = balancer_constants.INIT_WEIGHT_DT,
        swap_fee: int = balancer_constants.DEFAULT_SWAP_FEE,
    ) -> BPool:
        """
        Create a new pool with bound datatoken and OCEAN token then finalize it.
        The pool will have publicSwap enabled and swap fee is set
        to `balancer_constants.DEFAULT_SWAP_FEE`.
        Balances of both data tokens and OCEAN tokens must be sufficient in the
        `from_wallet`, otherwise this will fail.

        :param data_token_address: str address of the DataToken contract
        :param data_token_amount: int amount of initial liquidity of data tokens
        :param OCEAN_amount: int amount of initial liquidity of OCEAN tokens
        :param from_wallet: Wallet instance of pool owner
        :param data_token_weight: int weight of the data token to be set in the new pool must be >= 1 & <= 9
        :param swap_fee: int the fee taken by the pool on each swap transaction
        :return: BPool instance
        """
        bfactory = BFactory(self.web3, self.bfactory_address)
        pool_address = bfactory.newBPool(from_wallet)
        pool = BPool(self.web3, pool_address)
        logger.debug(f"pool created with address {pool_address}.")

        assert to_wei("1") <= data_token_weight <= to_wei("9")
        base_weight = to_wei(10) - data_token_weight

        # Must approve datatoken and Ocean tokens to the new pool as spender
        dt = DataToken(self.web3, data_token_address)
        if dt.balanceOf(from_wallet.address) < data_token_amount:
            raise InsufficientBalance(
                "Insufficient datatoken balance for pool creation!"
            )
        if dt.allowance(from_wallet.address, pool_address) < data_token_amount:
            tx_id = dt.approve(pool_address, data_token_amount, from_wallet)
            if dt.get_tx_receipt(self.web3, tx_id).status != 1:
                raise VerifyTxFailed(
                    f"Approve datatokens failed, pool was created at {pool_address}"
                )

        ot = DataToken(self.web3, self.ocean_address)
        if ot.balanceOf(from_wallet.address) < OCEAN_amount:
            raise InsufficientBalance("Insufficient OCEAN balance for pool creation!")
        if ot.allowance(from_wallet.address, pool_address) < OCEAN_amount:
            tx_id = ot.approve(pool_address, OCEAN_amount, from_wallet)
            if ot.get_tx_receipt(self.web3, tx_id).status != 1:
                raise VerifyTxFailed(
                    f"Approve OCEAN tokens failed, pool was created at {pool_address}"
                )
        tx_id = pool.setup(
            data_token_address,
            data_token_amount,
            data_token_weight,
            self.ocean_address,
            OCEAN_amount,
            base_weight,
            swap_fee,
            from_wallet,
        )
        if pool.get_tx_receipt(self.web3, tx_id).status != 1:
            raise VerifyTxFailed(
                f"pool.setup failed: txId={tx_id}, receipt={pool.get_tx_receipt(self.web3, tx_id)}"
            )

        logger.debug(
            f"create pool completed: poolAddress={pool_address}, pool setup TxId={tx_id}"
        )

        return pool

    @staticmethod
    @enforce_types
    def get(web3: Web3, pool_address: str) -> BPool:
        return BPool(web3, pool_address)

    @enforce_types
    def get_token_address(
        self, pool_address: str, pool: BPool = None, validate: bool = True
    ) -> str:
        """Returns the address of this pool's datatoken."""
        if not pool:
            if validate:
                assert self._is_valid_pool(pool_address)

            pool = BPool(self.web3, pool_address)

        tokens = pool.getCurrentTokens()
        return tokens[0] if tokens[0] != self.ocean_address else tokens[1]

    @enforce_types
    def get_OCEAN_address(self) -> str:
        return self.ocean_address

    # ============================================================
    # to simplify balancer flows. These methods are here because
    # BPool doesn't know (and shouldn't know) OCEAN_address and _DT_address
    @enforce_types
    def add_data_token_liquidity(
        self, pool_address: str, amount: int, from_wallet: Wallet
    ) -> str:
        """
        Add `amount` number of data tokens to the pool `pool_address`. In return the wallet owner
        will get a number of pool shares/tokens

        The pool has a datatoken and OCEAN token. This function can be used to add liquidity of only
        the datatoken. To add liquidity of the OCEAN token, use the `add_OCEAN_liquidity` function.

        :param pool_address: str address of pool contract
        :param amount: number of data tokens to add to this pool
        :param from_wallet: Wallet instance of the owner of data tokens
        :return: str transaction id/hash
        """
        return self._add_liquidity(
            pool_address, self.get_token_address(pool_address), amount, from_wallet
        )

    @enforce_types
    def add_OCEAN_liquidity(
        self, pool_address: str, amount: int, from_wallet: Wallet
    ) -> str:
        """
        Add `amount` number of OCEAN tokens to the pool `pool_address`. In return the wallet owner
        will get a number of pool shares/tokens

        :param pool_address: str address of pool contract
        :param amount: number of data tokens to add to this pool
        :param from_wallet: Wallet instance of the owner of data tokens
        :return: str transaction id/hash
        """
        return self._add_liquidity(
            pool_address, self.ocean_address, amount, from_wallet
        )

    @enforce_types
    def _add_liquidity(
        self, pool_address: str, token_address: str, amount: int, from_wallet: Wallet
    ) -> str:
        assert amount >= 0
        if amount == 0:
            return ""
        pool = BPool(self.web3, pool_address)
        token = BToken(self.web3, token_address)
        assert token.balanceOf(from_wallet.address) >= amount, (
            f"Insufficient funds, {amount} tokens are required of token address {token_address}, "
            f"but only a balance of {token.balanceOf(from_wallet.address)} is available."
        )
        if token.allowance(from_wallet.address, pool_address) < amount:
            tx_id = token.approve(pool_address, amount, from_wallet)
            r = token.get_tx_receipt(self.web3, tx_id)
            if not r or r.status != 1:
                raise VerifyTxFailed(
                    f"Approve OCEAN tokens failed, pool was created at {pool_address}"
                )

        pool_amount = pool.joinswapExternAmountIn(token_address, amount, 0, from_wallet)
        return pool_amount

    @enforce_types
    def remove_data_token_liquidity(
        self, pool_address: str, amount: int, max_pool_shares: int, from_wallet: Wallet
    ) -> str:
        """
        Remove `amount` number of data tokens from the pool `pool_address`. The wallet owner
        will get that amount of data tokens. At the same time a number of pool shares/tokens up to
        `max_pool_shares` will be taken from the caller's wallet and given back to the pool.

        :param pool_address: str address of pool contract
        :param amount: int number of data tokens to add to this pool in *base*
        :param max_pool_shares: int maximum number of pool shares as a cost for the withdrawn data tokens
        :param from_wallet: Wallet instance of the owner of data tokens
        :return: str transaction id/hash
        """
        dt_address = self.get_token_address(pool_address)
        return self._remove_liquidity(
            pool_address, dt_address, amount, max_pool_shares, from_wallet
        )

    @enforce_types
    def remove_OCEAN_liquidity(
        self, pool_address: str, amount: int, max_pool_shares: int, from_wallet: Wallet
    ) -> str:
        """
        Remove `amount` number of OCEAN tokens from the pool `pool_address`. The wallet owner
        will get that amount of OCEAN tokens. At the same time a number of pool shares/tokens up to
        `max_pool_shares` will be taken from the caller's wallet and given back to the pool.

        :param pool_address: str address of pool contract
        :param amount: int number of data tokens to add to this pool in *base*
        :param max_pool_shares: int maximum number of pool shares as a cost for the withdrawn data tokens
        :param from_wallet: Wallet instance of the owner of data tokens
        :return: str transaction id/hash
        """
        return self._remove_liquidity(
            pool_address, self.ocean_address, amount, max_pool_shares, from_wallet
        )

    @enforce_types
    def _remove_liquidity(
        self,
        pool_address: str,
        token_address: str,
        amount: int,
        max_pool_shares: int,
        from_wallet: Wallet,
    ) -> str:
        assert amount >= 0
        if amount == 0:
            return ""

        assert max_pool_shares > 0, ""

        pool = BPool(self.web3, pool_address)
        if pool.balanceOf(from_wallet.address) == 0:
            raise InsufficientBalance(
                "The current balance is already 0. Remove liquidity failed!"
            )

        return pool.exitswapExternAmountOut(
            token_address, amount, max_pool_shares, from_wallet
        )

    @enforce_types
    def buy_data_tokens(
        self, pool_address: str, amount: int, max_OCEAN_amount: int, from_wallet: Wallet
    ) -> str:
        """
        Buy data tokens from this pool, paying `max_OCEAN_amount` of OCEAN tokens.
        If total spent <= max_OCEAN_amount.
        - Caller is spending OCEAN tokens, and receiving `amount` DataTokens
        - OCEAN tokens are going into pool, DataTokens are going out of pool

        The transaction fails if total spent exceeds `max_OCEAN_amount`.

        :param pool_address: str address of pool contract
        :param amount: int number of data tokens to add to this pool in *base*
        :param max_OCEAN_amount:
        :param from_wallet:
        :return: str transaction id/hash
        """
        ocean_tok = DataToken(self.web3, self.ocean_address)
        if ocean_tok.balanceOf(from_wallet.address) < max_OCEAN_amount:
            raise InsufficientBalance("Insufficient funds for buying DataTokens!")
        if ocean_tok.allowance(from_wallet.address, pool_address) < max_OCEAN_amount:
            ocean_tok.approve(pool_address, max_OCEAN_amount, from_wallet)

        dtoken_address = self.get_token_address(pool_address)
        pool = BPool(self.web3, pool_address)
        return pool.swapExactAmountOut(
            tokenIn_address=self.ocean_address,  # entering pool
            maxAmountIn=max_OCEAN_amount,  # ""
            tokenOut_address=dtoken_address,  # leaving pool
            tokenAmountOut=amount,  # ""
            maxPrice=2 ** 255,  # here we limit by max_num_OCEAN, not price
            from_wallet=from_wallet,
        )

    @enforce_types
    def sell_data_tokens(
        self, pool_address: str, amount: int, min_OCEAN_amount: int, from_wallet: Wallet
    ) -> str:
        """
        Sell data tokens into this pool, receive `min_OCEAN_amount` of OCEAN tokens.
        If total income >= min_OCEAN_amount
        - Caller is spending DataTokens, and receiving OCEAN tokens
        - DataTokens are going into pool, OCEAN tokens are going out of pool

        The transaction fails if total income does not reach `min_OCEAN_amount`

        :param pool_address: str address of pool contract
        :param amount: int number of data tokens to add to this pool
        :param min_OCEAN_amount:
        :param from_wallet:
        :return: str transaction id/hash
        """
        dtoken_address = self.get_token_address(pool_address)
        dt = BToken(self.web3, dtoken_address)
        if dt.balanceOf(from_wallet.address) < amount:
            raise InsufficientBalance("Insufficient funds for selling DataTokens!")
        if dt.allowance(from_wallet.address, pool_address) < amount:
            dt.approve(pool_address, amount, from_wallet=from_wallet)

        pool = BPool(self.web3, pool_address)
        return pool.swapExactAmountIn(
            tokenIn_address=dtoken_address,  # entering pool
            tokenAmountIn=amount,  # ""
            tokenOut_address=self.ocean_address,  # leaving pool
            minAmountOut=min_OCEAN_amount,  # ""
            maxPrice=2 ** 255,  # here we limit by max_num_OCEAN, not price
            from_wallet=from_wallet,
        )

    @enforce_types
    def get_token_price(self, pool_address: str) -> int:
        """

        :param pool_address: str the address of the pool contract
        :return: int price of data token in terms of OCEAN tokens
        """
        dtoken_address = self.get_token_address(pool_address)
        pool = BPool(self.web3, pool_address)
        return pool.getSpotPrice(
            tokenIn_address=self.ocean_address, tokenOut_address=dtoken_address
        )

    @enforce_types
    def add_liquidity_finalized(
        self,
        pool_address: str,
        bpt_amount: int,
        max_data_token_amount: int,
        max_OCEAN_amount: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Add liquidity to a pool that's been finalized.
        Buy bpt_amount tokens from the pool, spending DataTokens and OCEAN tokens
        as needed and up to the specified maximum amounts.

        :param pool_address: str address of pool contract
        :param bpt_amount: int number of pool shares to receive for adding the liquidity
        :param max_data_token_amount: int maximum amount of Data tokens to go into the pool
        :param max_OCEAN_amount: int maximum amount of OCEAN tokens to go into the pool
        :param from_wallet: Wallet instance
        :return: str transaction id/hash
        """
        assert self._is_valid_pool(pool_address), "The pool address is not valid."
        dt_address = self.get_token_address(pool_address)
        dt = BToken(self.web3, dt_address)
        if dt.balanceOf(from_wallet.address) < max_data_token_amount:
            raise InsufficientBalance(
                f"Insufficient funds for adding liquidity for {dt.address} datatoken!"
            )
        if dt.allowance(from_wallet.address, pool_address) < max_data_token_amount:
            dt.approve(pool_address, max_data_token_amount, from_wallet=from_wallet)

        OCEAN = BToken(self.web3, self.ocean_address)
        if OCEAN.balanceOf(from_wallet.address) < max_OCEAN_amount:
            raise InsufficientBalance(
                f"Insufficient funds for adding liquidity for {OCEAN.address} OCEAN token!"
            )
        if OCEAN.allowance(from_wallet.address, pool_address) < max_OCEAN_amount:
            OCEAN.approve(pool_address, max_OCEAN_amount, from_wallet=from_wallet)

        pool = BPool(self.web3, pool_address)
        return pool.joinPool(
            bpt_amount,
            [max_data_token_amount, max_OCEAN_amount],
            from_wallet=from_wallet,
        )

    @enforce_types
    def _is_valid_pool(self, pool_address: str) -> bool:
        pool = BPool(self.web3, pool_address)
        if pool.getNumTokens() != 2:
            return False

        # dt should be 0th token, OCEAN should be 1st token
        if pool.getCurrentTokens()[1] != self.ocean_address:
            return False
        return True

    ###########################################################################
    # convenient functions

    @enforce_types
    def getReserve(self, pool_address: str, token_address: str) -> int:
        return BPool(self.web3, pool_address).getBalance(token_address)

    @enforce_types
    def getMaxBuyQuantity(self, pool_address, token_address):
        return int(self.getReserve(pool_address, token_address) / 3)

    @enforce_types
    def getOceanMaxBuyQuantity(self, pool_address):
        return self.getMaxBuyQuantity(pool_address, self.ocean_address)

    @enforce_types
    def getDTMaxBuyQuantity(self, pool_address):
        return self.getMaxBuyQuantity(
            pool_address, self.get_token_address(pool_address)
        )

    @enforce_types
    def calcInGivenOut(
        self,
        pool_address: str,
        token_in_address: str,
        token_out_address: str,
        token_out_amount: int,
    ) -> int:
        pool = BPool(self.web3, pool_address)
        return pool.calcInGivenOut(
            pool.getBalance(token_in_address),
            pool.getDenormalizedWeight(token_in_address),
            pool.getBalance(token_out_address),
            pool.getDenormalizedWeight(token_out_address),
            token_out_amount,
            pool.getSwapFee(),
        )

    @enforce_types
    def calcOutGivenIn(
        self,
        pool_address: str,
        token_in_address: str,
        token_out_address: str,
        token_in_amount: int,
    ) -> int:
        pool = BPool(self.web3, pool_address)
        return pool.calcOutGivenIn(
            pool.getBalance(token_in_address),
            pool.getDenormalizedWeight(token_in_address),
            pool.getBalance(token_out_address),
            pool.getDenormalizedWeight(token_out_address),
            token_in_amount,
            pool.getSwapFee(),
        )

    @enforce_types
    def calcPoolOutGivenSingleIn(
        self, pool_address: str, token_in_address: str, token_in_amount: int
    ) -> int:
        pool = BPool(self.web3, pool_address)
        return pool.calcPoolOutGivenSingleIn(
            pool.getBalance(token_in_address),
            pool.getDenormalizedWeight(token_in_address),
            pool.totalSupply(),
            pool.getTotalDenormalizedWeight(),
            token_in_amount,
            pool.getSwapFee(),
        )

    @enforce_types
    def calcSingleInGivenPoolOut(
        self, pool_address: str, token_in_address: str, pool_shares: int
    ) -> int:
        pool = BPool(self.web3, pool_address)
        return pool.calcSingleInGivenPoolOut(
            pool.getBalance(token_in_address),
            pool.getDenormalizedWeight(token_in_address),
            pool.totalSupply(),
            pool.getTotalDenormalizedWeight(),
            pool_shares,
            pool.getSwapFee(),
        )

    @enforce_types
    def calcSingleOutGivenPoolIn(
        self, pool_address: str, token_out_address: str, pool_shares: int
    ) -> int:
        pool = BPool(self.web3, pool_address)
        return pool.calcSingleInGivenPoolOut(
            pool.getBalance(token_out_address),
            pool.getDenormalizedWeight(token_out_address),
            pool.totalSupply(),
            pool.getTotalDenormalizedWeight(),
            pool_shares,
            pool.getSwapFee(),
        )

    @enforce_types
    def calcPoolInGivenSingleOut(
        self, pool_address: str, token_out_address: str, token_out_amount: int
    ):
        pool = BPool(self.web3, pool_address)
        return pool.calcPoolInGivenSingleOut(
            pool.getBalance(token_out_address),
            pool.getDenormalizedWeight(token_out_address),
            pool.totalSupply(),
            pool.getTotalDenormalizedWeight(),
            token_out_amount,
            pool.getSwapFee(),
        )

    @enforce_types
    def getPoolSharesRequiredToRemoveDT(self, pool_address: str, dt_amount: int):
        dt = self.get_token_address(pool_address)
        return self.calcPoolInGivenSingleOut(pool_address, dt, dt_amount)

    # def getPoolSharesForRemoveDT(self, pool_address: str, pool_shares: int):
    #     dt = self.get_token_address(pool_address)
    #     return self.calcSingleOutGivenPoolIn(pool_address, dt, pool_shares)

    @enforce_types
    def getPoolSharesRequiredToRemoveOcean(self, pool_address: str, ocean_amount: int):
        return self.calcPoolInGivenSingleOut(
            pool_address, self.ocean_address, ocean_amount
        )

    # def getPoolSharesForRemoveOcean(self, pool_address: str, pool_shares: int):
    #     return self.calcSingleOutGivenPoolIn(pool_address, )

    @enforce_types
    def getDTMaxAddLiquidity(self, pool_address: str):
        return self.getMaxAddLiquidity(
            pool_address, self.get_token_address(pool_address)
        )

    @enforce_types
    def getOceanMaxAddLiquidity(self, pool_address: str):
        return self.getMaxAddLiquidity(pool_address, self.ocean_address)

    @enforce_types
    def getMaxAddLiquidity(self, pool_address, token_address):
        return int(self.getReserve(pool_address, token_address) / 2)

    @enforce_types
    def getMaxRemoveLiquidity(self, pool_address: str, token_address: str):
        return int(self.getReserve(pool_address, token_address) / 3)

    @enforce_types
    def getDTMaxRemoveLiquidity(self, pool_address):
        return self.getMaxRemoveLiquidity(
            pool_address, self.get_token_address(pool_address)
        )

    @enforce_types
    def getOceanMaxRemoveLiquidity(self, pool_address):
        return self.getMaxRemoveLiquidity(pool_address, self.ocean_address)

    @enforce_types
    def getDTRequiredToBuyOcean(self, pool_address: str, ocean_amount: int):
        pool = BPool(self.web3, pool_address)
        _in = self.get_token_address(pool_address, pool=pool)
        _out = self.ocean_address
        return self.getTokenPrice(pool, _in, _out, ocean_amount)

    @enforce_types
    def getOceanRequiredToBuyDT(self, pool_address: str, dt_amount: int):
        pool = BPool(self.web3, pool_address)
        _out = self.get_token_address(pool_address, pool=pool)
        _in = self.ocean_address
        return self.getTokenPrice(pool, _in, _out, dt_amount)

    @enforce_types
    def getTokenPrice(self, pool, token_in, token_out, amount_out) -> int:
        return pool.calcInGivenOut(
            pool.getBalance(token_in),
            pool.getDenormalizedWeight(token_in),
            pool.getBalance(token_out),
            pool.getDenormalizedWeight(token_out),
            amount_out,
            pool.getSwapFee(),
        )

    @enforce_types
    def get_all_pools(self, from_block=0, chunk_size=1000, include_balance=False):
        current_block = self.web3.eth.block_number

        bfactory = BFactory(self.web3, self.bfactory_address)
        logs = bfactory.get_event_logs(
            "BPoolRegistered", from_block, current_block, {}, chunk_size=chunk_size
        )
        if include_balance:
            pools = sorted(
                [
                    (
                        lg.args.bpoolAddress,
                        BPool(self.web3, lg.args.bpoolAddress).getBalance(
                            self.ocean_address
                        ),
                    )
                    for lg in logs
                ],
                key=lambda x: x[1],
                reverse=True,
            )
        else:
            pools = {lg.args.bpoolAddress for lg in logs}

        return pools

    @enforce_types
    def get_account_to_liquidity_records_map(self, records):
        lps = {r[0] for r in records}
        a_to_token_amount = {a: [] for a in lps}
        for r in records:
            a_to_token_amount[r[0]].append(r)
        return a_to_token_amount

    @enforce_types
    def _get_all_liquidity_records(
        self,
        action,
        pool_address,
        block_number=None,
        to_block=None,
        token_address=None,
        raw_result=True,
    ):
        current_block = to_block if to_block is not None else self.web3.eth.block_number
        pool = BPool(self.web3, pool_address)
        dt_address = token_address or self.get_token_address(pool_address, pool)
        factory = DTFactory(self.web3, self.dtfactory_address)
        if block_number is None:
            block_number = factory.get_token_registered_event(
                0, current_block, token_address=dt_address
            ).blockNumber

        log_args = (block_number, current_block)
        if action == "join":
            logs = pool.get_join_logs(*log_args)
        elif action == "exit":
            logs = pool.get_exit_logs(*log_args)
        elif action == "swap":
            logs = pool.get_swap_logs(*log_args)
        else:
            raise ValueError(
                f"Invalid action: {action}. Expected 'join', 'exit', or 'swap'."
            )

        if raw_result:
            return logs

        _all = []
        for lg in logs:
            if action == "join":
                record = (
                    lg.args.caller,
                    lg.args.tokenIn,
                    lg.args.tokenAmountIn,
                    0,
                    0,
                    lg.blockNumber,
                    lg.transactionHash,
                    "join",
                )
            elif action == "exit":
                record = (
                    lg.args.caller,
                    lg.args.tokenOut,
                    lg.args.tokenAmountOut,
                    0,
                    0,
                    lg.blockNumber,
                    lg.transactionHash,
                    "exit",
                )
            else:
                assert action == "swap", f"Unknown pool action {action}"
                record = (
                    lg.args.caller,
                    lg.args.tokenIn,
                    lg.args.tokenAmountIn,
                    lg.args.tokenOut,
                    lg.args.tokenAmountOut,
                    lg.blockNumber,
                    lg.transactionHash,
                    "swap",
                )

            _all.append(record)
        return _all

    @enforce_types
    def get_all_liquidity_additions(
        self,
        pool_address,
        block_number=None,
        to_block=None,
        token_address=None,
        raw_result=True,
    ):
        return self._get_all_liquidity_records(
            "join", pool_address, block_number, to_block, token_address, raw_result
        )

    @enforce_types
    def get_all_liquidity_removals(
        self,
        pool_address,
        block_number=None,
        to_block=None,
        token_address=None,
        raw_result=True,
    ):
        return self._get_all_liquidity_records(
            "exit", pool_address, block_number, to_block, token_address, raw_result
        )

    @enforce_types
    def get_all_swaps(
        self,
        pool_address,
        block_number=None,
        to_block=None,
        token_address=None,
        raw_result=True,
    ):
        return self._get_all_liquidity_records(
            "swap", pool_address, block_number, to_block, token_address, raw_result
        )

    @enforce_types
    def get_short_pool_info(
        self, pool_address, dt_address=None, from_block=None, to_block=None
    ):
        return self.get_pool_info(
            pool_address,
            dt_address,
            from_block,
            to_block,
            ["price", "reserve", "liquidityTotals"],
        )

    @enforce_types
    def get_pool_info(
        self, pool_address, dt_address=None, from_block=None, to_block=None, flags=None
    ):
        if not flags:
            flags = self.POOL_INFO_FLAGS

        current_block = (
            to_block if to_block is not None else self.web3.eth.block_number
        )  # RPC_CALL
        pool = BPool(self.web3, pool_address)
        dt_address = (
            dt_address
            if dt_address
            else self.get_token_address(pool_address, pool, validate=False)
        )  # RPC_CALL
        from_block = (
            from_block
            if from_block is not None
            else self.get_creation_block(pool_address)
        )  # RPC_CALL

        pool_creator = None
        shares = None
        info_dict = {"address": pool.address, "dataTokenAddress": dt_address}
        if "datatokenInfo" in flags:
            dt = DataToken(self.web3, dt_address)
            minter = dt.minter()

            token_holders = []
            if "dtHolders" in flags:
                token_holders = dt.calculate_token_holders(
                    from_block, to_block, to_wei("0.000001")
                )

            order_logs = dt.get_start_order_logs(
                from_block=from_block, to_block=to_block
            )

            info_dict["dataToken"] = {
                "address": dt.address(),
                "name": dt.datatoken_name(),
                "symbol": dt.symbol(),
                "deciamls": dt.decimals(),
                "cap": dt.cap(),
                "totalSupply": dt.totalSupply(),
                "minter": minter,
                "minterBalance": dt.balanceOf(minter),
                "numHolders": len(token_holders),
                "holders": token_holders,
                "numOrders": len(order_logs),
            }

        if "price" in flags:
            info_dict.update(
                {
                    "spotPrice1DT": pool.getSpotPrice(self.ocean_address, dt_address),
                    "totalPrice1DT": self.getOceanRequiredToBuyDT(
                        pool_address, dt_amount=to_wei(1)
                    ),
                }
            )

        if "reserve" in flags:
            ocn_reserve = pool.getBalance(self.ocean_address)
            dt_reserve = pool.getBalance(dt_address)
            info_dict.update(
                {
                    "oceanWeight": pool.getDenormalizedWeight(self.ocean_address),
                    "oceanReserve": ocn_reserve,
                    "dtWeight": pool.getDenormalizedWeight(dt_address),
                    "dtReserve": dt_reserve,
                }
            )
        if "shares" in flags or "creator" in flags:
            pool_creator = pool.getController()
            shares = pool.totalSupply()
            info_dict.update({"creator": pool_creator})

        if "shareHolders" in flags:
            pool_erc20 = DataToken(self.web3, pool_address)
            pool_holders = pool_erc20.calculate_token_holders(
                from_block, current_block, to_wei("0.001")
            )
            info_dict.update(
                {"numShareHolders": len(pool_holders), "shareHolders": pool_holders}
            )

        all_join_records = []
        all_exit_records = []
        if "liquidityTotals" in flags or "liquidity" in flags:
            all_join_records = self.get_all_liquidity_additions(
                pool_address, from_block, current_block, dt_address, raw_result=False
            )  # RPC_CALL
            total_ocn_additions = sum(
                r[2] for r in all_join_records if r[1] == self.ocean_address
            )
            all_exit_records = self.get_all_liquidity_removals(
                pool_address, from_block, current_block, dt_address, raw_result=False
            )  # RPC_CALL
            total_ocn_removals = sum(
                r[2] for r in all_exit_records if r[1] == self.ocean_address
            )
            info_dict.update(
                {
                    "totalOceanAdditions": total_ocn_additions,
                    "totalOceanRemovals": total_ocn_removals,
                }
            )

        if "liquidity" in flags:
            creator_shares = pool.balanceOf(pool_creator)
            creator_shares_percent = Decimal(creator_shares) / Decimal(shares)

            account_to_join_record = self.get_account_to_liquidity_records_map(
                all_join_records
            )
            ocean_additions = [
                r[2]
                for r in account_to_join_record[pool_creator]
                if r[1] == self.ocean_address
            ]
            dt_additions = [
                r[2] for r in account_to_join_record[pool_creator] if r[1] == dt_address
            ]

            account_to_exit_record = self.get_account_to_liquidity_records_map(
                all_exit_records
            )
            ocean_removals = [
                r[2]
                for r in account_to_exit_record.get(pool_creator, [])
                if r[1] == self.ocean_address
            ]
            dt_removals = [
                r[2]
                for r in account_to_exit_record.get(pool_creator, [])
                if r[1] == dt_address
            ]

            all_swap_records = self.get_all_swaps(
                pool_address, from_block, current_block, dt_address, raw_result=False
            )
            account_to_swap_record = self.get_account_to_liquidity_records_map(
                all_swap_records
            )
            ocean_in = [
                r[2]
                for r in account_to_swap_record.get(pool_creator, [])
                if r[1] == self.ocean_address
            ]
            dt_in = [
                r[2]
                for r in account_to_swap_record.get(pool_creator, [])
                if r[1] == dt_address
            ]
            ocean_out = [
                r[4]
                for r in account_to_swap_record.get(pool_creator, [])
                if r[3] == self.ocean_address
            ]
            dt_out = [
                r[4]
                for r in account_to_swap_record.get(pool_creator, [])
                if r[3] == dt_address
            ]

            swap_fee = from_wei(pool.getSwapFee())
            sum_ocean_additions = sum(ocean_additions)
            sum_ocean_removals = sum(ocean_removals)
            sum_ocn_swap_in = sum(ocean_in)
            sum_ocn_swap_out = sum(ocean_out)
            sum_dt_additions = sum(dt_additions)
            sum_dt_removals = sum(dt_removals)
            sum_dt_swap_in = sum(dt_in)
            sum_dt_swap_out = sum(dt_out)
            taxable_ocn = (
                sum_ocn_swap_in
                + sum_ocn_swap_out
                + sum_ocean_additions
                + sum_ocean_removals
                - ocean_additions[0]
            )
            taxable_dt = (
                sum_dt_swap_in
                + sum_dt_swap_out
                + sum_dt_additions
                + sum_dt_removals
                - dt_additions[0]
            )

            info_dict.update(
                {
                    "totalShares": shares,
                    "creator": pool_creator,
                    "creatorShares": creator_shares,
                    "creatorSharesPercentage": creator_shares_percent,
                    "creatorFirstOceanStake": ocean_additions[0],
                    "creatorFirstDTStake": dt_additions[0],
                    "creatorTotalOceanStake": sum(ocean_additions),
                    "creatorTotalDTStake": sum(dt_additions),
                    "creatorTotalOceanUnstake": sum(ocean_removals),
                    "creatorTotalDTUnstake": sum(dt_removals),
                    "totalOceanSwapIn": sum_ocn_swap_in,
                    "totalOceanSwapOut": sum_ocn_swap_out,
                    "totalDTSwapIn": sum_dt_swap_in,
                    "totalDTSwapOut": sum_dt_swap_out,
                    "totalSwapFeesDT": swap_fee * taxable_dt,
                    "totalSwapFeesOcean": swap_fee * taxable_ocn,
                }
            )

        info_dict.update(
            {"fromBlockNumber": from_block, "latestBlockNumber": current_block}
        )
        return info_dict

    @enforce_types
    def get_liquidity_history(self, pool_address):
        pool_block = self.get_creation_block(pool_address)

        join_records = self.get_all_liquidity_additions(pool_address, pool_block)
        exit_records = self.get_all_liquidity_removals(pool_address, pool_block)
        swap_records = self.get_all_swaps(pool_address, pool_block)

        ocn_address = self.ocean_address
        # Liquidity Additions
        ocn_liq_add_list = [
            (r.args.tokenAmountIn, r.blockNumber)
            for r in join_records
            if r.args.tokenIn == ocn_address
        ]
        dt_liq_add_list = [
            (r.args.tokenAmountIn, r.blockNumber)
            for r in join_records
            if r.args.tokenIn != ocn_address
        ]

        # Liquidity removals
        ocn_liq_rem_list = [
            (r.args.tokenAmountOut, r.blockNumber)
            for r in exit_records
            if r.args.tokenOut == ocn_address
        ]
        dt_liq_rem_list = [
            (r.args.tokenAmountOut, r.blockNumber)
            for r in exit_records
            if r.args.tokenOut != ocn_address
        ]

        # l.args.caller, l.args.tokenIn, l.args.tokenAmountIn, l.args.tokenOut, l.args.tokenAmountOut, l.blockNumber, l.transactionHash
        for r in swap_records:
            block_no = r.blockNumber
            if r.args.tokenIn == ocn_address:
                # ocn is the tokenIn
                ocn_liq_add_list.append((r.args.tokenAmountIn, block_no))
                dt_liq_rem_list.append((r.args.tokenAmountOut, block_no))
            else:  # ocn is the tokenOut
                ocn_liq_rem_list.append((r.args.tokenAmountOut, block_no))
                dt_liq_add_list.append((r.args.tokenAmountIn, block_no))

        ocn_liq_rem_list = [(-v, t) for v, t in ocn_liq_rem_list]
        dt_liq_rem_list = [(-v, t) for v, t in dt_liq_rem_list]

        ocn_add_remove_list = ocn_liq_add_list + ocn_liq_rem_list
        ocn_add_remove_list.sort(key=lambda x: x[1])

        dt_add_remove_list = dt_liq_add_list + dt_liq_rem_list
        dt_add_remove_list.sort(key=lambda x: x[1])

        firstblock, lastblock = ocn_add_remove_list[0][1], ocn_add_remove_list[-1][1]
        if dt_add_remove_list[0][1] < firstblock:
            firstblock = dt_add_remove_list[0][1]
        if dt_add_remove_list[-1][1] > lastblock:
            lastblock = dt_add_remove_list[-1][1]

        # get timestamps for blocknumber every 4 hours, assuming there is
        # 240 blocks/hour (on average) or 15 seconds block time..
        # use interpolation to fill in the other timestamps
        timestamps = []
        blocks = list(range(firstblock, lastblock, 240 * 4)) + [lastblock]
        for b in blocks:
            timestamps.append(self.web3.eth.get_block(b).timestamp)

        f = interp1d(blocks, timestamps)
        times = f([a[1] for a in ocn_add_remove_list])
        ocn_add_remove_list = [
            (a[0], times[i]) for i, a in enumerate(ocn_add_remove_list)
        ]
        times = f([a[1] for a in dt_add_remove_list])
        dt_add_remove_list = [
            (a[0], times[i]) for i, a in enumerate(dt_add_remove_list)
        ]
        return ocn_add_remove_list, dt_add_remove_list

    @enforce_types
    def get_user_balances(self, user_address, from_block):
        current_block = self.web3.eth.block_number
        pool = BPool(self.web3, None)

        pools = self.get_all_pools(from_block, chunk_size=5000, include_balance=False)
        join_logs = pool.get_join_logs(
            from_block, current_block, user_address, this_pool_only=False
        )
        join_logs = [lg for lg in join_logs if lg.address in pools]

        balances = {
            lg.address: DataToken(self.web3, lg.address).balanceOf(user_address)
            for lg in join_logs
        }
        return balances

    @enforce_types
    def get_creation_block(self, pool_address):
        bfactory = BFactory(self.web3, self.bfactory_address)
        current_block = self.web3.eth.block_number
        logs = bfactory.get_event_logs(
            "BPoolCreated",
            0,
            current_block,
            {"newBPoolAddress": pool_address},
            chunk_size=current_block,
        )
        if not logs:
            return {}
        assert len(logs) == 1, "cannot happen"

        return logs[0].blockNumber
