#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List

from enforce_typing import enforce_types

from ocean_lib.models import balancer_constants
from ocean_lib.models.btoken import BTokenBase
from ocean_lib.web3_internal.wallet import Wallet


class BPool(BTokenBase):
    CONTRACT_NAME = "BPool"

    EVENT_LOG_SWAP = "LOG_SWAP"
    EVENT_LOG_JOIN = "LOG_JOIN"
    EVENT_LOG_EXIT = "LOG_EXIT"
    EVENT_LOG_CALL = "LOG_CALL"
    EVENT_LOG_BPT = "LOG_BPT"
    EVENT_LOG_BPT_SS = "LOG_BPT_SS"
    EVENT_OPC_FEE = "OPCFee"
    EVENT_SWAP_FEE_CHANGED = "SwapFeeChanged"
    EVENT_PUBLISH_MARKET_FEE = "PublishMarketFee"
    EVENT_CONSUME_MARKET_FEE = "ConsumeMarketFee"
    EVENT_LOG_SWAP_FEES = "SWAP_FEES"
    EVENT_PUBLISH_MARKET_FEE_CHANGED = "PublishMarketFeeChanged"

    @property
    def event_LOG_SWAP(self):
        return self.events.LOG_SWAP()

    @property
    def event_LOG_JOIN(self):
        return self.events.LOG_JOIN()

    @property
    def event_LOG_EXIT(self):
        return self.events.LOG_EXIT()

    @property
    def event_LOG_CALL(self):
        return self.events.LOG_CALL()

    @property
    def event_LOG_BPT(self):
        return self.events.LOG_BPT()

    @property
    def event_LOG_BPT_SS(self):
        return self.events.LOG_BPT_SS()

    @property
    def event_OPCFee(self):
        return self.events.OPCFee()

    @property
    def event_SwapFeeChanged(self):
        return self.events.SwapFeeChanged()

    @property
    def event_SWAP_FEES(self):
        return self.events.SWAP_FEES()

    @property
    def event_PublishMarketFee(self):
        return self.events.PublishMarketFee()

    @property
    def event_ConsumeMarketFee(self):
        return self.events.ConsumeMarketFee()

    @property
    def event_PublishMarketFeeChanged(self):
        return self.events.PublishMarketFeeChanged()

    @enforce_types
    def setup(
        self,
        datatoken: str,
        datatoken_amount: int,
        datatoken_weight: int,
        base_token: str,
        base_token_amount: int,
        base_token_weight: int,
        publish_market_swap_fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        tx_id = self.send_transaction(
            "setup",
            (
                datatoken,
                datatoken_amount,
                datatoken_weight,
                base_token,
                base_token_amount,
                base_token_weight,
                publish_market_swap_fee_amount,
            ),
            from_wallet,
            {"gas": balancer_constants.GASLIMIT_BFACTORY_NEWBPOOL},
        )

        return tx_id

    @enforce_types
    def is_public_pool(self) -> bool:
        return self.contract.caller.isPublicSwap()

    @enforce_types
    def opc_fee(self) -> int:
        return self.contract.caller.getOPCFee()

    @enforce_types
    def community_fee(self, address: str) -> int:
        return self.contract.caller.communityFees(address)

    @enforce_types
    def publish_market_fee(self, address: str) -> int:
        return self.contract.caller.publishMarketFees(address)

    @enforce_types
    def is_initialized(self) -> bool:
        """Returns true if state is initialized."""
        return self.contract.caller.isInitialized()

    @enforce_types
    def is_finalized(self) -> bool:
        """Returns true if state is finalized.

        The `finalized` state lets users know that the weights, balances, and
        fees of this pool are immutable. In the `finalized` state, `SWAP`,
        `JOIN`, and `EXIT` are public. `CONTROL` capabilities are disabled.
        """
        return self.contract.caller.isFinalized()

    @enforce_types
    def is_bound(self, token_address: str) -> bool:
        """Returns True if the token is bound.

        A bound token has a valid balance and weight. A token cannot be bound
        without valid parameters which will enable e.g. `getSpotPrice` in terms
        of other tokens. However, disabling `isSwapPublic` will disable any
        interaction with this token in practice (assuming there are no existing
        tokens in the pool, which can always `exitPool`).
        """
        return self.contract.caller.isBound(token_address)

    @enforce_types
    def get_num_tokens(self) -> int:
        """
        How many tokens are bound to this pool.
        """
        return self.contract.caller.getNumTokens()

    @enforce_types
    def get_current_tokens(self) -> List[str]:
        """@return -- list of [token_addr:str]"""
        return self.contract.caller.getCurrentTokens()

    @enforce_types
    def get_final_tokens(self) -> List[str]:
        """@return -- list of [token_addr:str]"""
        return self.contract.caller.getFinalTokens()

    @enforce_types
    def collect_opc(self, dst: str, from_wallet: Wallet) -> str:
        return self.send_transaction("collectOPC", (dst,), from_wallet)

    @enforce_types
    def collect_market_fee(self, dst: str, from_wallet: Wallet) -> str:
        return self.send_transaction("collectMarketFee", (dst,), from_wallet)

    @enforce_types
    def update_publish_market_fee(
        self,
        new_collector: str,
        publish_market_swap_fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "updatePublishMarketFee",
            (new_collector, publish_market_swap_fee_amount),
            from_wallet,
        )

    @enforce_types
    def get_denormalized_weight(self, token_address: str) -> int:
        return self.contract.caller.getDenormalizedWeight(token_address)

    @enforce_types
    def get_total_denormalized_weight(self) -> int:
        return self.contract.caller.getTotalDenormalizedWeight()

    @enforce_types
    def get_normalized_weight(self, token_address: str) -> int:
        """
        The normalized weight of a token. The combined normalized weights of
        all tokens will sum up to 1. (Note: the actual sum may be 1 plus or
        minus a few wei due to division precision loss)
        """
        return self.contract.caller.getNormalizedWeight(token_address)

    @enforce_types
    def get_balance(self, token_address: str) -> int:
        return self.contract.caller.getBalance(token_address)

    @enforce_types
    def get_swap_fee(self) -> int:
        return self.contract.caller.getSwapFee()

    @enforce_types
    def get_controller(self) -> str:
        """
        Get the "controller" address, which can call `CONTROL` functions like
        `rebind`, `setSwapFee`, or `finalize`.
        """
        return self.contract.caller.getController()

    @enforce_types
    def get_datatoken_address(self) -> str:
        return self.contract.caller.getDatatokenAddress()

    @enforce_types
    def get_base_token_address(self) -> str:
        return self.contract.caller.getBaseTokenAddress()

    @enforce_types
    def calc_pool_in_single_out(self, address: str, amount: int):
        return self.contract.caller.calcPoolInSingleOut(address, amount)

    @enforce_types
    def calc_pool_out_single_in(self, address: str, amount: int):
        return self.contract.caller.calcPoolOutSingleIn(address, amount)

    @enforce_types
    def calc_single_out_pool_in(self, address: str, amount: int):
        return self.contract.caller.calcSingleOutPoolIn(address, amount)

    @enforce_types
    def calc_single_in_pool_out(self, address: str, amount: int):
        return self.contract.caller.calcSingleInPoolOut(address, amount)

    @enforce_types
    def set_swap_fee(self, lp_swap_fee_amount: int, from_wallet: Wallet) -> str:
        """
        Caller must be controller. Pool must NOT be finalized.
        """
        return self.send_transaction("setSwapFee", (lp_swap_fee_amount,), from_wallet)

    @enforce_types
    def finalize(self, from_wallet: Wallet) -> str:
        """
        This makes the pool **finalized**. This is a one-way transition. `bind`,
        `rebind`, `unbind`, `setSwapFee` and `setPublicSwap` will all throw
        `ERR_IS_FINALIZED` after pool is finalized. This also switches
        `isSwapPublic` to true.
        """
        return self.send_transaction("finalize", (), from_wallet)

    @enforce_types
    def bind(
        self, token_address: str, balance: int, weight: int, from_wallet: Wallet
    ) -> str:
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
            "bind", (token_address, balance, weight), from_wallet
        )

    @enforce_types
    def rebind(
        self, token_address: str, balance: int, weight: int, from_wallet: Wallet
    ) -> str:
        """
        Changes the parameters of an already-bound token. Performs the same
        validation on the parameters.
        """
        return self.send_transaction(
            "rebind", (token_address, balance, weight), from_wallet
        )

    @enforce_types
    def get_spot_price(self, token_in: str, token_out: str) -> int:
        return self.contract.caller.getSpotPrice(token_in, token_out)

    @enforce_types
    def get_amount_in_exact_out(
        self,
        token_in: str,
        token_out: str,
        token_amount_out: int,
        consume_market_swap_fee_amount: int,
    ) -> list:
        return self.contract.caller.getAmountOutExactIn(
            token_in, token_out, token_amount_out, consume_market_swap_fee_amount
        )

    @enforce_types
    def get_amount_out_exact_in(
        self,
        token_in: str,
        token_out: str,
        token_amount_in: int,
        consume_market_swap_fee_amount: int,
    ) -> list:
        return self.contract.caller.getAmountOutExactIn(
            token_in, token_out, token_amount_in, consume_market_swap_fee_amount
        )

    @enforce_types
    def join_pool(
        self, pool_amount_out: int, max_amounts_in: List[int], from_wallet: Wallet
    ) -> str:
        """
        Join the pool, getting `poolAmountOut` pool tokens. This will pull some
        of each of the currently trading tokens in the pool, meaning you must
        have called `approve` for each token for this pool. These values are
        limited by the array of `maxAmountsIn` in the order of the pool tokens.
        """
        return self.send_transaction(
            "joinPool", (pool_amount_out, max_amounts_in), from_wallet
        )

    @enforce_types
    def exit_pool(
        self, pool_amount_in: int, min_amounts_out: List[int], from_wallet: Wallet
    ) -> str:
        """
        Exit the pool, paying `poolAmountIn` pool tokens and getting some of
        each of the currently trading tokens in return. These values are
        limited by the array of `minAmountsOut` in the order of the pool tokens.
        """
        return self.send_transaction(
            "exitPool", (pool_amount_in, min_amounts_out), from_wallet
        )

    @enforce_types
    def swap_exact_amount_in(
        self,
        token_in: str,
        token_out: str,
        consume_market_swap_fee_address: str,
        token_amount_in: int,
        min_amount_out: int,
        max_price: int,
        consume_market_swap_fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        """Trades an exact `tokenAmountIn` of `tokenIn` taken from the caller by
        the pool, in exchange for at least `minAmountOut` of `tokenOut` given
        to the caller from the pool, with a maximum marginal price of
        `maxPrice`.

        The return values are what are limited by the arguments; you are
        guaranteed `tokenAmountOut >= minAmountOut` and
        `spotPriceAfter <= maxPrice)`.

        Args:
            token_in (str),
            token_out (str),
            consume_market_swap_fee_address (str),
            token_amount_in (int),
            min_amount_out (int),
            max_price (int),
            consume_market_swap_fee_amount (int),
            from_wallet (Wallet): wallet to sign the transaction with

        Returns:
            tokenAmountIn (int): amount of `tokenIn` sent to the pool
            spotPriceAfter (int): the new marginal spot price, ie, the result of `getSpotPrice` after the call
        """
        return self.send_transaction(
            "swapExactAmountIn",
            (
                [token_in, token_out, consume_market_swap_fee_address],
                [
                    token_amount_in,
                    min_amount_out,
                    max_price,
                    consume_market_swap_fee_amount,
                ],
            ),
            from_wallet,
        )

    @enforce_types
    def swap_exact_amount_out(
        self,
        token_in: str,
        token_out: str,
        consume_market_swap_fee_address: str,
        max_amount_in: int,
        token_amount_out: int,
        max_price: int,
        consume_market_swap_fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        """Swaps as little as possible limited of `tokenIn` for `tokenAmountOut` of `tokenOut`.
        with a maximum amount of `tokenIn` of `maxAmountIn` and a maximum marginal price of
        `maxPrice`.

        The return values are what are limited by the arguments; you are
        guaranteed `tokenAmountOut >= minAmountOut` and
        `spotPriceAfter <= maxPrice)`.

        Args:
            token_in (str),
            token_out (str),
            consume_market_swap_fee_address (str),
            max_amount_in (int),
            token_amount_out (int),
            max_price (int),
            consume_market_swap_fee_amount (int),
            from_wallet (Wallet): wallet to sign the transaction with

        Returns:
            tokenAmountOut (int): amount of token that came out of the pool
            spotPriceAfter (int): the new marginal spot price, ie, the result of `getSpotPrice` after the call
        """
        return self.send_transaction(
            "swapExactAmountOut",
            (
                [token_in, token_out, consume_market_swap_fee_address],
                [
                    max_amount_in,
                    token_amount_out,
                    max_price,
                    consume_market_swap_fee_amount,
                ],
            ),
            from_wallet,
        )

    @enforce_types
    def join_swap_extern_amount_in(
        self,
        token_amount_in: int,
        min_pool_amount_out: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Pay `tokenAmountIn` of token `tokenIn` to join the pool, getting
        `poolAmountOut` of the pool shares.
        """
        return self.send_transaction(
            "joinswapExternAmountIn",
            (token_amount_in, min_pool_amount_out),
            from_wallet,
        )

    @enforce_types
    def exit_swap_pool_amount_in(
        self,
        pool_amount_in: int,
        min_amount_out: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Pay `poolAmountIn` pool shares into the pool, getting `tokenAmountOut`
        of the given token `tokenOut` out of the pool.
        """
        return self.send_transaction(
            "exitswapPoolAmountIn",
            (pool_amount_in, min_amount_out),
            from_wallet,
        )
