#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.bpool import BPool
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.web3_internal.currency import MAX_WEI, to_wei
from tests.resources.helper_functions import (
    create_nft_erc20_with_pool,
    get_address_of_type,
    join_pool_one_side,
    swap_exact_amount_in_base_token,
    swap_exact_amount_in_datatoken,
    transfer_base_token_if_balance_lte,
    wallet_exit_pool_one_side,
)


@pytest.mark.unit
def test_side_staking(
    web3,
    config,
    ocean_token,
    publisher_wallet,
    another_consumer_wallet,
    factory_deployer_wallet,
    factory_router,
    data_nft,
    datatoken,
):
    lp_swap_fee = int(1e15)
    publish_market_swap_fee = int(1e15)
    initial_ocean_liquidity = to_wei("10")

    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))

    assert side_staking.get_base_token_balance(datatoken.address) == 0

    # Datatoken initial circulating supply should be 0
    assert side_staking.get_datatoken_circulating_supply(datatoken.address) == 0

    # Transfer ocean if needed
    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=ocean_token.address,
        from_wallet=factory_deployer_wallet,
        recipient=publisher_wallet.address,
        min_balance=0,
        amount_to_transfer=to_wei("20000"),
    )

    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=ocean_token.address,
        from_wallet=factory_deployer_wallet,
        recipient=another_consumer_wallet.address,
        min_balance=to_wei("1000"),
        amount_to_transfer=to_wei("1000"),
    )

    ocean_token.approve(
        get_address_of_type(config, "Router"),
        to_wei("20000"),
        publisher_wallet,
    )

    tx = datatoken.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=ocean_token.decimals(),
        base_token_amount=initial_ocean_liquidity,
        lp_swap_fee_amount=lp_swap_fee,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        ss_contract=get_address_of_type(config, "Staking"),
        base_token_address=ocean_token.address,
        base_token_sender=publisher_wallet.address,
        publisher_address=publisher_wallet.address,
        publish_market_swap_fee_collector=get_address_of_type(
            config, "OPFCommunityFeeCollector"
        ),
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    pool_event = factory_router.get_event_log(
        DataNFTFactoryContract.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert side_staking.get_base_token_address(datatoken.address) == ocean_token.address
    assert (
        side_staking.get_publisher_address(datatoken.address)
        == publisher_wallet.address
    )

    assert pool_event[0].event == "NewPool"
    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)

    # Side staking pool address should match the newly created pool
    assert side_staking.get_pool_address(datatoken.address) == bpool_address

    # Publisher fails to mints new datatoken tokens even if it's minter
    with pytest.raises(exceptions.ContractLogicError) as err:
        datatoken.mint(publisher_wallet.address, to_wei("1"), publisher_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert"
    )

    # Another consumer buys some DT after burnIn period- exactAmountIn
    # Pool has initial ocean tokens at the beginning
    assert ocean_token.balanceOf(bpool_address) == initial_ocean_liquidity

    ocean_token.approve(bpool_address, to_wei("100"), another_consumer_wallet)

    # Transfer some ocean from publisher_wallet to another_consumer_wallet to continue testing
    ocean_token.transfer(
        another_consumer_wallet.address, to_wei("10"), publisher_wallet
    )

    bpool.swap_exact_amount_in(
        token_in=ocean_token.address,
        token_out=datatoken.address,
        consume_market_swap_fee_address=publisher_wallet.address,
        token_amount_in=to_wei("1"),
        min_amount_out=to_wei("0"),
        max_price=to_wei("1000000"),
        consume_market_swap_fee_amount=0,
        from_wallet=another_consumer_wallet,
    )

    assert datatoken.balanceOf(another_consumer_wallet.address) >= 0

    # Another consumer swaps some DT back to Ocean swapExactAmountIn
    initial_datatoken_balance = datatoken.balanceOf(another_consumer_wallet.address)
    initial_ocean_balance = ocean_token.balanceOf(another_consumer_wallet.address)
    datatoken.approve(bpool_address, to_wei("10000"), another_consumer_wallet)

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.swap_exact_amount_in(
            token_in=datatoken.address,
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

    assert (
        datatoken.balanceOf(another_consumer_wallet.address) < initial_datatoken_balance
    )
    assert (
        ocean_token.balanceOf(another_consumer_wallet.address) > initial_ocean_balance
    )

    # Publisher adds more liquidity with joinswapExternAmountIn
    ss_contract_dt_balance = datatoken.balanceOf(get_address_of_type(config, "Staking"))
    ss_contract_bpt_balance = bpool.balanceOf(get_address_of_type(config, "Staking"))

    initial_datatoken_balance_publisher = datatoken.balanceOf(publisher_wallet.address)

    ocean_token.approve(bpool.address, to_wei(1), publisher_wallet)

    ocean_amount_in = to_wei("0.4")
    min_bp_out = to_wei("0.1")

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.join_swap_extern_amount_in(ocean_amount_in, min_bp_out, publisher_wallet)
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
    assert registered_event[1].args.tokenIn == datatoken.address

    side_staking_amount_in = ss_contract_dt_balance - datatoken.balanceOf(
        get_address_of_type(config, "Staking")
    )

    assert registered_event[1].args.tokenAmountIn == side_staking_amount_in

    # We check ssContract actually moved DT and got back BPT
    assert ss_contract_dt_balance - registered_event[
        1
    ].args.tokenAmountIn == datatoken.balanceOf(get_address_of_type(config, "Staking"))

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
    assert (
        datatoken.balanceOf(publisher_wallet.address)
        == initial_datatoken_balance_publisher
    )

    # Publisher removes liquidity with exitswapPoolAmountIn, receiving only OCEAN tokens

    initial_datatoken_balance_publisher = datatoken.balanceOf(publisher_wallet.address)
    initial_ocean_balance_publisher = ocean_token.balanceOf(publisher_wallet.address)
    initial_bpt_balance_publisher = bpool.balanceOf(publisher_wallet.address)
    ss_contract_dt_balance = datatoken.balanceOf(get_address_of_type(config, "Staking"))
    ss_contract_bpt_balance = bpool.balanceOf(get_address_of_type(config, "Staking"))

    bpt_amount_in = to_wei("1")
    min_ocean_out = to_wei("0.000001")

    receipt = web3.eth.wait_for_transaction_receipt(
        bpool.exit_swap_pool_amount_in(bpt_amount_in, min_ocean_out, publisher_wallet)
    )

    assert (
        datatoken.balanceOf(publisher_wallet.address)
        == initial_datatoken_balance_publisher
    )

    registered_event = bpool.get_event_log(
        event_name=BPool.EVENT_LOG_EXIT,
        from_block=receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert registered_event[0].args.caller == publisher_wallet.address
    assert registered_event[0].args.tokenOut == ocean_token.address
    assert registered_event[1].args.tokenOut == datatoken.address

    assert registered_event[
        0
    ].args.tokenAmountOut + initial_ocean_balance_publisher == ocean_token.balanceOf(
        publisher_wallet.address
    )
    assert (
        initial_bpt_balance_publisher
        == bpool.balanceOf(publisher_wallet.address) + bpt_amount_in
    )
    assert (
        ss_contract_bpt_balance
        == bpool.balanceOf(get_address_of_type(config, "Staking")) + bpt_amount_in
    )
    assert ss_contract_dt_balance + registered_event[
        1
    ].args.tokenAmountOut == datatoken.balanceOf(get_address_of_type(config, "Staking"))


@pytest.mark.unit
def test_side_staking_steal(
    web3,
    config,
    publisher_wallet,
    another_consumer_wallet,
    datatoken,
):
    """
    In this test we try to steal base token from the pool
    """
    # Test initial values and setups
    initial_pool_liquidity_eth = 200000
    join_pool_step_eth = 20000
    datatoken_buy_amount_basetoken_eth = 5000

    initial_pool_liquidity = to_wei(initial_pool_liquidity_eth)
    swap_market_fee = to_wei("0.0001")
    swap_fee = to_wei("0.0001")
    big_allowance = MAX_WEI

    datatoken.mint(publisher_wallet.address, MAX_WEI, publisher_wallet)

    # We use an erc20 as ocean to have unlimited balance
    ocean_token = datatoken

    bpool, datatoken2, _, pool_token = create_nft_erc20_with_pool(
        web3,
        config,
        publisher_wallet,
        ocean_token,
        swap_fee,
        swap_market_fee,
        initial_pool_liquidity,
    )

    ocean_token.approve(bpool.address, big_allowance, another_consumer_wallet)
    datatoken2.approve(bpool.address, big_allowance, another_consumer_wallet)

    datatoken.transfer(
        another_consumer_wallet.address,
        datatoken.balanceOf(publisher_wallet.address),
        publisher_wallet,
    )

    # End test initial values and setups

    initial_ocean_user_balance = ocean_token.balanceOf(another_consumer_wallet.address)

    for _ in range(10):
        swap_exact_amount_in_base_token(
            bpool,
            datatoken2,
            ocean_token,
            another_consumer_wallet,
            to_wei(datatoken_buy_amount_basetoken_eth),
        )

    times = 2
    amounts_out = []
    for _ in range(times):
        join_pool_one_side(
            web3,
            bpool,
            ocean_token,
            another_consumer_wallet,
            to_wei(join_pool_step_eth),
        )
        amounts_out.append(
            bpool.get_amount_out_exact_in(
                datatoken2.address,
                ocean_token.address,
                datatoken2.balanceOf(another_consumer_wallet.address),
                swap_market_fee,
            )[0]
        )

    swap_exact_amount_in_datatoken(
        bpool,
        datatoken2,
        ocean_token,
        another_consumer_wallet,
        datatoken2.balanceOf(another_consumer_wallet.address),
    )

    while pool_token.balanceOf(another_consumer_wallet.address) > to_wei("50"):
        wallet_exit_pool_one_side(
            web3,
            bpool,
            ocean_token,
            pool_token,
            another_consumer_wallet,
            pool_token.balanceOf(another_consumer_wallet.address) // 5,
        )

    wallet_exit_pool_one_side(
        web3, bpool, ocean_token, pool_token, another_consumer_wallet
    )

    # Check that users hasn't made any profit
    assert datatoken2.balanceOf(another_consumer_wallet.address) == 0

    # Check that the the attacker is loosing money
    assert (
        ocean_token.balanceOf(another_consumer_wallet.address)
        < initial_ocean_user_balance
    )


def test_side_staking_constant_rate(
    web3,
    config,
    ocean_token,
    publisher_wallet,
    consumer_wallet,
    another_consumer_wallet,
):
    """
    In this test we test that the side staking bot keeps the same rate joining the pool one side
    """
    # Test initial values and setups
    initial_pool_liquidity = to_wei("1")
    swap_market_fee = to_wei("0.0001")
    swap_fee = to_wei("0.0001")
    big_allowance = to_wei("100000000")

    ocean_token.transfer(another_consumer_wallet.address, to_wei("50"), consumer_wallet)

    bpool, datatoken, _, _ = create_nft_erc20_with_pool(
        web3,
        config,
        publisher_wallet,
        ocean_token,
        swap_fee,
        swap_market_fee,
        initial_pool_liquidity,
    )

    ocean_token.approve(bpool.address, big_allowance, another_consumer_wallet)
    datatoken.approve(bpool.address, big_allowance, another_consumer_wallet)

    # End test initial values and setups
    initial_spot_price_basetoken_datatoken = bpool.get_spot_price(
        ocean_token.address, datatoken.address, swap_market_fee
    )
    # join the pool max ratio
    join_pool_one_side(web3, bpool, ocean_token, another_consumer_wallet)
    final_spot_price_basetoken_datatoken = bpool.get_spot_price(
        ocean_token.address, datatoken.address, swap_market_fee
    )

    # We check that the spot price is constant with a precision of 10^-10
    assert int(final_spot_price_basetoken_datatoken / 10**8) == int(
        initial_spot_price_basetoken_datatoken / 10**8
    )
