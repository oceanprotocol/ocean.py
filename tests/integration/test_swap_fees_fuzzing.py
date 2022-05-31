#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import random
import traceback
from decimal import Decimal
from math import floor
from time import time

from ocean_lib.models.bpool import BPool
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.web3_internal.currency import from_wei, to_wei
from tests.resources.helper_functions import approx_from_wei, create_nft_erc20_with_pool

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


def test_fuzzing_pool_ocean(
    web3,
    config,
    ocean_token,
    consumer_wallet,
    another_consumer_wallet,
    publisher_wallet,
):
    """Test the liquidity pool contract with random values."""

    errors = []
    big_allowance = 10**10
    (
        swap_fee,
        swap_market_fee,
        ss_rate,
        ss_OCEAN_init_liquidity,
        swap_in_one_amount_in,
        swap_out_one_amount_out,
        swap_out_one_balance,
        swap_in_two_amount_in,
        swap_out_two_amount_out,
        swap_out_two_balance,
    ) = [0 for _ in range(10)]

    for _ in range(BPOOL_FUZZING_TESTS_NBR_OF_RUNS):
        try:
            # Seed random number generator
            random.seed(time())

            swap_fee = to_wei(Decimal(random.uniform(0.00001, 0.1)))
            swap_market_fee = to_wei(Decimal(random.uniform(0.00001, 0.1)))

            # Tests consumer calls deployPool(), we then check ocean and market fee"
            consumer_balance = ocean_token.balanceOf(consumer_wallet.address)

            # Pool base_token inital liquidity
            ss_OCEAN_init_liquidity = floor(
                consumer_balance * Decimal(random.uniform(0, 1))
            )
            ss_OCEAN_init_liquidity = (
                ss_OCEAN_init_liquidity if ss_OCEAN_init_liquidity > 0 else 1
            )

            ss_rate = to_wei(Decimal(random.uniform(1 / 10**6, 10**4)))

            bpool, datatoken, _, _ = create_nft_erc20_with_pool(
                web3=web3,
                config=config,
                publisher_wallet=consumer_wallet,
                base_token=ocean_token,
                swap_fee=swap_fee,
                swap_market_fee=swap_market_fee,
                initial_pool_liquidity=ss_OCEAN_init_liquidity,
                pool_initial_rate=ss_rate,
            )

            assert (
                ocean_token.balanceOf(consumer_wallet.address) + ss_OCEAN_init_liquidity
                == consumer_balance
            )

            assert ocean_token.balanceOf(bpool.address) == ss_OCEAN_init_liquidity
            assert datatoken.balanceOf(publisher_wallet.address) == 0

            publisher_dt_balance = datatoken.balanceOf(publisher_wallet.address)
            publisher_ocean_balance = ocean_token.balanceOf(publisher_wallet.address)

            # Large approvals for the rest of tests
            ocean_token.approve(bpool.address, to_wei(big_allowance), publisher_wallet)
            datatoken.approve(bpool.address, to_wei(big_allowance), publisher_wallet)

            swap_in_one_amount_in = get_random_max_token_amount_in(
                ocean_token, bpool, publisher_wallet.address
            )

            tx = bpool.swap_exact_amount_in(
                token_in=ocean_token.address,
                token_out=datatoken.address,
                consume_market_swap_fee_address=another_consumer_wallet.address,
                token_amount_in=swap_in_one_amount_in,
                min_amount_out=1,
                max_price=to_wei("1000000000"),
                consume_market_swap_fee_amount=0,
                from_wallet=publisher_wallet,
            )

            tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

            assert (datatoken.balanceOf(publisher_wallet.address) > 0) is True

            swap_fee_event = bpool.get_event_log(
                bpool.EVENT_LOG_SWAP,
                tx_receipt.blockNumber,
                web3.eth.block_number,
                None,
            )

            swap_event_args = swap_fee_event[0].args

            # Check swap balances
            assert (
                ocean_token.balanceOf(publisher_wallet.address)
                + swap_event_args.tokenAmountIn
                == publisher_ocean_balance
            )
            assert (
                datatoken.balanceOf(publisher_wallet.address)
                == publisher_dt_balance + swap_event_args.tokenAmountOut
            )

            # Tests publisher buys some DT - exactAmountOut
            publisher_dt_balance = datatoken.balanceOf(publisher_wallet.address)
            publisher_ocean_balance = ocean_token.balanceOf(publisher_wallet.address)
            dt_market_fee_balance = bpool.publish_market_fee(datatoken.address)
            ocean_market_fee_balance = bpool.publish_market_fee(ocean_token.address)

            swap_out_one_amount_out = get_random_max_token_amount_out(
                ocean_token, datatoken, bpool, publisher_wallet.address
            )
            swap_out_one_balance = ocean_token.balanceOf(publisher_wallet.address)

            tx = bpool.swap_exact_amount_out(
                token_in=ocean_token.address,
                token_out=datatoken.address,
                consume_market_swap_fee_address=another_consumer_wallet.address,
                max_amount_in=swap_out_one_balance,
                token_amount_out=swap_out_one_amount_out,
                max_price=to_wei("1000000"),
                consume_market_swap_fee_amount=0,
                from_wallet=publisher_wallet,
            )

            tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

            swap_fee_event = bpool.get_event_log(
                bpool.EVENT_LOG_SWAP,
                tx_receipt.blockNumber,
                web3.eth.block_number,
                None,
            )

            swap_event_args = swap_fee_event[0].args

            assert (
                ocean_token.balanceOf(publisher_wallet.address)
                + swap_event_args.tokenAmountIn
                == publisher_ocean_balance
            )
            assert (
                datatoken.balanceOf(publisher_wallet.address)
                == publisher_dt_balance + swap_event_args.tokenAmountOut
            )

            swap_fees_event = bpool.get_event_log(
                "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
            )

            swap_fees_event_args = swap_fees_event[0].args

            assert (
                ocean_market_fee_balance + swap_fees_event_args.marketFeeAmount
                == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
            )
            assert dt_market_fee_balance == bpool.publish_market_fee(datatoken.address)

            # Tests publisher swaps some DT back to Ocean with swapExactAmountIn, check swap custom fees
            assert bpool.is_finalized() is True

            datatoken.approve(bpool.address, to_wei(big_allowance), publisher_wallet)
            publisher_dt_balance = datatoken.balanceOf(publisher_wallet.address)
            dt_market_fee_balance = bpool.publish_market_fee(datatoken.address)

            swap_in_two_amount_in = get_random_max_token_amount_in(
                datatoken, bpool, publisher_wallet.address
            )

            tx = bpool.swap_exact_amount_in(
                token_in=datatoken.address,
                token_out=ocean_token.address,
                consume_market_swap_fee_address=another_consumer_wallet.address,
                token_amount_in=swap_in_two_amount_in,
                min_amount_out=1,
                max_price=to_wei("1000000000"),
                consume_market_swap_fee_amount=0,
                from_wallet=publisher_wallet,
            )

            tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

            swap_fees_event = bpool.get_event_log(
                "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
            )

            swap_fees_event_args = swap_fees_event[0].args

            assert approx_from_wei(
                to_wei(from_wei(swap_market_fee) * from_wei(swap_in_two_amount_in)),
                swap_fees_event_args.marketFeeAmount,
            )

            assert (
                dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
                == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
            )

            swap_event = bpool.get_event_log(
                bpool.EVENT_LOG_SWAP,
                tx_receipt.blockNumber,
                web3.eth.block_number,
                None,
            )

            swap_event_args = swap_event[0].args

            assert (
                datatoken.balanceOf(publisher_wallet.address)
                + swap_event_args.tokenAmountIn
                == publisher_dt_balance
            )

            assert approx_from_wei(
                to_wei(
                    from_wei(swap_event_args.tokenAmountIn) * from_wei(swap_market_fee)
                ),
                swap_fees_event_args.marketFeeAmount,
            )

            assert approx_from_wei(
                to_wei(from_wei(swap_event_args.tokenAmountIn) * from_wei(swap_fee)),
                swap_fees_event_args.LPFeeAmount,
            )

            # Tests publisher swaps some DT back to Ocean with swapExactAmountOut, check swap custom fees

            datatoken.approve(bpool.address, to_wei(big_allowance), publisher_wallet)
            publisher_dt_balance = datatoken.balanceOf(publisher_wallet.address)
            publisher_ocean_balance = ocean_token.balanceOf(publisher_wallet.address)
            dt_market_fee_balance = bpool.publish_market_fee(datatoken.address)

            swap_out_two_amount_out = get_random_max_token_amount_out(
                datatoken, ocean_token, bpool, publisher_wallet.address
            )
            swap_out_two_balance = datatoken.balanceOf(publisher_wallet.address)

            tx = bpool.swap_exact_amount_out(
                token_in=datatoken.address,
                token_out=ocean_token.address,
                consume_market_swap_fee_address=another_consumer_wallet.address,
                max_amount_in=swap_out_two_balance,
                token_amount_out=swap_out_two_amount_out,
                max_price=to_wei("10000000"),
                consume_market_swap_fee_amount=0,
                from_wallet=publisher_wallet,
            )

            tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

            swap_fees_event = bpool.get_event_log(
                "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
            )

            swap_fees_event_args = swap_fees_event[0].args
            assert (
                dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
                == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
            )

            swap_event = bpool.get_event_log(
                bpool.EVENT_LOG_SWAP,
                tx_receipt.blockNumber,
                web3.eth.block_number,
                None,
            )

            swap_event_args = swap_event[0].args

            assert (
                datatoken.balanceOf(publisher_wallet.address)
                + swap_event_args.tokenAmountIn
                == publisher_dt_balance
            )
            assert (
                publisher_ocean_balance + swap_event_args.tokenAmountOut
                == ocean_token.balanceOf(publisher_wallet.address)
            )

            assert approx_from_wei(
                to_wei(
                    from_wei(swap_event_args.tokenAmountIn) * from_wei(swap_market_fee)
                ),
                swap_fees_event_args.marketFeeAmount,
            )

            assert approx_from_wei(
                to_wei(from_wei(swap_event_args.tokenAmountIn) * from_wei(swap_fee)),
                swap_fees_event_args.LPFeeAmount,
            )
        except Exception:

            error = traceback.format_exc()

            dt_balance = (
                datatoken.balanceOf(publisher_wallet.address) if datatoken else 0
            )
            ocean_balance = (
                ocean_token.balanceOf(publisher_wallet.address) if ocean_token else 0
            )

            params = f"""
            Final balances:
            datatoken: {dt_balance} {from_wei(dt_balance)}
            ocean: {ocean_balance} {from_wei(ocean_balance)}

            Values
            swap_fee: {swap_fee} {from_wei(swap_fee)}
            swap_market_fee: {swap_market_fee} {from_wei(swap_market_fee)}
            ss_rate: {ss_rate}
            ss_OCEAN_init_liquidity: {ss_OCEAN_init_liquidity} {from_wei(ss_OCEAN_init_liquidity)}
            swap_in_one_amount_in: {swap_in_one_amount_in} {from_wei(swap_in_one_amount_in)}
            swap_out_one_amount_out: {swap_out_one_amount_out} {from_wei(swap_out_one_amount_out)}
            swap_out_one_balance: {swap_out_one_balance} {from_wei(swap_out_one_balance)}
            swap_in_two_amount_in: {swap_in_two_amount_in} {from_wei(swap_in_two_amount_in)}
            swap_out_two_amount_out: {swap_out_two_amount_out} {from_wei(swap_out_two_amount_out)}
            swap_out_two_balance: {swap_out_two_balance} {from_wei(swap_out_two_balance)}
            """

            errors.append([error, params])
        finally:
            final_datatoken_balance = datatoken.balanceOf(publisher_wallet.address)
            # sell all the datatokens before ending
            if final_datatoken_balance > 0 and datatoken and bpool:
                tx = bpool.swap_exact_amount_in(
                    token_in=datatoken.address,
                    token_out=ocean_token.address,
                    consume_market_swap_fee_address=another_consumer_wallet.address,
                    token_amount_in=min(
                        datatoken.balanceOf(publisher_wallet.address),
                        to_wei(
                            from_wei(bpool.get_max_in_ratio())
                            * from_wei(bpool.get_balance(datatoken.address))
                        ),
                    ),
                    min_amount_out=1,
                    max_price=to_wei("1000000000"),
                    consume_market_swap_fee_amount=0,
                    from_wallet=publisher_wallet,
                )

                web3.eth.wait_for_transaction_receipt(tx)
                last = datatoken.balanceOf(publisher_wallet.address)
                print(last)

    # print errors
    for error in errors:
        print(error[0])
        print(error[1])
        print("\n")

    print(f"Number of errors: {len(errors)}")

    assert not errors
