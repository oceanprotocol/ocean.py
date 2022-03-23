#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from re import I
from eth_utils import from_wei
import pytest
from web3 import exceptions

from ocean_lib.models.bpool import BPool
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721NFT
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.web3_internal.constants import MAX_UINT256
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import (
    create_nft_erc20_with_pool,
    deploy_erc721_erc20,
    get_address_of_type,
    join_pool_one_side,
    swap_exact_amount_in_base_token,
    swap_exact_amount_in_datatoken,
    transfer_ocean_if_balance_lte,
    wallet_exit_pool,
)


@pytest.mark.unit
def test_side_staking(
    web3,
    config,
    publisher_wallet,
    consumer_wallet,
    another_consumer_wallet,
    factory_deployer_wallet,
    factory_router,
):
    lp_swap_fee = int(1e15)
    publish_market_swap_fee = int(1e15)
    initial_ocean_liquidity = to_wei("10")

    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))

    ocean_token = ERC20Token(web3, get_address_of_type(config, "Ocean"))

    # Deploy erc721 and erc20 data token
    erc721, erc20 = deploy_erc721_erc20(
        web3, config, consumer_wallet, consumer_wallet, to_wei("10000")
    )

    # Initial vesting should be 0 and last vested block two
    assert side_staking.get_vesting_amount_so_far(erc20.address) == 0
    assert side_staking.get_vesting_last_block(erc20.address) == 0
    assert side_staking.get_vesting_end_block(erc20.address) == 0
    assert side_staking.get_base_token_balance(erc20.address) == 0

    # Datatoken initial circulating supply should be 0
    assert side_staking.get_datatoken_circulating_supply(erc20.address) == 0

    # Transfer ocean if needed
    transfer_ocean_if_balance_lte(
        web3=web3,
        config=config,
        factory_deployer_wallet=factory_deployer_wallet,
        recipient=consumer_wallet.address,
        min_balance=0,
        amount_to_transfer=to_wei("20000"),
    )

    transfer_ocean_if_balance_lte(
        web3=web3,
        config=config,
        factory_deployer_wallet=factory_deployer_wallet,
        recipient=another_consumer_wallet.address,
        min_balance=to_wei("1000"),
        amount_to_transfer=to_wei("1000"),
    )

    ocean_token.approve(
        get_address_of_type(config, "Router"),
        to_wei("20000"),
        consumer_wallet,
    )

    tx = erc20.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=ocean_token.decimals(),
        vesting_amount=to_wei("0.5"),
        vesting_blocks=2500000,
        base_token_amount=initial_ocean_liquidity,
        lp_swap_fee_amount=lp_swap_fee,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        ss_contract=get_address_of_type(config, "Staking"),
        base_token_address=ocean_token.address,
        base_token_sender=consumer_wallet.address,
        publisher_address=consumer_wallet.address,
        publish_market_swap_fee_collector=get_address_of_type(
            config, "OPFCommunityFeeCollector"
        ),
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    pool_event = factory_router.get_event_log(
        ERC721FactoryContract.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert side_staking.get_base_token_address(erc20.address) == ocean_token.address
    assert side_staking.get_publisher_address(erc20.address) == consumer_wallet.address
    assert side_staking.get_vesting_amount(erc20.address) == to_wei("0.5")

    assert pool_event[0].event == "NewPool"
    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)

    # Side staking pool address should match the newly created pool
    assert side_staking.get_pool_address(erc20.address) == bpool_address

    assert (
        erc20.balanceOf(get_address_of_type(config, "Staking"))
        == MAX_UINT256 - initial_ocean_liquidity
    )
    assert bpool.opc_fee() == to_wei("0.001")
    assert bpool.get_swap_fee() == lp_swap_fee
    assert bpool.community_fee(ocean_token.address) == 0
    assert bpool.community_fee(erc20.address) == 0
    assert bpool.publish_market_fee(ocean_token.address) == 0
    assert bpool.publish_market_fee(erc20.address) == 0

    # Consumer fails to mints new erc20 tokens even if it's minter
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.mint(consumer_wallet.address, to_wei("1"), consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert"
    )

    # Another consumer buys some DT after burnIn period- exactAmountIn
    # Pool has initial ocean tokens at the beginning
    assert ocean_token.balanceOf(bpool_address) == initial_ocean_liquidity

    ocean_token.approve(bpool_address, to_wei("100"), another_consumer_wallet)

    # Transfer some ocean from consumer_wallet to another_consumer_wallet to continue testing
    ocean_token.transfer(another_consumer_wallet.address, to_wei("10"), consumer_wallet)

    bpool.swap_exact_amount_in(
        token_in=ocean_token.address,
        token_out=erc20.address,
        consume_market_swap_fee_address=publisher_wallet.address,
        token_amount_in=to_wei("1"),
        min_amount_out=to_wei("0"),
        max_price=to_wei("1000000"),
        consume_market_swap_fee_amount=0,
        from_wallet=another_consumer_wallet,
    )

    assert erc20.balanceOf(another_consumer_wallet.address) >= 0

    # Another consumer swaps some DT back to Ocean swapExactAmountIn
    initial_erc20_balance = erc20.balanceOf(another_consumer_wallet.address)
    initial_ocean_balance = ocean_token.balanceOf(another_consumer_wallet.address)
    erc20.approve(bpool_address, to_wei("10000"), another_consumer_wallet)

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.swap_exact_amount_in(
            token_in=erc20.address,
            token_out=ocean_token.address,
            consume_market_swap_fee_address=publisher_wallet.address,
            token_amount_in=to_wei("0.01"),
            min_amount_out=to_wei("0.001"),
            max_price=to_wei("100"),
            consume_market_swap_fee_amount=0,
            from_wallet=another_consumer_wallet,
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

    bpt_amount_out = to_wei("0.01")
    maxAmountsIn = [
        to_wei("50"),  # Amounts IN
        to_wei("50"),  # Amounts IN
    ]
    ocean_token.approve(bpool.address, to_wei("50"), another_consumer_wallet)

    erc20.approve(bpool.address, to_wei("50"), another_consumer_wallet)

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

    ocean_token.approve(bpool.address, to_wei(1), consumer_wallet)

    ocean_amount_in = to_wei("0.4")
    min_bp_out = to_wei("0.1")

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.join_swap_extern_amount_in(ocean_amount_in, min_bp_out, consumer_wallet)
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

    # Consumer removes liquidity with JoinPool, receiving both tokens
    initial_erc20_balance_consumer = erc20.balanceOf(consumer_wallet.address)
    initial_ocean_balance_consumer = ocean_token.balanceOf(consumer_wallet.address)
    initial_bpt_balance_consumer = bpool.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20.balanceOf(get_address_of_type(config, "Staking"))
    ss_contract_bpt_balance = bpool.balanceOf(get_address_of_type(config, "Staking"))

    # NO APPROVAL FOR BPT is required

    bpt_amount_in = to_wei("0.001")
    min_amount_out = [
        to_wei("0.00001"),  # Amounts IN
        to_wei("0.00001"),  # Amounts IN
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

    bpt_amount_in = to_wei("1")
    min_ocean_out = to_wei("0.000001")

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.exit_swap_pool_amount_in(bpt_amount_in, min_ocean_out, consumer_wallet)
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

    # Get vesting should be callable by anyone
    side_staking.get_vesting(erc20.address, another_consumer_wallet)

    # Only pool can call this function
    with pytest.raises(exceptions.ContractLogicError) as err:
        side_staking.can_stake(erc20.address, 10)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERR: Only pool can call this"
    )

    # Only pool can call this function
    with pytest.raises(exceptions.ContractLogicError) as err:
        side_staking.stake(erc20.address, 10, consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERR: Only pool can call this"
    )

    # Only pool can call this function
    with pytest.raises(exceptions.ContractLogicError) as err:
        side_staking.unstake(erc20.address, 10, 5, consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERR: Only pool can call this"
    )


@pytest.mark.unit
def test_side_staking_bot_consistency(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """
    In this test we try to make a profit in base_token by joining the pool and swapping in different orders. We check that it's not possible
    to make any profit an therefore steal from the pool.
    """
    # Test initial values and setups
    initial_pool_liquidity = to_wei("50")
    token_cap = to_wei("100")
    swap_market_fee = to_wei("0.0001")
    swap_fee = to_wei("0.0001")
    big_allowance = to_wei("100000000")

    ocean_token = ERC20Token(web3, get_address_of_type(config, "Ocean"))

    ocean_token.transfer(another_consumer_wallet.address, to_wei("50"), consumer_wallet)

    bpool, erc20_token, erc721_token, pool_token = create_nft_erc20_with_pool(
        web3,
        config,
        publisher_wallet,
        swap_fee,
        swap_market_fee,
        initial_pool_liquidity,
        token_cap,
    )

    ocean_token.approve(bpool.address, big_allowance, another_consumer_wallet)
    erc20_token.approve(bpool.address, big_allowance, another_consumer_wallet)

    # End test initial values and setups

    initial_ocean_user_balance = ocean_token.balanceOf(another_consumer_wallet.address)
    swap_exact_amount_in_base_token(
        bpool, erc20_token, ocean_token, another_consumer_wallet, to_wei("20")
    )
    join_pool_one_side(web3, bpool, ocean_token, another_consumer_wallet)
    wallet_exit_pool(web3, bpool, pool_token, another_consumer_wallet)
    swap_exact_amount_in_datatoken(
        bpool,
        erc20_token,
        ocean_token,
        another_consumer_wallet,
        erc20_token.balanceOf(another_consumer_wallet.address),
    )

    # Check that users hasn't made any profit
    assert pool_token.balanceOf(another_consumer_wallet.address) == 0
    assert erc20_token.balanceOf(another_consumer_wallet.address) == 0
    assert (
        ocean_token.balanceOf(another_consumer_wallet.address)
        <= initial_ocean_user_balance
    )

    # Test in a different order
    initial_ocean_user_balance = ocean_token.balanceOf(another_consumer_wallet.address)
    swap_exact_amount_in_base_token(
        bpool, erc20_token, ocean_token, another_consumer_wallet, to_wei("20")
    )
    join_pool_one_side(web3, bpool, ocean_token, another_consumer_wallet)
    swap_exact_amount_in_datatoken(
        bpool,
        erc20_token,
        ocean_token,
        another_consumer_wallet,
        erc20_token.balanceOf(another_consumer_wallet.address),
    )
    wallet_exit_pool(web3, bpool, pool_token, another_consumer_wallet)
    swap_exact_amount_in_datatoken(
        bpool,
        erc20_token,
        ocean_token,
        another_consumer_wallet,
        erc20_token.balanceOf(another_consumer_wallet.address),
    )

    # Check that users hasn't made any profit
    assert pool_token.balanceOf(another_consumer_wallet.address) == 0
    assert erc20_token.balanceOf(another_consumer_wallet.address) == 0
    assert (
        ocean_token.balanceOf(another_consumer_wallet.address)
        <= initial_ocean_user_balance
    )


def test_side_staking_constant_rate(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """
    In this test we test that the side staking bot keeps the same rate when the datatoken supply is less than the cap.
    """
    # Test initial values and setups
    initial_pool_liquidity = to_wei("1")
    token_cap = to_wei("5")
    swap_market_fee = to_wei("0.0001")
    swap_fee = to_wei("0.0001")
    big_allowance = to_wei("100000000")

    ocean_token = ERC20Token(web3, get_address_of_type(config, "Ocean"))

    ocean_token.transfer(another_consumer_wallet.address, to_wei("50"), consumer_wallet)

    bpool, erc20_token, erc721_token, pool_token = create_nft_erc20_with_pool(
        web3,
        config,
        publisher_wallet,
        swap_fee,
        swap_market_fee,
        initial_pool_liquidity,
        token_cap,
    )

    ocean_token.approve(bpool.address, big_allowance, another_consumer_wallet)
    erc20_token.approve(bpool.address, big_allowance, another_consumer_wallet)

    # End test initial values and setups

    initial_spot_price_basetoken_datatoken = bpool.get_spot_price(
        ocean_token.address, erc20_token.address, swap_market_fee
    )
    join_pool_one_side(web3, bpool, ocean_token, another_consumer_wallet, to_wei("0.5"))
    final_spot_price_basetoken_datatoken = bpool.get_spot_price(
        ocean_token.address, erc20_token.address, swap_market_fee
    )

    assert (
        final_spot_price_basetoken_datatoken != initial_spot_price_basetoken_datatoken
    )


def test_side_staking_over_datatoken_cap(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """
    In this test we test that the side staking bot works as espected when the datatoken supply is over the cap.
    """
    # Test initial values and setups
    initial_pool_liquidity = to_wei("1")
    token_cap = to_wei("5")
    swap_market_fee = to_wei("0.0001")
    swap_fee = to_wei("0.0001")
    big_allowance = to_wei("100000000")

    ocean_token = ERC20Token(web3, get_address_of_type(config, "Ocean"))

    ocean_token.transfer(another_consumer_wallet.address, to_wei("50"), consumer_wallet)

    bpool, erc20_token, erc721_token, pool_token = create_nft_erc20_with_pool(
        web3,
        config,
        publisher_wallet,
        swap_fee,
        swap_market_fee,
        initial_pool_liquidity,
        token_cap,
    )

    ocean_token.approve(bpool.address, big_allowance, another_consumer_wallet)
    erc20_token.approve(bpool.address, big_allowance, another_consumer_wallet)

    # End test initial values and setups

    erc20_token_total_supply = erc20_token.get_total_supply()
    assert erc20_token_total_supply == token_cap

    # Fill the pool until the cap is reached
    previous_pool_datatoken_balance = 0
    while previous_pool_datatoken_balance != erc20_token.balanceOf(bpool.address):
        previous_pool_datatoken_balance = erc20_token.balanceOf(bpool.address)
        join_pool_one_side(
            web3, bpool, ocean_token, another_consumer_wallet, to_wei("0.5")
        )
    join_pool_one_side(web3, bpool, ocean_token, another_consumer_wallet, to_wei("0.5"))

    assert erc20_token.balanceOf(bpool.address) > to_wei("4")
    assert erc20_token.balanceOf(bpool.address) < to_wei("5")

    # From this point the test that the SS bot doesn't add more datatokens
    max_erc20_pool_balance = erc20_token.balanceOf(bpool.address)
    join_pool_one_side(web3, bpool, ocean_token, another_consumer_wallet, to_wei("0.5"))
    assert erc20_token.balanceOf(bpool.address) == max_erc20_pool_balance
