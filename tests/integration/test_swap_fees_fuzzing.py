#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import random
from time import time

import pytest

import traceback
import logging

from ocean_lib.models.bpool import BPool
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.structures.abi_tuples import CreateErc20Data, PoolData
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import from_wei, to_wei
from tests.resources.helper_functions import (
    approx_from_wei,
    deploy_erc721_erc20,
    get_address_of_type,
)
from math import floor


def _deploy_erc721_token(config, web3, factory_deployer_wallet, manager_wallet):
    erc721_nft = deploy_erc721_erc20(web3, config, factory_deployer_wallet)

    erc721_nft.add_to_725_store_list(manager_wallet.address, factory_deployer_wallet)
    erc721_nft.add_to_create_erc20_list(manager_wallet.address, factory_deployer_wallet)
    erc721_nft.add_to_metadata_list(manager_wallet.address, factory_deployer_wallet)
    return erc721_nft


def get_random_max_token_amount_in(
    token_in: ERC20Token, bpool: BPool, wallet_address: str
) -> int:
    """Returns a random amount of tokens of token_in that is less than the max_in_ratio_in of the pool and
    less than the balance of the wallet in the token_in"""
    return floor(
        min(
            token_in.balanceOf(wallet_address),
            to_wei(
                from_wei(bpool.get_max_in_ratio())
                * from_wei(bpool.get_balance(token_in.address))
            ),
        )
        * random.uniform(0.01, 1)
    )


def get_random_max_token_amount_out(
    token_in: ERC20Token, token_out: ERC20Token, bpool: BPool, wallet_address: str
) -> int:
    """Returns a random amount of tokens of token_out that is less than the max_out_ratio_out of the pool and
    and less than the maximum amount of token_out that can be purchased by the wallet_address"""
    pool_token_out_balance = bpool.get_balance(token_out.address)
    max_out_ratio = bpool.get_max_out_ratio()
    max_out_ratio_limit = to_wei(
        from_wei(max_out_ratio) * from_wei(pool_token_out_balance)
    )
    return floor(
        random.uniform(0.001, 1)
        * min(
            token_in.balanceOf(wallet_address)
            * bpool.get_spot_price(token_in.address, token_out.address, 0)
            / to_wei(1),
            max_out_ratio_limit,
        )
    )


