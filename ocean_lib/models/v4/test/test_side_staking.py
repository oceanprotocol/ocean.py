#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.v4.bpool import BPool
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.models_structures import PoolData
from tests.resources.helper_functions import (
    get_address_of_type,
    deploy_erc721_erc20,
)


def test_side_staking(
    web3,
    config,
    publisher_wallet,
    consumer_wallet,
    another_consumer_wallet,
    factory_deployer_wallet,
    factory_router,
):
    swap_fee = int(1e15)
    swap_market_fee = int(1e15)
    vested_blocks = 2500000
    initial_ocean_liquidity = web3.toWei("10", "ether")

    ocean_token = ERC20Token(web3, get_address_of_type(config, "Ocean"))

    # Deploy erc721 and erc20 data token
    erc721, erc20 = deploy_erc721_erc20(
        web3, config, consumer_wallet, consumer_wallet, web3.toWei("10000", "ether")
    )

    if ocean_token.balanceOf(consumer_wallet.address) == 0:
        ocean_token.transfer(
            consumer_wallet.address,
            web3.toWei("20000", "ether"),
            factory_deployer_wallet,
        )
    if ocean_token.balanceOf(another_consumer_wallet.address) == 0:
        ocean_token.transfer(
            another_consumer_wallet.address,
            web3.toWei("100", "ether"),
            factory_deployer_wallet,
        )

    ocean_token.approve(
        get_address_of_type(config, "Router"),
        web3.toWei("20000", "ether"),
        consumer_wallet,
    )

    pool_data = PoolData(
        ss_params=[
            web3.toWei(1, "ether"),
            ocean_token.decimals(),
            web3.toWei("0.5", "ether"),
            vested_blocks,
            initial_ocean_liquidity,
        ],
        swap_fees=[swap_fee, swap_market_fee],
        addresses=[
            get_address_of_type(config, "Staking"),
            ocean_token.address,
            consumer_wallet.address,
            consumer_wallet.address,
            get_address_of_type(config, "OPFCommunityFeeCollector"),
            get_address_of_type(config, "poolTemplate"),
        ],
    )

    tx = erc20.deploy_pool(pool_data, consumer_wallet)

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

    assert erc20.balanceOf(get_address_of_type(config, "Staking")) == web3.toWei(
        "9990", "ether"
    )

    # Consumer fails to mints new erc20 tokens even if it's minter
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.mint(consumer_wallet.address, web3.toWei("1", "ether"), consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert DataTokenTemplate: cap exceeded"
    )

    # Another consumer buys some DT after burnIn period- exactAmountIn
    # Pool has initial ocean tokens at the beginning
    assert ocean_token.balanceOf(bpool_address) == initial_ocean_liquidity

    ocean_token.approve(
        bpool_address, web3.toWei("10000", "ether"), another_consumer_wallet
    )

    bpool.swap_exact_amount_in(
        ocean_token.address,
        web3.toWei("1", "ether"),
        erc20.address,
        web3.toWei("0", "ether"),
        web3.toWei("1000000", "ether"),
        another_consumer_wallet,
    )

    assert erc20.balanceOf(another_consumer_wallet.address) >= 0

    # Another consumer swaps some DT back to Ocean swapExactAmountIn
    initial_erc20_balance = erc20.balanceOf(another_consumer_wallet.address)
    initial_ocean_balance = ocean_token.balanceOf(another_consumer_wallet.address)
    erc20.approve(bpool_address, web3.toWei("10000", "ether"), another_consumer_wallet)

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.swap_exact_amount_in(
            erc20.address,
            web3.toWei("0.01", "ether"),
            ocean_token.address,
            web3.toWei("0.001", "ether"),
            web3.toWei("100", "ether"),
            another_consumer_wallet,
        )
    )

    registered_event = bpool.get_event_log(
        event_name=BPool.EVENT_LOG_SWAP,
        from_block=receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert registered_event[0].event == BPool.EVENT_LOG_SWAP

    assert erc20.balanceOf(another_consumer_wallet.address) < initial_erc20_balance
    assert (
        ocean_token.balanceOf(another_consumer_wallet.address) > initial_ocean_balance
    )

    #  Another consumer adds more liquidity with joinPool() (adding both tokens)

    initial_erc20_balance = erc20.balanceOf(another_consumer_wallet.address)
    initial_ocean_balance = ocean_token.balanceOf(another_consumer_wallet.address)
    initial_bpt_balance = bpool.balanceOf(another_consumer_wallet.address)
    ss_contract_dt_balance = erc20.balanceOf(get_address_of_type(config, "Staking"))
    ss_contract_bpt_balance = bpool.balanceOf(get_address_of_type(config, "Staking"))

    bpt_amount_out = web3.toWei("0.01", "ether")
    maxAmountsIn = [
        web3.toWei("50", "ether"),  # Amounts IN
        web3.toWei("50", "ether"),  # Amounts IN
    ]
    ocean_token.approve(
        bpool.address, web3.toWei("50", "ether"), another_consumer_wallet
    )

    erc20.approve(bpool.address, web3.toWei("50", "ether"), another_consumer_wallet)

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.join_pool(bpt_amount_out, maxAmountsIn, another_consumer_wallet)
    )

    registered_event = bpool.get_event_log(
        event_name=BPool.EVENT_LOG_JOIN,
        from_block=receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    assert registered_event[0].event == BPool.EVENT_LOG_JOIN

    assert registered_event[0].args.tokenIn == erc20.address
    assert registered_event[1].args.tokenIn == ocean_token.address

    # Check balances
    assert (
        registered_event[0].args.tokenAmountIn
        + erc20.balanceOf(another_consumer_wallet.address)
    ) == initial_erc20_balance
    assert (
        registered_event[1].args.tokenAmountIn
        + ocean_token.balanceOf(another_consumer_wallet.address)
    ) == initial_ocean_balance
    assert (initial_bpt_balance + bpt_amount_out) == bpool.balanceOf(
        another_consumer_wallet.address
    )

    # Check that the ssContract BPT and DT balance didn't change.
    assert ss_contract_dt_balance == erc20.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # Consumer adds more liquidity with joinswapExternAmountIn

    initial_erc20_balance_consumer = erc20.balanceOf(consumer_wallet.address)

    ocean_token.approve(bpool.address, web3.toWei("1", "ether"), consumer_wallet)

    ocean_amount_in = web3.toWei("0.4", "ether")
    min_bp_out = web3.toWei("0.1", "ether")

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.join_swap_extern_amount_in(
            ocean_token.address, ocean_amount_in, min_bp_out, consumer_wallet
        )
    )

    registered_event = bpool.get_event_log(
        event_name=BPool.EVENT_LOG_JOIN,
        from_block=receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert registered_event[0].event == BPool.EVENT_LOG_JOIN
    assert registered_event[0].args.tokenIn == ocean_token.address
    assert registered_event[0].args.tokenAmountIn == ocean_amount_in
    assert registered_event[1].args.tokenIn == erc20.address

    side_staking_amount_in = ss_contract_dt_balance - erc20.balanceOf(
        get_address_of_type(config, "Staking")
    )

    assert registered_event[1].args.tokenAmountIn == side_staking_amount_in

    # We check ssContract actually moved DT and got back BPT
    assert ss_contract_dt_balance - registered_event[
        1
    ].args.tokenAmountIn == erc20.balanceOf(get_address_of_type(config, "Staking"))

    registered_event2 = bpool.get_event_log(
        event_name=BPool.EVENT_LOG_BPT,
        from_block=receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert registered_event2[
        0
    ].args.bptAmount + ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # No dt token where taken from user3

    assert erc20.balanceOf(consumer_wallet.address) == initial_erc20_balance_consumer

    # Consumer adds more liquidity with joinswapPoolAmountOut (only OCEAN)
    initial_erc20_balance_consumer = erc20.balanceOf(consumer_wallet.address)
    initial_ocean_balance_consumer = ocean_token.balanceOf(consumer_wallet.address)
    initial_bpt_balance_consumer = bpool.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20.balanceOf(get_address_of_type(config, "Staking"))
    ss_contract_bpt_balance = bpool.balanceOf(get_address_of_type(config, "Staking"))

    ocean_token.approve(bpool.address, web3.toWei("1", "ether"), consumer_wallet)
    bp_amt_out = web3.toWei("0.01", "ether")
    max_ocean_in = web3.toWei("100", "ether")

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.join_swap_pool_amount_out(
            ocean_token.address, bp_amt_out, max_ocean_in, consumer_wallet
        )
    )

    registered_event = bpool.get_event_log(
        event_name=BPool.EVENT_LOG_JOIN,
        from_block=receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    assert registered_event[0].args.tokenIn == ocean_token.address
    assert registered_event[1].args.tokenIn == erc20.address

    # Check balances (ocean and bpt)
    assert (
        registered_event[0].args.tokenAmountIn
        + ocean_token.balanceOf(consumer_wallet.address)
        == initial_ocean_balance_consumer
    )
    assert bp_amt_out + initial_bpt_balance_consumer == bpool.balanceOf(
        consumer_wallet.address
    )

    # We check ssContract received the same amount of BPT
    assert ss_contract_bpt_balance + bp_amt_out == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # And also that DT balance lowered in the ssContract
    assert ss_contract_dt_balance - registered_event[
        1
    ].args.tokenAmountIn == erc20.balanceOf(get_address_of_type(config, "Staking"))

    # No token where taken from user3.
    assert erc20.balanceOf(consumer_wallet.address) == initial_erc20_balance_consumer

    # Consumer removes liquidity with JoinPool, receiving both tokens
    initial_erc20_balance_consumer = erc20.balanceOf(consumer_wallet.address)
    initial_ocean_balance_consumer = ocean_token.balanceOf(consumer_wallet.address)
    initial_bpt_balance_consumer = bpool.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20.balanceOf(get_address_of_type(config, "Staking"))
    ss_contract_bpt_balance = bpool.balanceOf(get_address_of_type(config, "Staking"))

    # NO APPROVAL FOR BPT is required

    bpt_amount_in = web3.toWei("0.001", "ether")
    min_amount_out = [
        web3.toWei("0.00001", "ether"),  # Amounts IN
        web3.toWei("0.00001", "ether"),  # Amounts IN
    ]

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.exit_pool(bpt_amount_in, min_amount_out, consumer_wallet)
    )

    registered_event = bpool.get_event_log(
        event_name=BPool.EVENT_LOG_EXIT,
        from_block=receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    # Check all balances (DT,OCEAN,BPT)
    assert registered_event[0].args.tokenOut == erc20.address
    assert registered_event[1].args.tokenOut == ocean_token.address

    assert registered_event[
        0
    ].args.tokenAmountOut + initial_erc20_balance_consumer == erc20.balanceOf(
        consumer_wallet.address
    )
    assert registered_event[
        1
    ].args.tokenAmountOut + initial_ocean_balance_consumer == ocean_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        bpool.balanceOf(consumer_wallet.address) + bpt_amount_in
        == initial_bpt_balance_consumer
    )

    # Check the ssContract BPT and DT balance didn't change.
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # Consumer removes liquidity with exitswapPoolAmountIn, receiving only OCEAN tokens

    initial_erc20_balance_consumer = erc20.balanceOf(consumer_wallet.address)
    initial_ocean_balance_consumer = ocean_token.balanceOf(consumer_wallet.address)
    initial_bpt_balance_consumer = bpool.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20.balanceOf(get_address_of_type(config, "Staking"))
    ss_contract_bpt_balance = bpool.balanceOf(get_address_of_type(config, "Staking"))

    bpt_amount_in = web3.toWei("1", "ether")
    min_ocean_out = web3.toWei("0.000001", "ether")

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.exit_swap_pool_amount_in(
            ocean_token.address, bpt_amount_in, min_ocean_out, consumer_wallet
        )
    )

    assert erc20.balanceOf(consumer_wallet.address) == initial_erc20_balance_consumer

    registered_event = bpool.get_event_log(
        event_name=BPool.EVENT_LOG_EXIT,
        from_block=receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert registered_event[0].args.caller == consumer_wallet.address
    assert registered_event[0].args.tokenOut == ocean_token.address
    assert registered_event[1].args.tokenOut == erc20.address

    assert registered_event[
        0
    ].args.tokenAmountOut + initial_ocean_balance_consumer == ocean_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        initial_bpt_balance_consumer
        == bpool.balanceOf(consumer_wallet.address) + bpt_amount_in
    )
    assert (
        ss_contract_bpt_balance
        == bpool.balanceOf(get_address_of_type(config, "Staking")) + bpt_amount_in
    )
    assert ss_contract_dt_balance + registered_event[
        1
    ].args.tokenAmountOut == erc20.balanceOf(get_address_of_type(config, "Staking"))

    # Consumer removes liquidity with exitswapPoolAmountIn, receiving only DT tokens

    initial_erc20_balance_consumer = erc20.balanceOf(consumer_wallet.address)
    initial_ocean_balance_consumer = ocean_token.balanceOf(consumer_wallet.address)
    initial_bpt_balance_consumer = bpool.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20.balanceOf(get_address_of_type(config, "Staking"))
    ss_contract_bpt_balance = bpool.balanceOf(get_address_of_type(config, "Staking"))

    max_btp_in = web3.toWei("0.01", "ether")
    exact_ocean_out = web3.toWei("1", "ether")

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.exit_swap_extern_amount_out(
            ocean_token.address, max_btp_in, exact_ocean_out, consumer_wallet
        )
    )

    registered_event = bpool.get_event_log(
        event_name=BPool.EVENT_LOG_BPT,
        from_block=receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert initial_erc20_balance_consumer == erc20.balanceOf(consumer_wallet.address)
    assert (
        bpool.balanceOf(consumer_wallet.address)
        == initial_bpt_balance_consumer - registered_event[0].args.bptAmount
    )

    # Check exit event
    exit_event = bpool.get_event_log(
        event_name=BPool.EVENT_LOG_EXIT,
        from_block=receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    # We check event arguments
    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == ocean_token.address
    assert exit_event[1].args.tokenOut == erc20.address

    assert exit_event[
        0
    ].args.tokenAmountOut + initial_ocean_balance_consumer == ocean_token.balanceOf(
        consumer_wallet.address
    )

    # Now we check the ssContract BPT balance
    assert ss_contract_bpt_balance - registered_event[
        0
    ].args.bptAmount == bpool.balanceOf(get_address_of_type(config, "Staking"))
    # And that we got back some dt when redeeeming BPT
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20.balanceOf(get_address_of_type(config, "Staking"))
