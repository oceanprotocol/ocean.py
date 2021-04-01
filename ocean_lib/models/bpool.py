#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import typing

from eth_utils import remove_0x_prefix
from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.models import balancer_constants
from ocean_lib.ocean import util
from ocean_lib.web3_internal.wallet import Wallet
from web3.utils.events import get_event_data

from .btoken import BToken

logger = logging.getLogger(__name__)


@enforce_types_shim
class BPool(BToken):
    CONTRACT_NAME = "BPool"

    def __init__(self, *args, **kwargs):
        """Initialises BPool object."""
        BToken.__init__(self, *args, **kwargs)
        self._ccontract = self.contract_concise

    def __str__(self):
        """Formats with attributes as key, value pairs."""
        s = []
        s += ["BPool:"]
        s += [f"  pool_address={self.address}"]
        s += [f"  controller address = {self.getController()}"]
        s += [f"  isPublicSwap = {self.isPublicSwap()}"]
        s += [f"  isFinalized = {self.isFinalized()}"]

        swap_fee = util.from_base_18(self.getSwapFee())
        s += ["  swapFee = %.2f%%" % (swap_fee * 100.0)]

        s += [f"  numTokens = {self.getNumTokens()}"]
        cur_addrs = self.getCurrentTokens()
        cur_symbols = [BToken(addr).symbol() for addr in cur_addrs]
        s += [f"  currentTokens (as symbols) = {', '.join(cur_symbols)}"]

        if self.isFinalized():
            final_addrs = self.getFinalTokens()
            final_symbols = [BToken(addr).symbol() for addr in final_addrs]
            s += [f"  finalTokens (as symbols) = {final_symbols}"]

        s += ["  is bound:"]
        for addr, symbol in zip(cur_addrs, cur_symbols):
            s += [f"    {symbol}: {self.isBound(addr)}"]

        s += ["  weights (fromBase):"]
        for addr, symbol in zip(cur_addrs, cur_symbols):
            denorm_w = util.from_base_18(self.getDenormalizedWeight(addr))
            norm_w = util.from_base_18(self.getNormalizedWeight(addr))
            s += [f"    {symbol}: denorm_w={denorm_w}, norm_w={norm_w} "]

        total_denorm_w = util.from_base_18(self.getTotalDenormalizedWeight())
        s += [f"    total_denorm_w={total_denorm_w}"]

        s += ["  balances (fromBase):"]
        for addr, symbol in zip(cur_addrs, cur_symbols):
            balance_base = self.getBalance(addr)
            dec = BToken(addr).decimals()
            balance = util.from_base(balance_base, dec)
            s += [f"    {symbol}: {balance}"]

        return "\n".join(s)

    def setup(
        self,
        data_token: str,
        data_token_amount: int,
        data_token_weight: int,
        base_token: str,
        base_token_amount: int,
        base_token_weight: int,
        swap_fee: int,
        from_wallet: Wallet,
    ) -> str:

        tx_id = self.send_transaction(
            "setup",
            (
                data_token,
                data_token_amount,
                data_token_weight,
                base_token,
                base_token_amount,
                base_token_weight,
                swap_fee,
            ),
            from_wallet,
            {"gas": balancer_constants.GASLIMIT_BFACTORY_NEWBPOOL},
        )

        return tx_id

    # ============================================================
    # reflect BPool Solidity methods: everything at Balancer Interfaces "BPool"
    # docstrings are adapted from Balancer API
    # https://docs.balancer.finance/smart-contracts/api

    # ==== View Functions
    def isPublicSwap(self) -> bool:
        return self._ccontract.isPublicSwap()

    def isFinalized(self) -> bool:
        """Returns true if state is finalized.

        The `finalized` state lets users know that the weights, balances, and
        fees of this pool are immutable. In the `finalized` state, `SWAP`,
        `JOIN`, and `EXIT` are public. `CONTROL` capabilities are disabled.
        (https://docs.balancer.finance/smart-contracts/api#access-control)
        """
        return self._ccontract.isFinalized()

    def isBound(self, token_address: str) -> bool:
        """Returns True if the token is bound.

        A bound token has a valid balance and weight. A token cannot be bound
        without valid parameters which will enable e.g. `getSpotPrice` in terms
        of other tokens. However, disabling `isSwapPublic` will disable any
        interaction with this token in practice (assuming there are no existing
        tokens in the pool, which can always `exitPool`).
        """
        return self._ccontract.isBound(token_address)

    def getNumTokens(self) -> int:
        """
        How many tokens are bound to this pool.
        """
        return self._ccontract.getNumTokens()

    def getCurrentTokens(self) -> typing.List[str]:
        """@return -- list of [token_addr:str]"""
        return self._ccontract.getCurrentTokens()

    def getFinalTokens(self) -> typing.List[str]:
        """@return -- list of [token_addr:str]"""
        return self._ccontract.getFinalTokens()

    def getDenormalizedWeight(self, token_address: str) -> int:
        return self._ccontract.getDenormalizedWeight(token_address)

    def getTotalDenormalizedWeight(self) -> int:
        return self._ccontract.getTotalDenormalizedWeight()

    def getNormalizedWeight(self, token_address: str) -> int:
        """
        The normalized weight of a token. The combined normalized weights of
        all tokens will sum up to 1. (Note: the actual sum may be 1 plus or
        minus a few wei due to division precision loss)
        """
        return self._ccontract.getNormalizedWeight(token_address)

    def getBalance(self, token_address: str) -> int:
        return self._ccontract.getBalance(token_address)

    def getSwapFee(self) -> int:
        return self._ccontract.getSwapFee()

    def getController(self) -> str:
        """
        Get the "controller" address, which can call `CONTROL` functions like
        `rebind`, `setSwapFee`, or `finalize`.
        """
        return self._ccontract.getController()

    # ==== Controller Functions

    def setSwapFee(self, swapFee_base: int, from_wallet: Wallet):
        """
        Caller must be controller. Pool must NOT be finalized.
        """
        return self.send_transaction("setSwapFee", (swapFee_base,), from_wallet)

    def setController(self, manager_address: str, from_wallet: Wallet):
        return self.send_transaction("setController", (manager_address,), from_wallet)

    def setPublicSwap(self, public: bool, from_wallet: Wallet):
        """
        Makes `isPublicSwap` return `_publicSwap`. Requires caller to be
        controller and pool not to be finalized. Finalized pools always have
        public swap.
        """
        return self.send_transaction("setPublicSwap", (public,), from_wallet)

    def finalize(self, from_wallet: Wallet):
        """
        This makes the pool **finalized**. This is a one-way transition. `bind`,
        `rebind`, `unbind`, `setSwapFee` and `setPublicSwap` will all throw
        `ERR_IS_FINALIZED` after pool is finalized. This also switches
        `isSwapPublic` to true.
        """
        return self.send_transaction("finalize", (), from_wallet)

    def bind(
        self,
        token_address: str,
        balance_base: int,
        weight_base: int,
        from_wallet: Wallet,
    ):
        """
        Binds the token with address `token`. Tokens will be pushed/pulled from
        caller to adjust match new balance. Token must not already be bound.
        `balance` must be a valid balance and denorm must be a valid denormalized
        weight. `bind` creates the token record and then calls `rebind` for
        updating pool weights and token transfers.

        Possible errors:
        -`ERR_NOT_CONTROLLER` -- caller is not the controller
        -`ERR_IS_BOUND` -- T is already bound
        -`ERR_IS_FINALIZED` -- isFinalized() is true
        -`ERR_ERC20_FALSE` -- ERC20 token returned false
        -`ERR_MAX_TOKENS` -- Only 8 tokens are allowed per pool
        -unspecified error thrown by token
        """
        return self.send_transaction(
            "bind", (token_address, balance_base, weight_base), from_wallet
        )

    def rebind(
        self,
        token_address: str,
        balance_base: int,
        weight_base: int,
        from_wallet: Wallet,
    ):
        """
        Changes the parameters of an already-bound token. Performs the same
        validation on the parameters.
        """
        return self.send_transaction(
            "rebind", (token_address, balance_base, weight_base), from_wallet
        )

    def unbind(self, token_address: str, from_wallet: Wallet):
        """
        Unbinds a token, clearing all of its parameters. Exit fee is charged
        and the remaining balance is sent to caller.
        """
        return self.send_transaction("unbind", (token_address,), from_wallet)

    def gulp(self, token_address: str, from_wallet: Wallet):
        """
        This syncs the internal `balance` of `token` within a pool with the
        actual `balance` registered on the ERC20 contract. This is useful to
        wallet for airdropped tokens or any tokens sent to the pool without
        using the `join` or `joinSwap` methods.

        As an example, pools that contain `COMP` tokens can have the `COMP`
        balance updated with the rewards sent by Compound (https://etherscan.io/tx/0xeccd42bf2b8a180a561c026717707d9024a083059af2f22c197ee511d1010e23).
        In order for any airdrop balance to be gulped, the token must be bound
        to the pool. So if a shared pool (which is immutable) does not have a
        given token, any airdrops in that token will be locked in the pool
        forever.
        """
        return self.send_transaction("gulp", (token_address,), from_wallet)

    # ==== Price Functions

    def getSpotPrice(self, tokenIn_address: str, tokenOut_address: str) -> int:
        return self._ccontract.getSpotPrice(tokenIn_address, tokenOut_address)

    def getSpotPriceSansFee(self, tokenIn_address: str, tokenOut_address: str) -> int:
        return self._ccontract.getSpotPriceSansFee(tokenIn_address, tokenOut_address)

    # ==== Trading and Liquidity Functions

    def joinPool(
        self,
        poolAmountOut_base: int,
        maxAmountsIn_base: typing.List[int],
        from_wallet: Wallet,
    ):
        """
        Join the pool, getting `poolAmountOut` pool tokens. This will pull some
        of each of the currently trading tokens in the pool, meaning you must
        have called `approve` for each token for this pool. These values are
        limited by the array of `maxAmountsIn` in the order of the pool tokens.
        """
        return self.send_transaction(
            "joinPool", (poolAmountOut_base, maxAmountsIn_base), from_wallet
        )

    def exitPool(
        self,
        poolAmountIn_base: int,
        minAmountsOut_base: typing.List[int],
        from_wallet: Wallet,
    ):
        """
        Exit the pool, paying `poolAmountIn` pool tokens and getting some of
        each of the currently trading tokens in return. These values are
        limited by the array of `minAmountsOut` in the order of the pool tokens.
        """
        return self.send_transaction(
            "exitPool", (poolAmountIn_base, minAmountsOut_base), from_wallet
        )

    def swapExactAmountIn(
        self,
        tokenIn_address: str,
        tokenAmountIn_base: int,
        tokenOut_address: str,
        minAmountOut_base: int,
        maxPrice_base: int,
        from_wallet: Wallet,
    ):
        """
        Trades an exact `tokenAmountIn` of `tokenIn` taken from the caller by
        the pool, in exchange for at least `minAmountOut` of `tokenOut` given
        to the caller from the pool, with a maximum marginal price of
        `maxPrice`.

        Returns `(tokenAmountOut`, `spotPriceAfter)`, where `tokenAmountOut`
        is the amount of token that came out of the pool, and `spotPriceAfter`
        is the new marginal spot price, ie, the result of `getSpotPrice` after
        the call. (These values are what are limited by the arguments; you are
        guaranteed `tokenAmountOut >= minAmountOut` and
        `spotPriceAfter <= maxPrice)`.
        """
        return self.send_transaction(
            "swapExactAmountIn",
            (
                tokenIn_address,
                tokenAmountIn_base,
                tokenOut_address,
                minAmountOut_base,
                maxPrice_base,
            ),
            from_wallet,
        )

    def swapExactAmountOut(
        self,
        tokenIn_address: str,
        maxAmountIn_base: int,
        tokenOut_address: str,
        tokenAmountOut_base: int,
        maxPrice_base: int,
        from_wallet: Wallet,
    ):
        return self.send_transaction(
            "swapExactAmountOut",
            (
                tokenIn_address,
                maxAmountIn_base,
                tokenOut_address,
                tokenAmountOut_base,
                maxPrice_base,
            ),
            from_wallet,
        )

    def joinswapExternAmountIn(
        self,
        tokenIn_address: str,
        tokenAmountIn_base: int,
        minPoolAmountOut_base: int,
        from_wallet: Wallet,
    ):
        """
        Pay `tokenAmountIn` of token `tokenIn` to join the pool, getting
        `poolAmountOut` of the pool shares.
        """
        return self.send_transaction(
            "joinswapExternAmountIn",
            (tokenIn_address, tokenAmountIn_base, minPoolAmountOut_base),
            from_wallet,
        )

    def joinswapPoolAmountOut(
        self,
        tokenIn_address: str,
        poolAmountOut_base: int,
        maxAmountIn_base: int,
        from_wallet: Wallet,
    ):
        """
        Specify `poolAmountOut` pool shares that you want to get, and a token
        `tokenIn` to pay with. This costs `maxAmountIn` tokens (these went
        into the pool).
        """
        return self.send_transaction(
            "joinswapPoolAmountOut",
            (tokenIn_address, poolAmountOut_base, maxAmountIn_base),
            from_wallet,
        )

    def exitswapPoolAmountIn(
        self,
        tokenOut_address: str,
        poolAmountIn_base: int,
        minAmountOut_base: int,
        from_wallet: Wallet,
    ):
        """
        Pay `poolAmountIn` pool shares into the pool, getting `tokenAmountOut`
        of the given token `tokenOut` out of the pool.
        """
        return self.send_transaction(
            "exitswapPoolAmountIn",
            (tokenOut_address, poolAmountIn_base, minAmountOut_base),
            from_wallet,
        )

    def exitswapExternAmountOut(
        self,
        tokenOut_address: str,
        tokenAmountOut_base: int,
        maxPoolAmountIn_base: int,
        from_wallet: Wallet,
    ):
        """
        Specify `tokenAmountOut` of token `tokenOut` that you want to get out
        of the pool. This costs `poolAmountIn` pool shares (these went into
        the pool).
        """
        return self.send_transaction(
            "exitswapExternAmountOut",
            (tokenOut_address, tokenAmountOut_base, maxPoolAmountIn_base),
            from_wallet,
        )

    # ==== Balancer Pool as ERC20
    def totalSupply(self) -> int:
        return self._ccontract.totalSupply()

    def balanceOf(self, whom_address: str) -> int:
        return self._ccontract.balanceOf(whom_address)

    def allowance(self, src_address: str, dst_address: str) -> int:
        return self._ccontract.allowance(src_address, dst_address)

    def approve(self, dst_address: str, amt_base: int, from_wallet: Wallet):
        return self.send_transaction("approve", (dst_address, amt_base), from_wallet)

    def transfer(self, dst_address: str, amt_base: int, from_wallet: Wallet):
        return self.send_transaction("transfer", (dst_address, amt_base), from_wallet)

    def transferFrom(
        self, src_address: str, dst_address: str, amt_base: int, from_wallet: Wallet
    ):
        return self.send_transaction(
            "transferFrom", (dst_address, src_address, amt_base), from_wallet
        )

    # ===== Calculators
    def calcSpotPrice(
        self,
        tokenBalanceIn_base: int,
        tokenWeightIn_base: int,
        tokenBalanceOut_base: int,
        tokenWeightOut_base: int,
        swapFee_base: int,
    ) -> int:
        """Returns spotPrice_base."""
        return self._ccontract.calcSpotPrice(
            tokenBalanceIn_base,
            tokenWeightIn_base,
            tokenBalanceOut_base,
            tokenWeightOut_base,
            swapFee_base,
        )

    def calcOutGivenIn(
        self,
        tokenBalanceIn_base: int,
        tokenWeightIn_base: int,
        tokenBalanceOut: int,
        tokenWeightOut_base: int,
        tokenAmountIn_base: int,
        swapFee_base: int,
    ) -> int:
        """Returns tokenAmountOut_base."""
        return self._ccontract.calcOutGivenIn(
            tokenBalanceIn_base,
            tokenWeightIn_base,
            tokenBalanceOut,
            tokenWeightOut_base,
            tokenAmountIn_base,
            swapFee_base,
        )

    def calcInGivenOut(
        self,
        tokenBalanceIn_base: int,
        tokenWeightIn_base: int,
        tokenBalanceOut_base: int,
        tokenWeightOut_base: int,
        tokenAmountOut_base: int,
        swapFee_base: int,
    ) -> int:
        """Returns tokenAmountIn_base."""
        return self._ccontract.calcInGivenOut(
            tokenBalanceIn_base,
            tokenWeightIn_base,
            tokenBalanceOut_base,
            tokenWeightOut_base,
            tokenAmountOut_base,
            swapFee_base,
        )

    def calcPoolOutGivenSingleIn(
        self,
        tokenBalanceIn_base: int,
        tokenWeightIn_base: int,
        poolSupply_base: int,
        totalWeight_base: int,
        tokenAmountIn_base: int,
        swapFee_base: int,
    ) -> int:
        """Returns poolAmountOut_base."""
        return self._ccontract.calcPoolOutGivenSingleIn(
            tokenBalanceIn_base,
            tokenWeightIn_base,
            poolSupply_base,
            totalWeight_base,
            tokenAmountIn_base,
            swapFee_base,
        )

    def calcSingleInGivenPoolOut(
        self,
        tokenBalanceIn_base: int,
        tokenWeightIn_base: int,
        poolSupply_base: int,
        totalWeight_base: int,
        poolAmountOut_base: int,
        swapFee_base: int,
    ) -> int:
        """Returns tokenAmountIn_base."""
        return self._ccontract.calcSingleInGivenPoolOut(
            tokenBalanceIn_base,
            tokenWeightIn_base,
            poolSupply_base,
            totalWeight_base,
            poolAmountOut_base,
            swapFee_base,
        )

    def calcSingleOutGivenPoolIn(
        self,
        tokenBalanceOut_base: int,
        tokenWeightOut_base: int,
        poolSupply_base: int,
        totalWeight_base: int,
        poolAmountIn_base: int,
        swapFee_base: int,
    ) -> int:
        """Returns tokenAmountOut_base."""
        return self._ccontract.calcSingleOutGivenPoolIn(
            tokenBalanceOut_base,
            tokenWeightOut_base,
            poolSupply_base,
            totalWeight_base,
            poolAmountIn_base,
            swapFee_base,
        )

    def calcPoolInGivenSingleOut(
        self,
        tokenBalanceOut_base: int,
        tokenWeightOut_base: int,
        poolSupply_base: int,
        totalWeight_base: int,
        tokenAmountOut_base: int,
        swapFee_base: int,
    ) -> int:
        """Returns poolAmountIn_base."""
        return self._ccontract.calcPoolInGivenSingleOut(
            tokenBalanceOut_base,
            tokenWeightOut_base,
            poolSupply_base,
            totalWeight_base,
            tokenAmountOut_base,
            swapFee_base,
        )

    # ===== Events

    def get_liquidity_logs(
        self,
        event_name,
        web3,
        from_block,
        to_block=None,
        user_address=None,
        this_pool_only=True,
    ):
        """
        :param event_name: str, one of LOG_JOIN, LOG_EXIT, LOG_SWAP
        """
        topic0 = self.get_event_signature(event_name)
        to_block = to_block or "latest"
        _filter = {"fromBlock": from_block, "toBlock": to_block, "topics": [topic0]}
        if this_pool_only:
            _filter["address"] = self.address

        if user_address:
            assert web3.isChecksumAddress(user_address)
            _filter["topics"].append(
                f"0x000000000000000000000000{remove_0x_prefix(user_address).lower()}"
            )

        event = getattr(self.events, event_name)
        event_abi = event().abi
        try:
            logs = web3.eth.getLogs(_filter)
            logs = [get_event_data(event_abi, lg) for lg in logs]
        except ValueError as e:
            logger.error(
                f"get_join_logs failed -> web3.eth.getLogs (filter={_filter}) failed: "
                f"{e}.."
            )
            logs = []

        return logs

    def get_join_logs(
        self, web3, from_block, to_block=None, user_address=None, this_pool_only=True
    ):
        return self.get_liquidity_logs(
            "LOG_JOIN", web3, from_block, to_block, user_address, this_pool_only
        )

    def get_exit_logs(
        self, web3, from_block, to_block=None, user_address=None, this_pool_only=True
    ):
        return self.get_liquidity_logs(
            "LOG_EXIT", web3, from_block, to_block, user_address, this_pool_only
        )

    def get_swap_logs(
        self, web3, from_block, to_block=None, user_address=None, this_pool_only=True
    ):
        return self.get_liquidity_logs(
            "LOG_SWAP", web3, from_block, to_block, user_address, this_pool_only
        )