# @pytest.mark.skip(reason="This test is slow and not needed in the CI")
@pytest.mark.nosetup_all
def test_fuzzing_pool_ocean(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    another_consumer_wallet,
    publisher_wallet,
    factory_router,
):
    """Test the liquidity pool contract with random values."""

    number_of_runs = 20

    errors = []

    (
        cap,
        swap_fee,
        swap_market_fee,
        ss_rate,
        ss_DT_vest_amt,
        ss_DT_vested_blocks,
        ss_OCEAN_init_liquidity,
        swap_in_one_amount_in,
        swap_out_one_amount_out,
        swap_out_one_balance,
        swap_in_two_amount_in,
        swap_out_two_amount_out,
        swap_out_two_balance,
    ) = [0 for _ in range(13)]

    for _ in range(number_of_runs):
        try:
            try:
                mint_fake_OCEAN(config)
            except:
                # print("We don't need more balance.")
                pass

            erc721_factory = ERC721FactoryContract(
                web3, get_address_of_type(config, "ERC721Factory")
            )
            side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
            erc721_nft = _deploy_erc721_token(
                config, web3, factory_deployer_wallet, consumer_wallet
            )

            # Seed random number generator
            random.seed(time())

            # Tests consumer deploys a new erc20DT, assigning himself as minter
            cap = web3.toWei(random.randint(100, 1000000), "ether")

            tx = erc721_nft.create_erc20(
                CreateErc20Data(
                    1,
                    ["ERC20DT1", "ERC20DT1Symbol"],
                    [
                        consumer_wallet.address,
                        factory_deployer_wallet.address,
                        consumer_wallet.address,
                        ZERO_ADDRESS,
                    ],
                    [cap, 0],
                    [b""],
                ),
                consumer_wallet,
            )
            tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
            event = erc721_factory.get_event_log(
                erc721_nft.EVENT_TOKEN_CREATED,
                tx_receipt.blockNumber,
                web3.eth.block_number,
                None,
            )
            erc20_address = event[0].args.newTokenAddress
            erc20_token = ERC20Token(web3, erc20_address)

            assert erc20_token.get_permissions(consumer_wallet.address)[0] is True

            swap_fee = web3.toWei(random.uniform(0.00001, 0.1), "ether")
            swap_market_fee = web3.toWei(random.uniform(0.00001, 0.1), "ether")

            # Tests consumer calls deployPool(), we then check ocean and market fee"
            ocean_contract = ERC20Token(
                web3=web3, address=get_address_of_type(config, "Ocean")
            )
            consumer_balance = ocean_contract.balanceOf(consumer_wallet.address)
            ss_OCEAN_init_liquidity = floor(
                consumer_balance * random.uniform(0.000000001, 1)
            )
            ocean_contract.approve(
                get_address_of_type(config, "Router"),
                ss_OCEAN_init_liquidity,
                consumer_wallet,
            )

            # Random vesting amount capped to 10% of ss_OCEAN_init_liquidity
            ss_DT_vest_amt = floor(random.uniform(0.001, 0.1) * ss_OCEAN_init_liquidity)

            min_vesting_period = factory_router.get_min_vesting_period()

            ss_DT_vested_blocks = random.randint(
                min_vesting_period, min_vesting_period * 1000
            )

            ss_rate = web3.toWei(random.uniform(0.00001, 0.1), "ether")

            pool_data = PoolData(
                [
                    ss_rate,
                    ocean_contract.decimals(),
                    ss_DT_vest_amt,
                    ss_DT_vested_blocks,
                    ss_OCEAN_init_liquidity,
                ],
                [swap_fee, swap_market_fee],
                [
                    side_staking.address,
                    ocean_contract.address,
                    consumer_wallet.address,
                    consumer_wallet.address,
                    get_address_of_type(config, "OPFCommunityFeeCollector"),
                    get_address_of_type(config, "poolTemplate"),
                ],
            )

            tx = erc20_token.deploy_pool(pool_data, consumer_wallet)

            tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
            pool_event = factory_router.get_event_log(
                ERC721FactoryContract.EVENT_NEW_POOL,
                tx_receipt.blockNumber,
                web3.eth.block_number,
                None,
            )

            assert pool_event[0].event == "NewPool"
            bpool_address = pool_event[0].args.poolAddress
            bpool = BPool(web3, bpool_address)
            assert bpool.is_finalized() is True
            assert bpool.opc_fee() == 0
            assert bpool.get_swap_fee() == swap_fee
            assert bpool.community_fee(get_address_of_type(config, "Ocean")) == 0
            assert bpool.community_fee(erc20_token.address) == 0
            assert bpool.publish_market_fee(get_address_of_type(config, "Ocean")) == 0
            assert bpool.publish_market_fee(erc20_token.address) == 0

            assert (
                ocean_contract.balanceOf(consumer_wallet.address)
                + ss_OCEAN_init_liquidity
                == consumer_balance
            )

            assert approx_from_wei(
                cap - ss_OCEAN_init_liquidity * from_wei(ss_rate),
                erc20_token.balanceOf(side_staking.address),
            )

            assert ocean_contract.balanceOf(bpool.address) == ss_OCEAN_init_liquidity
            assert erc20_token.balanceOf(publisher_wallet.address) == 0

            publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
            publisher_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)

            # Large approvals for the rest of tests
            ocean_contract.approve(
                bpool_address, to_wei("1000000000000000"), publisher_wallet
            )
            erc20_token.approve(
                bpool_address, to_wei("1000000000000000"), publisher_wallet
            )

            swap_in_one_amount_in = get_random_max_token_amount_in(
                ocean_contract, bpool, publisher_wallet.address
            )
            tx = bpool.swap_exact_amount_in(
                [
                    ocean_contract.address,
                    erc20_address,
                    another_consumer_wallet.address,
                ],
                [
                    swap_in_one_amount_in,
                    1,
                    to_wei("1000000000"),
                    0,
                ],
                publisher_wallet,
            )

            tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

            assert (erc20_token.balanceOf(publisher_wallet.address) > 0) is True

            swap_fee_event = bpool.get_event_log(
                bpool.EVENT_LOG_SWAP,
                tx_receipt.blockNumber,
                web3.eth.block_number,
                None,
            )

            swap_event_args = swap_fee_event[0].args

            # Check swap balances
            assert (
                ocean_contract.balanceOf(publisher_wallet.address)
                + swap_event_args.tokenAmountIn
                == publisher_ocean_balance
            )
            assert (
                erc20_token.balanceOf(publisher_wallet.address)
                == publisher_dt_balance + swap_event_args.tokenAmountOut
            )

            # Tests publisher buys some DT - exactAmountOut
            publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
            publisher_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)
            dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)
            ocean_market_fee_balance = bpool.publish_market_fee(ocean_contract.address)

            swap_out_one_amount_out = get_random_max_token_amount_out(
                ocean_contract, erc20_token, bpool, publisher_wallet.address
            )
            swap_out_one_balance = ocean_contract.balanceOf(publisher_wallet.address)

            tx = bpool.swap_exact_amount_out(
                [
                    ocean_contract.address,
                    erc20_address,
                    another_consumer_wallet.address,
                ],
                [
                    swap_out_one_balance,  # max amount in
                    swap_out_one_amount_out,
                    to_wei("1000000"),
                    0,
                ],
                publisher_wallet,
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
                ocean_contract.balanceOf(publisher_wallet.address)
                + swap_event_args.tokenAmountIn
                == publisher_ocean_balance
            )
            assert (
                erc20_token.balanceOf(publisher_wallet.address)
                == publisher_dt_balance + swap_event_args.tokenAmountOut
            )

            swap_fees_event = bpool.get_event_log(
                "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
            )

            swap_fees_event_args = swap_fees_event[0].args

            assert swap_fees_event_args.oceanFeeAmount == 0
            assert (
                ocean_market_fee_balance + swap_fees_event_args.marketFeeAmount
                == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
            )
            assert dt_market_fee_balance == bpool.publish_market_fee(
                erc20_token.address
            )

            # Tests publisher swaps some DT back to Ocean with swapExactAmountIn, check swap custom fees
            assert bpool.is_finalized() is True

            erc20_token.approve(bpool_address, to_wei("1000"), publisher_wallet)
            publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
            dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

            assert bpool.community_fee(ocean_contract.address) == 0
            assert bpool.community_fee(erc20_address) == 0
            assert bpool.publish_market_fee(erc20_address) == 0

            swap_in_two_amount_in = get_random_max_token_amount_in(
                erc20_token, bpool, publisher_wallet.address
            )

            tx = bpool.swap_exact_amount_in(
                [
                    erc20_address,
                    ocean_contract.address,
                    another_consumer_wallet.address,
                ],
                [
                    swap_in_two_amount_in,
                    1,
                    to_wei("1000000000"),
                    0,
                ],
                publisher_wallet,
            )

            tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

            swap_fees_event = bpool.get_event_log(
                "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
            )

            swap_fees_event_args = swap_fees_event[0].args

            assert approx_from_wei(
                swap_market_fee * swap_in_two_amount_in / to_wei(1),
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
                erc20_token.balanceOf(publisher_wallet.address)
                + swap_event_args.tokenAmountIn
                == publisher_dt_balance
            )

            assert approx_from_wei(
                swap_event_args.tokenAmountIn / (to_wei(1) / swap_market_fee),
                swap_fees_event_args.marketFeeAmount,
            )

            assert approx_from_wei(
                swap_event_args.tokenAmountIn / (to_wei(1) / swap_fee),
                swap_fees_event_args.LPFeeAmount,
            )

            # Tests publisher swaps some DT back to Ocean with swapExactAmountOut, check swap custom fees

            erc20_token.approve(bpool_address, to_wei("1000"), publisher_wallet)
            publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
            publisher_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)
            dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

            assert bpool.community_fee(ocean_contract.address) == 0
            assert bpool.community_fee(erc20_address) == 0

            swap_out_two_amount_out = get_random_max_token_amount_out(
                erc20_token, ocean_contract, bpool, publisher_wallet.address
            )
            swap_out_two_balance = erc20_token.balanceOf(publisher_wallet.address)

            tx = bpool.swap_exact_amount_out(
                [
                    erc20_token.address,
                    ocean_contract.address,
                    another_consumer_wallet.address,
                ],
                [
                    swap_out_two_balance,
                    swap_out_two_amount_out,
                    to_wei("10000000"),
                    0,
                ],
                publisher_wallet,
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
                erc20_token.balanceOf(publisher_wallet.address)
                + swap_event_args.tokenAmountIn
                == publisher_dt_balance
            )
            assert (
                publisher_ocean_balance + swap_event_args.tokenAmountOut
                == ocean_contract.balanceOf(publisher_wallet.address)
            )

            assert approx_from_wei(
                swap_event_args.tokenAmountIn / (to_wei("1") / swap_market_fee),
                swap_fees_event_args.marketFeeAmount,
            )

            assert approx_from_wei(
                swap_event_args.tokenAmountIn / (to_wei("1") / swap_fee),
                swap_fees_event_args.LPFeeAmount,
            )
        except:

            error = traceback.format_exc()

            dt_balance = erc20_token.balanceOf(publisher_wallet.address)
            ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)

            params = f"""
            Final balances:
            datatoken: {dt_balance} {from_wei(dt_balance)}
            ocean: {ocean_balance} {from_wei(ocean_balance)}

            Values
            cap: {cap} {from_wei(cap)}
            swap_fee: {swap_fee} {from_wei(swap_fee)}
            swap_market_fee: {swap_market_fee} {from_wei(swap_market_fee)}
            ss_rate: {ss_rate}
            ss_DT_vest_amt: {ss_DT_vest_amt} {from_wei(ss_DT_vest_amt)}
            ss_DT_vested_blocks: {ss_DT_vested_blocks}
            ss_OCEAN_init_liquidity: {ss_OCEAN_init_liquidity} {from_wei(ss_OCEAN_init_liquidity)}
            swap_in_one_amount_in: {swap_in_one_amount_in} {from_wei(swap_in_one_amount_in)}
            swap_out_one_amount_out: {swap_out_one_amount_out} {from_wei(swap_out_one_amount_out)}
            swap_out_one_balance: {swap_out_one_balance} {from_wei(swap_out_one_balance)}
            swap_in_two_amount_in: {swap_in_two_amount_in} {from_wei(swap_in_two_amount_in)}
            swap_out_two_amount_out: {swap_out_two_amount_out} {from_wei(swap_out_two_amount_out)}
            swap_out_two_balance: {swap_out_two_balance} {from_wei(swap_out_two_balance)}
            """

            errors.append([error, params])

    # print errors
    for error in errors:
        print(error[0])
        print(error[1])
        print("\n")

    print(f"Number of errors: {len(errors)}")

    assert not errors
