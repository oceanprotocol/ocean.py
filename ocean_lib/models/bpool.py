#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List, Tuple

from enforce_typing import enforce_types

from ocean_lib.models.btoken import BTokenBase
from ocean_lib.web3_internal.wallet import Wallet


class BPool(BTokenBase):
    CONTRACT_NAME = "BPool"

    EVENT_LOG_SWAP = "LOG_SWAP"
    EVENT_LOG_JOIN = "LOG_JOIN"
    EVENT_LOG_SETUP = "LOG_SETUP"
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
    EVENT_GULPED = "Gulped"

    @property
    def event_LOG_SWAP(self):
        return self.events.LOG_SWAP()

    @property
    def event_LOG_JOIN(self):
        return self.events.LOG_JOIN()

    @property
    def event_LOG_SETUP(self):
        return self.events.LOG_SETUP()

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

    @property
    def event_Gulped(self):
        return self.events.Gulped()

    @enforce_types
    def get_publish_market_collector(self) -> str:
        return self.contract.caller._publishMarketCollector()

    @enforce_types
    def get_id(self) -> int:
        return self.contract.caller.getId()

    @enforce_types
    def is_initialized(self) -> bool:
        """Returns true if state is initialized."""
        return self.contract.caller.isInitialized()

    @enforce_types
    def is_public_swap(self) -> bool:
        return self.contract.caller.isPublicSwap()

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
    def collect_opc(self, from_wallet: Wallet) -> str:
        return self.send_transaction("collectOPC", (), from_wallet)

    @enforce_types
    def get_current_opc_fees(self) -> Tuple[List[str], List[int]]:
        """Get the current amount of fees which can be withdrawned by OPC

        :return: List of token addresses and List of amounts
        """
        return self.contract.caller.getCurrentOPCFees()

    @enforce_types
    def get_current_market_fees(self) -> Tuple[List[str], List[int]]:
        """Get the current amount of fees which can be withdrawned by _publishMarketCollector

        :return: List of token addresses and List of amounts
        """
        return self.contract.caller.getCurrentMarketFees()

    @enforce_types
    def collect_market_fee(self, from_wallet: Wallet) -> str:
        return self.send_transaction("collectMarketFee", (), from_wallet)

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
    def get_market_fee(self) -> int:
        return self.contract.caller.getMarketFee()

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
    def set_swap_fee(self, lp_swap_fee_amount: int, from_wallet: Wallet) -> str:
        """
        Caller must be controller. Pool must NOT be finalized.
        """
        return self.send_transaction("setSwapFee", (lp_swap_fee_amount,), from_wallet)

    @enforce_types
    def get_spot_price(
        self, token_in: str, token_out: str, consume_market_swap_fee
    ) -> int:
        return self.contract.caller.getSpotPrice(
            token_in, token_out, consume_market_swap_fee
        )

    @enforce_types
    def get_amount_in_exact_out(
        self,
        token_in: str,
        token_out: str,
        token_amount_out: int,
        consume_market_swap_fee_amount: int,
    ) -> list:
        return self.contract.caller.getAmountInExactOut(
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

    @enforce_types
    def calc_single_out_pool_in(self, address: str, amount: int):
        return self.contract.caller.calcSingleOutPoolIn(address, amount)

    @enforce_types
    def calc_pool_in_single_out(self, address: str, amount: int):
        return self.contract.caller.calcPoolInSingleOut(address, amount)

    @enforce_types
    def calc_single_in_pool_out(self, address: str, amount: int):
        return self.contract.caller.calcSingleInPoolOut(address, amount)

    @enforce_types
    def calc_pool_out_single_in(self, address: str, amount: int):
        return self.contract.caller.calcPoolOutSingleIn(address, amount)

    @enforce_types
    def gulp(self, address: str, from_wallet: Wallet):
        return self.send_transaction(
            "gulp",
            (address),
            from_wallet,
        )

    # BMath.sol

    @enforce_types
    def swap_publish_market_fee(self) -> int:
        return self.contract.caller._swapPublishMarketFee()

    @enforce_types
    def community_fee(self, address: str) -> int:
        return self.contract.caller.communityFees(address)

    @enforce_types
    def publish_market_fee(self, address: str) -> int:
        return self.contract.caller.publishMarketFees(address)

    @enforce_types
    def get_opc_fee(self) -> int:
        return self.contract.caller.getOPCFee()

    @enforce_types
    def calc_in_given_out(
        self,
        token_in: str,
        token_out: str,
        amount_out: int,
        consume_market_swap_fee: int,
    ) -> Tuple[int, int, Tuple[int, int, int, int]]:
        """
        :return: [amountIn, amountAddedToPool, [LPFee, OPCFee, publishMarketFee, consumeMarketFee]]
        :rtype: Tuple[int, int, Tuple[int, int, int, int]]
        """
        return self.contract.caller.calcInGivenOut(
            [
                self.get_balance(token_in),
                self.get_denormalized_weight(token_in),
                self.get_balance(token_out),
                self.get_denormalized_weight(token_out),
            ],
            amount_out,
            consume_market_swap_fee,
        )

    @enforce_types
    def calc_out_given_in(
        self, token_in: str, token_out: str, amount_in: int, consume_market_swap_fee
    ) -> Tuple[int, int, Tuple[int, int, int, int]]:
        """
        :return: [amountOut, amountAddedToPool, [LPFee, OPCFee, publishMarketFee, consumeMarketFee]]
        :rtype: Tuple[int, int, Tuple[int, int, int, int]]
        """
        return self.contract.caller.calcOutGivenIn(
            [
                self.get_balance(token_in),
                self.get_denormalized_weight(token_in),
                self.get_balance(token_out),
                self.get_denormalized_weight(token_out),
            ],
            amount_in,
            consume_market_swap_fee,
        )
