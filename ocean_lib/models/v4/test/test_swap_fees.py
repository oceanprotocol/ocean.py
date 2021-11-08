#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.v4.bpool import BPool
from ocean_lib.models.v4.dispenser import DispenserV4
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.models_structures import ErcCreateData, PoolData
from ocean_lib.models.v4.side_staking import SideStaking
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import get_address_of_type


def deploy_erc721_token(config, web3, factory_deployer_wallet, manager_wallet):
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    tx = erc721_factory.deploy_erc721_contract(
        "NFT",
        "SYMBOL",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        factory_deployer_wallet,
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)
    event = erc721_factory.get_event_log(
        erc721_factory.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    token_address = event[0].args.newTokenAddress
    erc721_token = ERC721Token(web3, token_address)

    erc721_token.add_to_725_store_list(manager_wallet.address, factory_deployer_wallet)
    erc721_token.add_to_create_erc20_list(
        manager_wallet.address, factory_deployer_wallet
    )
    erc721_token.add_to_metadata_list(manager_wallet.address, factory_deployer_wallet)
    return erc721_token


def test_deploy_erc721_and_manage(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    another_consumer_wallet,
):
    """
    Owner deploys a new ERC721 contract
    """
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    tx = erc721_factory.deploy_erc721_contract(
        "NFT",
        "SYMBOL",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        factory_deployer_wallet,
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)

    event = erc721_factory.get_event_log(
        erc721_factory.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert event is not None

    token_address = event[0].args.newTokenAddress
    erc721_token = ERC721Token(web3, token_address)

    assert erc721_token.balance_of(factory_deployer_wallet.address) == 1

    erc721_token.add_manager(another_consumer_wallet.address, factory_deployer_wallet)
    erc721_token.add_to_725_store_list(consumer_wallet.address, factory_deployer_wallet)
    erc721_token.add_to_create_erc20_list(
        consumer_wallet.address, factory_deployer_wallet
    )
    erc721_token.add_to_metadata_list(consumer_wallet.address, factory_deployer_wallet)

    permissions = erc721_token.get_permissions(consumer_wallet.address)

    assert permissions[1] == True
    assert permissions[2] == True
    assert permissions[3] == True


def test_pool_ocean(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    publisher_wallet,
    factory_router,
):
    """Tests pool with ocean token and market fee 0.1%"""
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
    erc721_token = deploy_erc721_token(
        config, web3, factory_deployer_wallet, consumer_wallet
    )

    # * Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = web3.toWei(100000, "ether")
    tx = erc721_token.create_erc20(
        ErcCreateData(
            1,
            ["ERC20DT1", "ERC20DT1Symbol"],
            [
                consumer_wallet.address,
                factory_deployer_wallet.address,
                consumer_wallet.address,
                "0x0000000000000000000000000000000000000000",
            ],
            [cap, 0],
            [],
        ),
        consumer_wallet,
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)
    event = erc721_factory.get_event_log(
        erc721_token.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    erc20_address = event[0].args.newTokenAddress
    erc20_token = ERC20Token(web3, erc20_address)

    assert erc20_token.get_permissions(consumer_wallet.address)[0] == True

    swap_fee = web3.toWei(0.001, "ether")
    swap_ocean_fee = web3.toWei(0.001, "ether")
    swap_market_fee = web3.toWei(0.001, "ether")

    # * Tests consumer calls deployPool(), we then check ocean and market fee"

    initial_ocean_liq = web3.toWei(10, "ether")
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(
        get_address_of_type(config, "Router"),
        web3.toWei(10, "ether"),
        consumer_wallet,
    )

    pool_data = PoolData(
        [
            web3.toWei(1, "ether"),
            ocean_contract.decimals(),
            initial_ocean_liq,
            2500000,
            initial_ocean_liq,
        ],
        [
            web3.toWei(0.001, "ether"),
            web3.toWei(0.001, "ether"),
        ],
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
    assert bpool.is_finalized() == True
    assert bpool.opf_fee() == 0
    assert bpool.get_swap_fee() == web3.toWei(0.001, "ether")
    assert bpool.community_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.market_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == web3.toWei(99990, "ether")

    assert bpool.calc_pool_in_single_out(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_pool_in_single_out(
        get_address_of_type(config, "Ocean"), web3.toWei(1, "ether")
    )
    assert bpool.calc_pool_out_single_in(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_pool_out_single_in(
        get_address_of_type(config, "Ocean"), web3.toWei(1, "ether")
    )
    assert bpool.calc_single_in_pool_out(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_single_in_pool_out(
        get_address_of_type(config, "Ocean"), web3.toWei(1, "ether")
    )
    assert bpool.calc_single_out_pool_in(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_single_out_pool_in(
        get_address_of_type(config, "Ocean"), web3.toWei(1, "ether")
    )
    # * Tests publisher buys some DT - exactAmountIn

    assert ocean_contract.balanceOf(bpool.address) == web3.toWei(10, "ether")
    ocean_contract.approve(bpool_address, web3.toWei(10, "ether"), publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)

    tx = bpool.swap_exact_amount_in(
        ocean_contract.address,
        web3.toWei(0.1, "ether"),
        erc20_address,
        web3.toWei(0.0001, "ether"),
        web3.toWei(100, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert (erc20_token.balanceOf(publisher_wallet.address) > 0) == True

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

    # * Tests publisher buys some DT - exactAmountOut
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)
    ocean_market_fee_balance = bpool.market_fee(ocean_contract.address)

    tx = bpool.swap_exact_amount_out(
        ocean_contract.address,
        web3.toWei(10, "ether"),
        erc20_address,
        web3.toWei(1, "ether"),
        web3.toWei(100, "ether"),
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
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert swap_fees_event_args.oceanFeeAmount == 0
    assert (
        ocean_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )
    assert dt_market_fee_balance == bpool.market_fee(erc20_token.address)

    # * Tests publisher swaps some DT back to Ocean with swapExactAmountIn, check swap custom fees
    assert bpool.is_finalized() is True

    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)
    ocean_market_fee_balance = bpool.market_fee(ocean_contract.address)

    assert bpool.community_fee(ocean_contract.address) == 0
    assert bpool.community_fee(erc20_address) == 0
    assert bpool.market_fee(erc20_address) == 0

    tx = bpool.swap_exact_amount_in(
        erc20_address,
        web3.toWei(0.1, "ether"),
        ocean_contract.address,
        web3.toWei(0.0001, "ether"),
        web3.toWei(100, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert web3.toWei("0.0001", "ether") == swap_fees_event_args.marketFeeAmount
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dt_balance
    )
    assert (
        swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_market_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_fee)
        == swap_fees_event_args.swapFeeAmount
    )

    # * Tests publisher swaps some DT back to Ocean with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)

    assert bpool.community_fee(ocean_contract.address) == 0
    assert bpool.community_fee(erc20_address) == 0

    tx = bpool.swap_exact_amount_out(
        erc20_token.address,
        web3.toWei(0.1, "ether"),
        ocean_contract.address,
        web3.toWei(0.0001, "ether"),
        web3.toWei(100, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dt_balance
    )
    assert (
        publisher_ocean_balance + swap_event_args.tokenAmountOut
        == ocean_contract.balanceOf(publisher_wallet.address)
    )

    assert (
        round(
            swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_market_fee)
        )
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_fee))
        == swap_fees_event_args.swapFeeAmount
    )

    # * Tests publisher adds more liquidity with joinPool() (adding both tokens)

    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)

    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)

    tx = bpool.join_pool(
        web3.toWei("0.01", "ether"),
        [
            web3.toWei("50", "ether"),
            web3.toWei("50", "ether"),
        ],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == erc20_token.address
    assert join_pool_event[1].args.tokenIn == ocean_contract.address

    assert web3.toWei("0.01", "ether") == bpool.balanceOf(publisher_wallet.address)
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20_token.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # * Tests consumer adds more liquidity with joinswapExternAmountIn (only OCEAN)

    consumer_ocean_balance = ocean_contract.balanceOf(consumer_wallet.address)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_join = side_staking.get_data_token_balance(erc20_token.address)

    ocean_contract.approve(bpool_address, web3.toWei(1000, "ether"), consumer_wallet)

    tx = bpool.join_swap_extern_amount_in(
        ocean_contract.address,
        web3.toWei(1, "ether"),
        web3.toWei(0.01, "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == ocean_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address
    assert join_pool_event[0].args.tokenAmountIn == web3.toWei(1, "ether")
    side_staking_amount_in = ss_contract_dt_balance - erc20_token.balanceOf(
        side_staking.address
    )

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_join - side_staking_amount_in
    )

    assert join_pool_event[1].args.tokenAmountIn == side_staking_amount_in

    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert bpt_event[0].args.bptAmount + ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    # * Tests consumer adds more liquidity with joinswapPoolAmountOut (only OCEAN)

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_ocean_balance = ocean_contract.balanceOf(consumer_wallet.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    dt_balance_before_join = side_staking.get_data_token_balance(erc20_token.address)
    bpt_amount_out = web3.toWei(0.1, "ether")
    max_ocean_in = web3.toWei(100, "ether")

    tx = bpool.join_swap_pool_amount_out(
        ocean_contract.address, bpt_amount_out, max_ocean_in, consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == ocean_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_join - join_pool_event[1].args.tokenAmountIn
    )
    assert consumer_ocean_balance == join_pool_event[
        0
    ].args.tokenAmountIn + ocean_contract.balanceOf(consumer_wallet.address)

    assert bpt_amount_out + consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    )
    assert ss_contract_bpt_balance + bpt_amount_out == bpool.balanceOf(
        side_staking.address
    )
    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)
    assert consumer_dt_balance == erc20_token.balanceOf(consumer_wallet.address)

    # * Tests consumer removes liquidity with ExitPool, receiving both tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_ocean_balance = ocean_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)

    tx = bpool.exit_pool(
        web3.toWei("0.5", "ether"),
        [
            web3.toWei(0.001, "ether"),
            web3.toWei(0.001, "ether"),
        ],
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.tokenOut == erc20_token.address
    assert exit_event[1].args.tokenOut == ocean_contract.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert exit_event[
        1
    ].args.tokenAmountOut + consumer_ocean_balance == ocean_contract.balanceOf(
        consumer_wallet.address
    )

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert (
        bpool.balanceOf(consumer_wallet.address) + web3.toWei("0.5", "ether")
        == consumer_bpt_balance
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)

    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * Tests consumer removes liquidity with exitswapPoolAmountIn, receiving only OCEAN tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_ocean_balance = ocean_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        ocean_contract.address,
        web3.toWei("0.05", "ether"),
        web3.toWei("0.005", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == ocean_contract.address
    assert exit_event[1].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_ocean_balance == ocean_contract.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )

    assert consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    ) + web3.toWei("0.05", "ether")

    assert ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    ) + web3.toWei("0.05", "ether")

    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapPoolAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_ocean_balance = ocean_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        erc20_token.address,
        web3.toWei("0.05", "ether"),
        web3.toWei("0.005", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert ocean_contract.balanceOf(consumer_wallet.address) == consumer_ocean_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert (
        bpool.balanceOf(consumer_wallet.address)
        == consumer_bpt_balance - bpt_event[0].args.bptAmount
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    ) + web3.toWei("0.05", "ether")

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)
    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapExternAmountOut, receiving only OCEAN tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_ocean_balance = ocean_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_extern_amount_out(
        ocean_contract.address,
        web3.toWei("0.001", "ether"),
        web3.toWei("0.005", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert consumer_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        consumer_wallet.address
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == ocean_contract.address
    assert exit_event[1].args.tokenOut == erc20_token.address
    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_ocean_balance == ocean_contract.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )
    assert ss_contract_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        side_staking.address
    )
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapExternAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_ocean_balance = ocean_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_extern_amount_out(
        erc20_token.address,
        web3.toWei("0.001", "ether"),
        web3.toWei("0.05", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert ocean_contract.balanceOf(consumer_wallet.address) == consumer_ocean_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert consumer_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        consumer_wallet.address
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)
    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * Tests no ocean and market fees were accounted for
    assert bpool.opf_fee() == 0
    assert bpool.get_swap_fee() == swap_market_fee
    assert bpool.community_fee(ocean_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert (bpool.market_fee(erc20_token.address) > 0) is True
    assert (bpool.market_fee(ocean_contract.address) > 0) is True


def test_pool_dai(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    publisher_wallet,
    factory_router,
):
    """Tests pool with DAI token 18 decimals and market fee 0.1%"""

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
    dai_contract = ERC20Token(address=get_address_of_type(config, "MockDAI"), web3=web3)
    dai_contract.transfer(
        consumer_wallet.address, web3.toWei("20", "ether"), factory_deployer_wallet
    )
    dai_contract.transfer(
        publisher_wallet.address, web3.toWei("20", "ether"), factory_deployer_wallet
    )

    erc721_token = deploy_erc721_token(
        config, web3, factory_deployer_wallet, consumer_wallet
    )
    swap_fee = web3.toWei(0.001, "ether")
    swap_ocean_fee = 0
    swap_market_fee = web3.toWei(0.001, "ether")

    # * Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = web3.toWei(1000, "ether")
    tx = erc721_token.create_erc20(
        ErcCreateData(
            1,
            ["ERC20DT1", "ERC20DT1Symbol"],
            [
                consumer_wallet.address,
                factory_deployer_wallet.address,
                consumer_wallet.address,
                "0x0000000000000000000000000000000000000000",
            ],
            [cap, 0],
            [],
        ),
        consumer_wallet,
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)
    event = erc721_factory.get_event_log(
        erc721_token.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    erc20_address = event[0].args.newTokenAddress
    erc20_token = ERC20Token(web3, erc20_address)

    assert erc20_token.get_permissions(consumer_wallet.address)[0] == True

    # * Tests consumer calls deployPool(), we then check dai and market fee"

    initial_dai_liq = web3.toWei(10, "ether")

    dai_contract.approve(
        get_address_of_type(config, "Router"),
        web3.toWei(10, "ether"),
        consumer_wallet,
    )

    pool_data = PoolData(
        [
            web3.toWei(1, "ether"),
            dai_contract.decimals(),
            initial_dai_liq,
            2500000,
            initial_dai_liq,
        ],
        [
            web3.toWei(0.001, "ether"),
            web3.toWei(0.001, "ether"),
        ],
        [
            side_staking.address,
            dai_contract.address,
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
    assert bpool.is_finalized() == True
    assert bpool.opf_fee() == web3.toWei(0.001, "ether")
    assert bpool.get_swap_fee() == web3.toWei(0.001, "ether")
    assert bpool.community_fee(dai_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.market_fee(dai_contract.address) == 0
    assert bpool.market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == web3.toWei(990, "ether")

    assert bpool.calc_pool_in_single_out(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_pool_in_single_out(dai_contract.address, web3.toWei(1, "ether"))
    assert bpool.calc_pool_out_single_in(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_pool_out_single_in(dai_contract.address, web3.toWei(1, "ether"))
    assert bpool.calc_single_in_pool_out(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_single_in_pool_out(dai_contract.address, web3.toWei(1, "ether"))
    assert bpool.calc_single_out_pool_in(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_single_out_pool_in(dai_contract.address, web3.toWei(1, "ether"))
    # * Tests publisher buys some DT - exactAmountIn

    assert dai_contract.balanceOf(bpool.address) == web3.toWei(10, "ether")
    dai_contract.approve(bpool_address, web3.toWei(10, "ether"), publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)

    tx = bpool.swap_exact_amount_in(
        dai_contract.address,
        web3.toWei(0.1, "ether"),
        erc20_address,
        web3.toWei(0.0001, "ether"),
        web3.toWei(100, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert (erc20_token.balanceOf(publisher_wallet.address) > 0) == True

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_fee_event[0].args

    # Check swap balances
    assert (
        dai_contract.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dai_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    # * Tests publisher buys some DT - exactAmountOut
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)
    dai_market_fee_balance = bpool.market_fee(dai_contract.address)

    tx = bpool.swap_exact_amount_out(
        dai_contract.address,
        web3.toWei(10, "ether"),
        erc20_address,
        web3.toWei(1, "ether"),
        web3.toWei(100, "ether"),
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
        dai_contract.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dai_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert swap_fees_event_args.tokenFees == dai_contract.address
    assert (
        dai_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )
    assert dt_market_fee_balance == bpool.market_fee(erc20_token.address)

    # * Tests publisher swaps some DT back to DAI with swapExactAmountIn, check swap custom fees
    assert bpool.is_finalized() is True

    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)
    dai_market_fee_balance = bpool.market_fee(dai_contract.address)

    tx = bpool.swap_exact_amount_in(
        erc20_address,
        web3.toWei(0.1, "ether"),
        dai_contract.address,
        web3.toWei(0.0001, "ether"),
        web3.toWei(100, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert web3.toWei("0.0001", "ether") == swap_fees_event_args.marketFeeAmount
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dt_balance
    )
    assert (
        swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_market_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_fee)
        == swap_fees_event_args.swapFeeAmount
    )

    # * Tests publisher swaps some DT back to dai with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        erc20_token.address,
        web3.toWei(0.1, "ether"),
        dai_contract.address,
        web3.toWei(0.0001, "ether"),
        web3.toWei(100, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dt_balance
    )
    assert (
        publisher_dai_balance + swap_event_args.tokenAmountOut
        == dai_contract.balanceOf(publisher_wallet.address)
    )

    assert (
        round(
            swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_market_fee)
        )
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_fee))
        == swap_fees_event_args.swapFeeAmount
    )

    # * Tests publisher adds more liquidity with joinPool() (adding both tokens)

    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)

    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    dai_contract.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)

    tx = bpool.join_pool(
        web3.toWei("0.01", "ether"),
        [
            web3.toWei("50", "ether"),
            web3.toWei("50", "ether"),
        ],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == erc20_token.address
    assert join_pool_event[1].args.tokenIn == dai_contract.address

    assert web3.toWei("0.01", "ether") == bpool.balanceOf(publisher_wallet.address)
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20_token.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # * Tests consumer adds more liquidity with joinswapExternAmountIn (only OCEAN)

    consumer_ocean_balance = dai_contract.balanceOf(consumer_wallet.address)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_join = side_staking.get_data_token_balance(erc20_token.address)

    dai_contract.approve(bpool_address, web3.toWei(1000, "ether"), consumer_wallet)

    tx = bpool.join_swap_extern_amount_in(
        dai_contract.address,
        web3.toWei(1, "ether"),
        web3.toWei(0.01, "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == dai_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address
    assert join_pool_event[0].args.tokenAmountIn == web3.toWei(1, "ether")
    side_staking_amount_in = ss_contract_dt_balance - erc20_token.balanceOf(
        side_staking.address
    )

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_join - side_staking_amount_in
    )

    assert join_pool_event[1].args.tokenAmountIn == side_staking_amount_in

    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert bpt_event[0].args.bptAmount + ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    # * Tests consumer adds more liquidity with joinswapPoolAmountOut (only dai)

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    dt_balance_before_join = side_staking.get_data_token_balance(erc20_token.address)
    bpt_amount_out = web3.toWei(0.1, "ether")
    max_dai_in = web3.toWei(100, "ether")

    tx = bpool.join_swap_pool_amount_out(
        dai_contract.address, bpt_amount_out, max_dai_in, consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == dai_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_join - join_pool_event[1].args.tokenAmountIn
    )
    assert consumer_dai_balance == join_pool_event[
        0
    ].args.tokenAmountIn + dai_contract.balanceOf(consumer_wallet.address)

    assert bpt_amount_out + consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    )
    assert ss_contract_bpt_balance + bpt_amount_out == bpool.balanceOf(
        side_staking.address
    )
    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)
    assert consumer_dt_balance == erc20_token.balanceOf(consumer_wallet.address)

    # * Tests consumer removes liquidity with ExitPool, receiving both tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)

    tx = bpool.exit_pool(
        web3.toWei("0.5", "ether"),
        [
            web3.toWei(0.001, "ether"),
            web3.toWei(0.001, "ether"),
        ],
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.tokenOut == erc20_token.address
    assert exit_event[1].args.tokenOut == dai_contract.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert exit_event[
        1
    ].args.tokenAmountOut + consumer_dai_balance == dai_contract.balanceOf(
        consumer_wallet.address
    )

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert (
        bpool.balanceOf(consumer_wallet.address) + web3.toWei("0.5", "ether")
        == consumer_bpt_balance
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)

    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * Tests consumer removes liquidity with exitswapPoolAmountIn, receiving only dai tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        dai_contract.address,
        web3.toWei("0.05", "ether"),
        web3.toWei("0.005", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == dai_contract.address
    assert exit_event[1].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dai_balance == dai_contract.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )

    assert consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    ) + web3.toWei("0.05", "ether")

    assert ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    ) + web3.toWei("0.05", "ether")

    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapPoolAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        erc20_token.address,
        web3.toWei("0.05", "ether"),
        web3.toWei("0.005", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert dai_contract.balanceOf(consumer_wallet.address) == consumer_dai_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert (
        bpool.balanceOf(consumer_wallet.address)
        == consumer_bpt_balance - bpt_event[0].args.bptAmount
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    ) + web3.toWei("0.05", "ether")

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)
    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapExternAmountOut, receiving only dai tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_extern_amount_out(
        dai_contract.address,
        web3.toWei("0.001", "ether"),
        web3.toWei("0.005", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert consumer_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        consumer_wallet.address
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == dai_contract.address
    assert exit_event[1].args.tokenOut == erc20_token.address
    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dai_balance == dai_contract.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )
    assert ss_contract_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        side_staking.address
    )
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapExternAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_extern_amount_out(
        erc20_token.address,
        web3.toWei("0.001", "ether"),
        web3.toWei("0.05", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert dai_contract.balanceOf(consumer_wallet.address) == consumer_dai_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert consumer_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        consumer_wallet.address
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)
    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * Tests Ocean and market fees were accounted for
    assert bpool.opf_fee() == web3.toWei("0.001", "ether")
    assert bpool.get_swap_fee() == swap_market_fee
    assert (bpool.community_fee(erc20_token.address) > 0) is True
    assert (bpool.community_fee(dai_contract.address) > 0) is True
    assert (bpool.market_fee(erc20_token.address) > 0) is True
    assert (bpool.market_fee(dai_contract.address) > 0) is True


def test_pool_usdc(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    publisher_wallet,
    factory_router,
):
    """Tests pool with NO ocean token (USDC 6 decimals) and market fee 0.1%"""
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))

    usdc_contract = ERC20Token(
        address=get_address_of_type(config, "MockUSDC"), web3=web3
    )
    usdc_contract.transfer(
        consumer_wallet.address, web3.toWei("20", "ether"), factory_deployer_wallet
    )
    usdc_contract.transfer(
        publisher_wallet.address, web3.toWei("20", "ether"), factory_deployer_wallet
    )

    erc721_token = deploy_erc721_token(
        config, web3, factory_deployer_wallet, consumer_wallet
    )
    swap_fee = web3.toWei(0.001, "ether")
    swap_market_fee = web3.toWei(0.001, "ether")

    # * Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = web3.toWei(1000, "ether")
    tx = erc721_token.create_erc20(
        ErcCreateData(
            1,
            ["ERC20DT1", "ERC20DT1Symbol"],
            [
                consumer_wallet.address,
                factory_deployer_wallet.address,
                consumer_wallet.address,
                "0x0000000000000000000000000000000000000000",
            ],
            [cap, 0],
            [],
        ),
        consumer_wallet,
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)
    event = erc721_factory.get_event_log(
        erc721_token.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    erc20_address = event[0].args.newTokenAddress
    erc20_token = ERC20Token(web3, erc20_address)

    assert erc20_token.get_permissions(consumer_wallet.address)[0] == True

    # * Tests consumer calls deployPool(), we then check USDC and market fee"

    initial_usdc_liq = int(880 * 1e6)  # 880 USDC

    usdc_contract.approve(
        get_address_of_type(config, "Router"),
        web3.toWei(100, "ether"),
        consumer_wallet,
    )

    pool_data = PoolData(
        [
            web3.toWei(1, "ether"),
            usdc_contract.decimals(),
            initial_usdc_liq,
            2500000,
            initial_usdc_liq,
        ],
        [
            web3.toWei(0.001, "ether"),
            web3.toWei(0.001, "ether"),
        ],
        [
            side_staking.address,
            usdc_contract.address,
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
    assert bpool.is_finalized() == True
    assert bpool.opf_fee() == web3.toWei(0.001, "ether")
    assert bpool.get_swap_fee() == web3.toWei(0.001, "ether")
    assert bpool.community_fee(usdc_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.market_fee(usdc_contract.address) == 0
    assert bpool.market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == web3.toWei(120, "ether")

    assert (
        bpool.calc_pool_in_single_out(erc20_address, web3.toWei(1, "ether")) // 1e12
        == bpool.calc_pool_in_single_out(usdc_contract.address, int(1e6)) // 1e12
    )
    assert bpool.calc_pool_out_single_in(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_pool_out_single_in(usdc_contract.address, int(1e6))
    assert bpool.calc_single_in_pool_out(
        erc20_address, web3.toWei(10, "ether")
    ) // 1e12 == bpool.calc_single_in_pool_out(
        usdc_contract.address, web3.toWei(10, "ether")
    )
    assert bpool.calc_single_out_pool_in(
        erc20_address, web3.toWei(10, "ether")
    ) // 1e12 == bpool.calc_single_out_pool_in(
        usdc_contract.address, web3.toWei(10, "ether")
    )
    # * Tests publisher buys some DT - exactAmountIn

    assert usdc_contract.balanceOf(bpool.address) == initial_usdc_liq
    usdc_contract.approve(bpool_address, web3.toWei(10, "ether"), publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    tx = bpool.swap_exact_amount_in(
        usdc_contract.address,
        int(1e7),
        erc20_address,
        web3.toWei(1, "ether"),
        web3.toWei(5, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert (erc20_token.balanceOf(publisher_wallet.address) > 0) == True

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_fee_event[0].args

    # Check swap balances
    assert (
        usdc_contract.balanceOf(publisher_wallet.address)
        + swap_event_args.tokenAmountIn
        == publisher_usdc_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    # * Tests publisher buys some DT - exactAmountOut
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)
    usdc_market_fee_balance = bpool.market_fee(usdc_contract.address)

    tx = bpool.swap_exact_amount_out(
        usdc_contract.address,
        web3.toWei(10, "ether"),
        erc20_address,
        web3.toWei(1, "ether"),
        web3.toWei(100, "ether"),
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
        usdc_contract.balanceOf(publisher_wallet.address)
        + swap_event_args.tokenAmountIn
        == publisher_usdc_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert swap_fees_event_args.tokenFees == usdc_contract.address
    assert (
        usdc_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )
    assert dt_market_fee_balance == bpool.market_fee(erc20_token.address)

    # * Tests publisher swaps some DT back to USDC with swapExactAmountIn, check swap custom fees
    assert bpool.is_finalized() is True

    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)
    usdc_market_fee_balance = bpool.market_fee(usdc_contract.address)

    tx = bpool.swap_exact_amount_in(
        erc20_address,
        web3.toWei(0.1, "ether"),
        usdc_contract.address,
        int(1e4),
        int(2 ** 256 - 1),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert web3.toWei("0.0001", "ether") == swap_fees_event_args.marketFeeAmount
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dt_balance
    )
    assert (
        swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_market_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_fee)
        == swap_fees_event_args.swapFeeAmount
    )

    # * Tests publisher swaps some DT back to USDC with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        erc20_token.address,
        web3.toWei(10, "ether"),
        usdc_contract.address,
        int(1e6),
        web3.toWei(1000000000000000, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dt_balance
    )
    assert (
        publisher_usdc_balance + swap_event_args.tokenAmountOut
        == usdc_contract.balanceOf(publisher_wallet.address)
    )

    assert (
        round(
            swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_market_fee)
        )
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_fee))
        == swap_fees_event_args.swapFeeAmount
    )

    # * Tests publisher adds more liquidity with joinPool() (adding both tokens)

    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)

    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    usdc_contract.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)

    tx = bpool.join_pool(
        web3.toWei("0.01", "ether"),
        [
            web3.toWei("50", "ether"),
            web3.toWei("50", "ether"),
        ],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == erc20_token.address
    assert join_pool_event[1].args.tokenIn == usdc_contract.address

    assert web3.toWei("0.01", "ether") == bpool.balanceOf(publisher_wallet.address)
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20_token.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # * Tests consumer adds more liquidity with joinswapExternAmountIn (only OCEAN)

    consumer_ocean_balance = usdc_contract.balanceOf(consumer_wallet.address)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_join = side_staking.get_data_token_balance(erc20_token.address)

    usdc_contract.approve(bpool_address, web3.toWei(1000, "ether"), consumer_wallet)

    tx = bpool.join_swap_extern_amount_in(
        usdc_contract.address,
        int(1e6),
        web3.toWei(0.01, "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == usdc_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address
    assert join_pool_event[0].args.tokenAmountIn == int(1e6)
    side_staking_amount_in = ss_contract_dt_balance - erc20_token.balanceOf(
        side_staking.address
    )

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_join - side_staking_amount_in
    )

    assert join_pool_event[1].args.tokenAmountIn == side_staking_amount_in

    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert bpt_event[0].args.bptAmount + ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    # * Tests consumer adds more liquidity with joinswapPoolAmountOut (only USDC)

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    dt_balance_before_join = side_staking.get_data_token_balance(erc20_token.address)
    bpt_amount_out = web3.toWei(0.1, "ether")
    max_usdc_in = web3.toWei(100, "ether")

    tx = bpool.join_swap_pool_amount_out(
        usdc_contract.address, bpt_amount_out, max_usdc_in, consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == usdc_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_join - join_pool_event[1].args.tokenAmountIn
    )
    assert consumer_usdc_balance == join_pool_event[
        0
    ].args.tokenAmountIn + usdc_contract.balanceOf(consumer_wallet.address)

    assert bpt_amount_out + consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    )
    assert ss_contract_bpt_balance + bpt_amount_out == bpool.balanceOf(
        side_staking.address
    )
    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)
    assert consumer_dt_balance == erc20_token.balanceOf(consumer_wallet.address)

    # * Tests consumer removes liquidity with ExitPool, receiving both tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)

    tx = bpool.exit_pool(
        web3.toWei("0.1", "ether"),
        [web3.toWei("0.1", "ether"), int(1e5)],
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.tokenOut == erc20_token.address
    assert exit_event[1].args.tokenOut == usdc_contract.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert exit_event[
        1
    ].args.tokenAmountOut + consumer_usdc_balance == usdc_contract.balanceOf(
        consumer_wallet.address
    )

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert (
        bpool.balanceOf(consumer_wallet.address) + web3.toWei("0.1", "ether")
        == consumer_bpt_balance
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)

    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * Tests consumer removes liquidity with exitswapPoolAmountIn, receiving only USDC tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        usdc_contract.address,
        web3.toWei("0.1", "ether"),
        int(1e5),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == usdc_contract.address
    assert exit_event[1].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_usdc_balance == usdc_contract.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )

    assert consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    ) + web3.toWei("0.1", "ether")

    assert ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    ) + web3.toWei("0.1", "ether")

    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapPoolAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        erc20_token.address,
        web3.toWei("0.05", "ether"),
        web3.toWei("0.005", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert usdc_contract.balanceOf(consumer_wallet.address) == consumer_usdc_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert (
        bpool.balanceOf(consumer_wallet.address)
        == consumer_bpt_balance - bpt_event[0].args.bptAmount
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    ) + web3.toWei("0.05", "ether")

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)
    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapExternAmountOut, receiving only USDC tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_extern_amount_out(
        usdc_contract.address,
        int(1e6),
        web3.toWei("1", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert consumer_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        consumer_wallet.address
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == usdc_contract.address
    assert exit_event[1].args.tokenOut == erc20_token.address
    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_usdc_balance == usdc_contract.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )
    assert ss_contract_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        side_staking.address
    )
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapExternAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_extern_amount_out(
        erc20_token.address,
        web3.toWei("0.001", "ether"),
        web3.toWei("0.05", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert usdc_contract.balanceOf(consumer_wallet.address) == consumer_usdc_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert consumer_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        consumer_wallet.address
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)
    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * Tests Ocean and market fees were accounted for
    assert bpool.opf_fee() == web3.toWei("0.001", "ether")
    assert bpool.get_swap_fee() == swap_market_fee
    assert (bpool.community_fee(erc20_token.address) > 0) is True
    assert (bpool.community_fee(usdc_contract.address) > 0) is True
    assert (bpool.market_fee(erc20_token.address) > 0) is True
    assert (bpool.market_fee(usdc_contract.address) > 0) is True


def test_pool_usdc_flexible(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    publisher_wallet,
    factory_router,
):
    """Tests pool with NO ocean token (USDC 6 decimals) and market fee 0.1% flexible opf fee"""
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
    usdc_contract = ERC20Token(
        address=get_address_of_type(config, "MockUSDC"), web3=web3
    )
    usdc_contract.transfer(
        consumer_wallet.address, web3.toWei("20", "ether"), factory_deployer_wallet
    )
    usdc_contract.transfer(
        publisher_wallet.address, web3.toWei("20", "ether"), factory_deployer_wallet
    )

    erc721_token = deploy_erc721_token(
        config, web3, factory_deployer_wallet, consumer_wallet
    )
    swap_fee = web3.toWei(0.001, "ether")
    swap_ocean_fee = 0
    swap_market_fee = web3.toWei(0.001, "ether")

    # * Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = web3.toWei(1000, "ether")
    tx = erc721_token.create_erc20(
        ErcCreateData(
            1,
            ["ERC20DT1", "ERC20DT1Symbol"],
            [
                consumer_wallet.address,
                factory_deployer_wallet.address,
                consumer_wallet.address,
                "0x0000000000000000000000000000000000000000",
            ],
            [cap, 0],
            [],
        ),
        consumer_wallet,
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)
    event = erc721_factory.get_event_log(
        erc721_token.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    erc20_address = event[0].args.newTokenAddress
    erc20_token = ERC20Token(web3, erc20_address)

    assert erc20_token.get_permissions(consumer_wallet.address)[0] == True

    # * Tests consumer calls deployPool(), we then check USDC and market fee"

    initial_usdc_liq = int(880 * 1e6)  # 880 USDC

    usdc_contract.approve(
        get_address_of_type(config, "Router"),
        web3.toWei(10, "ether"),
        consumer_wallet,
    )

    pool_data = PoolData(
        [
            web3.toWei(1, "ether"),
            usdc_contract.decimals(),
            initial_usdc_liq,
            2500000,
            initial_usdc_liq,
        ],
        [
            web3.toWei(0.001, "ether"),
            web3.toWei(0.001, "ether"),
        ],
        [
            side_staking.address,
            usdc_contract.address,
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
    factory_router.update_opf_fee(web3.toWei(0.01, "ether"), factory_deployer_wallet)

    assert bpool.is_finalized() == True
    assert bpool.opf_fee() == web3.toWei(0.01, "ether")
    assert bpool.get_swap_fee() == web3.toWei(0.001, "ether")
    assert bpool.community_fee(usdc_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.market_fee(usdc_contract.address) == 0
    assert bpool.market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == web3.toWei(120, "ether")
    assert (
        bpool.calc_pool_in_single_out(erc20_address, web3.toWei(1, "ether")) // 1e12
        == bpool.calc_pool_in_single_out(usdc_contract.address, int(1e6)) // 1e12
    )
    assert bpool.calc_pool_out_single_in(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_pool_out_single_in(usdc_contract.address, int(1e6))
    assert bpool.calc_single_in_pool_out(
        erc20_address, web3.toWei(10, "ether")
    ) // 1e12 == bpool.calc_single_in_pool_out(
        usdc_contract.address, web3.toWei(10, "ether")
    )
    assert bpool.calc_single_out_pool_in(
        erc20_address, web3.toWei(10, "ether")
    ) // 1e12 == bpool.calc_single_out_pool_in(
        usdc_contract.address, web3.toWei(10, "ether")
    )
    # * Tests publisher buys some DT - exactAmountIn

    assert usdc_contract.balanceOf(bpool.address) == initial_usdc_liq
    usdc_contract.approve(bpool_address, web3.toWei(10, "ether"), publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    tx = bpool.swap_exact_amount_in(
        usdc_contract.address,
        int(1e7),
        erc20_address,
        web3.toWei(1, "ether"),
        web3.toWei(5, "ether"),
        publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert (erc20_token.balanceOf(publisher_wallet.address) > 0) == True

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_fee_event[0].args

    # Check swap balances
    assert (
        usdc_contract.balanceOf(publisher_wallet.address)
        + swap_event_args.tokenAmountIn
        == publisher_usdc_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    # * Tests opf fee is updated to 0.1% again
    assert bpool.opf_fee() == web3.toWei(0.01, "ether")
    factory_router.update_opf_fee(web3.toWei(0.001, "ether"), factory_deployer_wallet)
    assert bpool.opf_fee() == web3.toWei(0.001, "ether")

    # * Tests publisher buys some DT - exactAmountOut
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)
    usdc_market_fee_balance = bpool.market_fee(usdc_contract.address)

    tx = bpool.swap_exact_amount_out(
        usdc_contract.address,
        web3.toWei(10, "ether"),
        erc20_address,
        web3.toWei(1, "ether"),
        web3.toWei(100, "ether"),
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
        usdc_contract.balanceOf(publisher_wallet.address)
        + swap_event_args.tokenAmountIn
        == publisher_usdc_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert swap_fees_event_args.tokenFees == usdc_contract.address
    assert (
        usdc_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )
    assert dt_market_fee_balance == bpool.market_fee(erc20_token.address)

    # * Tests publisher swaps some DT back to USDC with swapExactAmountIn, check swap custom fees
    assert bpool.is_finalized() is True

    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)
    usdc_market_fee_balance = bpool.market_fee(usdc_contract.address)

    tx = bpool.swap_exact_amount_in(
        erc20_address,
        web3.toWei(0.1, "ether"),
        usdc_contract.address,
        int(1e4),
        int(2 ** 256 - 1),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert web3.toWei("0.0001", "ether") == swap_fees_event_args.marketFeeAmount
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dt_balance
    )
    assert (
        swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_market_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_fee)
        == swap_fees_event_args.swapFeeAmount
    )

    # * Tests publisher swaps some DT back to USDC with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        erc20_token.address,
        web3.toWei(10, "ether"),
        usdc_contract.address,
        int(1e6),
        web3.toWei(1000000000000000, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dt_balance
    )
    assert (
        publisher_usdc_balance + swap_event_args.tokenAmountOut
        == usdc_contract.balanceOf(publisher_wallet.address)
    )

    assert (
        round(
            swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_market_fee)
        )
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_fee))
        == swap_fees_event_args.swapFeeAmount
    )

    # * Tests publisher adds more liquidity with joinPool() (adding both tokens)

    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)

    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    usdc_contract.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)

    tx = bpool.join_pool(
        web3.toWei("0.01", "ether"),
        [
            web3.toWei("50", "ether"),
            web3.toWei("50", "ether"),
        ],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == erc20_token.address
    assert join_pool_event[1].args.tokenIn == usdc_contract.address

    assert web3.toWei("0.01", "ether") == bpool.balanceOf(publisher_wallet.address)
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20_token.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # * Tests consumer adds more liquidity with joinswapExternAmountIn (only OCEAN)

    consumer_ocean_balance = usdc_contract.balanceOf(consumer_wallet.address)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_join = side_staking.get_data_token_balance(erc20_token.address)

    usdc_contract.approve(bpool_address, web3.toWei(1000, "ether"), consumer_wallet)

    tx = bpool.join_swap_extern_amount_in(
        usdc_contract.address,
        int(1e6),
        web3.toWei(0.01, "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == usdc_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address
    assert join_pool_event[0].args.tokenAmountIn == int(1e6)
    side_staking_amount_in = ss_contract_dt_balance - erc20_token.balanceOf(
        side_staking.address
    )

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_join - side_staking_amount_in
    )

    assert join_pool_event[1].args.tokenAmountIn == side_staking_amount_in

    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert bpt_event[0].args.bptAmount + ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    # * Tests consumer adds more liquidity with joinswapPoolAmountOut (only USDC)

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    dt_balance_before_join = side_staking.get_data_token_balance(erc20_token.address)
    bpt_amount_out = web3.toWei(0.1, "ether")
    max_usdc_in = web3.toWei(100, "ether")

    tx = bpool.join_swap_pool_amount_out(
        usdc_contract.address, bpt_amount_out, max_usdc_in, consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == usdc_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_join - join_pool_event[1].args.tokenAmountIn
    )
    assert consumer_usdc_balance == join_pool_event[
        0
    ].args.tokenAmountIn + usdc_contract.balanceOf(consumer_wallet.address)

    assert bpt_amount_out + consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    )
    assert ss_contract_bpt_balance + bpt_amount_out == bpool.balanceOf(
        side_staking.address
    )
    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)
    assert consumer_dt_balance == erc20_token.balanceOf(consumer_wallet.address)

    # * Tests consumer removes liquidity with ExitPool, receiving both tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)

    tx = bpool.exit_pool(
        web3.toWei("0.1", "ether"),
        [web3.toWei("0.1", "ether"), int(1e5)],
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.tokenOut == erc20_token.address
    assert exit_event[1].args.tokenOut == usdc_contract.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert exit_event[
        1
    ].args.tokenAmountOut + consumer_usdc_balance == usdc_contract.balanceOf(
        consumer_wallet.address
    )

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert (
        bpool.balanceOf(consumer_wallet.address) + web3.toWei("0.1", "ether")
        == consumer_bpt_balance
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)

    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * Tests consumer removes liquidity with exitswapPoolAmountIn, receiving only USDC tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        usdc_contract.address,
        web3.toWei("0.1", "ether"),
        int(1e5),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == usdc_contract.address
    assert exit_event[1].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_usdc_balance == usdc_contract.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )

    assert consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    ) + web3.toWei("0.1", "ether")

    assert ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    ) + web3.toWei("0.1", "ether")

    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapPoolAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        erc20_token.address,
        web3.toWei("0.05", "ether"),
        web3.toWei("0.005", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert usdc_contract.balanceOf(consumer_wallet.address) == consumer_usdc_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert (
        bpool.balanceOf(consumer_wallet.address)
        == consumer_bpt_balance - bpt_event[0].args.bptAmount
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    ) + web3.toWei("0.05", "ether")

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)
    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapExternAmountOut, receiving only USDC tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_extern_amount_out(
        usdc_contract.address,
        int(1e6),
        web3.toWei("1", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert consumer_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        consumer_wallet.address
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == usdc_contract.address
    assert exit_event[1].args.tokenOut == erc20_token.address
    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_usdc_balance == usdc_contract.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )
    assert ss_contract_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        side_staking.address
    )
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapExternAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_extern_amount_out(
        erc20_token.address,
        web3.toWei("0.001", "ether"),
        web3.toWei("0.05", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert usdc_contract.balanceOf(consumer_wallet.address) == consumer_usdc_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert consumer_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        consumer_wallet.address
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)
    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * Tests Ocean and market fees were accounted for
    assert bpool.opf_fee() == web3.toWei("0.001", "ether")
    assert bpool.get_swap_fee() == swap_market_fee
    assert (bpool.community_fee(erc20_token.address) > 0) is True
    assert (bpool.community_fee(usdc_contract.address) > 0) is True
    assert (bpool.market_fee(erc20_token.address) > 0) is True
    assert (bpool.market_fee(usdc_contract.address) > 0) is True


def test_pool_dai_flexible(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    publisher_wallet,
    factory_router,
):
    """Tests pool with NO ocean token (DAI 18 decimals) and market fee 0.1% and flexible opf fee"""
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
    dai_contract = ERC20Token(address=get_address_of_type(config, "MockDAI"), web3=web3)
    dai_contract.transfer(
        consumer_wallet.address, web3.toWei("20", "ether"), factory_deployer_wallet
    )
    dai_contract.transfer(
        publisher_wallet.address, web3.toWei("20", "ether"), factory_deployer_wallet
    )

    erc721_token = deploy_erc721_token(
        config, web3, factory_deployer_wallet, consumer_wallet
    )
    swap_fee = web3.toWei(0.001, "ether")
    swap_ocean_fee = 0
    swap_market_fee = web3.toWei(0.001, "ether")

    # * Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = web3.toWei(1000, "ether")
    tx = erc721_token.create_erc20(
        ErcCreateData(
            1,
            ["ERC20DT1", "ERC20DT1Symbol"],
            [
                consumer_wallet.address,
                factory_deployer_wallet.address,
                consumer_wallet.address,
                "0x0000000000000000000000000000000000000000",
            ],
            [cap, 0],
            [],
        ),
        consumer_wallet,
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)
    event = erc721_factory.get_event_log(
        erc721_token.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    erc20_address = event[0].args.newTokenAddress
    erc20_token = ERC20Token(web3, erc20_address)

    assert erc20_token.get_permissions(consumer_wallet.address)[0] == True

    # * Tests consumer calls deployPool(), we then check DAI and market fee"

    initial_dai_liq = web3.toWei(10, "ether")

    dai_contract.approve(
        get_address_of_type(config, "Router"),
        web3.toWei(10, "ether"),
        consumer_wallet,
    )

    pool_data = PoolData(
        [
            web3.toWei(1, "ether"),
            18,
            initial_dai_liq,
            2500000,
            initial_dai_liq,
        ],
        [
            web3.toWei(0.001, "ether"),
            web3.toWei(0.001, "ether"),
        ],
        [
            side_staking.address,
            dai_contract.address,
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
    factory_router.update_opf_fee(web3.toWei(0.01, "ether"), factory_deployer_wallet)

    assert bpool.is_finalized() == True
    assert bpool.opf_fee() == web3.toWei(0.01, "ether")
    assert bpool.get_swap_fee() == web3.toWei(0.001, "ether")
    assert bpool.community_fee(dai_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.market_fee(dai_contract.address) == 0
    assert bpool.market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == web3.toWei(990, "ether")

    assert bpool.calc_pool_in_single_out(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_pool_in_single_out(dai_contract.address, web3.toWei(1, "ether"))
    assert bpool.calc_pool_out_single_in(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_pool_out_single_in(dai_contract.address, web3.toWei(1, "ether"))
    assert bpool.calc_single_in_pool_out(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_single_in_pool_out(dai_contract.address, web3.toWei(1, "ether"))
    assert bpool.calc_single_out_pool_in(
        erc20_address, web3.toWei(1, "ether")
    ) == bpool.calc_single_out_pool_in(dai_contract.address, web3.toWei(1, "ether"))
    # * Tests publisher buys some DT - exactAmountIn

    assert dai_contract.balanceOf(bpool.address) == web3.toWei(10, "ether")
    dai_contract.approve(bpool_address, web3.toWei(10, "ether"), publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)

    tx = bpool.swap_exact_amount_in(
        dai_contract.address,
        web3.toWei(0.1, "ether"),
        erc20_address,
        web3.toWei(0.0001, "ether"),
        web3.toWei(100, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert (erc20_token.balanceOf(publisher_wallet.address) > 0) == True

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_fee_event[0].args

    # Check swap balances
    assert (
        dai_contract.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dai_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    # * Tests opf fee is updated to 0.1% again
    assert bpool.opf_fee() == web3.toWei(0.01, "ether")
    factory_router.update_opf_fee(web3.toWei(0.001, "ether"), factory_deployer_wallet)
    assert bpool.opf_fee() == web3.toWei(0.001, "ether")

    # * Tests publisher buys some DT - exactAmountOut
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)
    dai_market_fee_balance = bpool.market_fee(dai_contract.address)

    tx = bpool.swap_exact_amount_out(
        dai_contract.address,
        web3.toWei(10, "ether"),
        erc20_address,
        web3.toWei(1, "ether"),
        web3.toWei(100, "ether"),
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
        dai_contract.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dai_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert swap_fees_event_args.tokenFees == dai_contract.address
    assert (
        dai_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )
    assert dt_market_fee_balance == bpool.market_fee(erc20_token.address)

    # * Tests publisher swaps some DT back to DAI with swapExactAmountIn, check swap custom fees
    assert bpool.is_finalized() is True

    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)
    dai_market_fee_balance = bpool.market_fee(dai_contract.address)

    tx = bpool.swap_exact_amount_in(
        erc20_address,
        web3.toWei(0.1, "ether"),
        dai_contract.address,
        web3.toWei(0.0001, "ether"),
        web3.toWei(100, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert web3.toWei("0.0001", "ether") == swap_fees_event_args.marketFeeAmount
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dt_balance
    )
    assert (
        swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_market_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_fee)
        == swap_fees_event_args.swapFeeAmount
    )

    # * Tests publisher swaps some DT back to DAI with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        erc20_token.address,
        web3.toWei(0.1, "ether"),
        dai_contract.address,
        web3.toWei(0.0001, "ether"),
        web3.toWei(100, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_fees_event_args = swap_fees_event[0].args
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dt_balance
    )
    assert (
        publisher_dai_balance + swap_event_args.tokenAmountOut
        == dai_contract.balanceOf(publisher_wallet.address)
    )

    assert (
        round(
            swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_market_fee)
        )
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (web3.toWei(1, "ether") / swap_fee))
        == swap_fees_event_args.swapFeeAmount
    )

    # * Tests publisher adds more liquidity with joinPool() (adding both tokens)

    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.market_fee(erc20_token.address)

    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    dai_contract.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)
    erc20_token.approve(bpool_address, web3.toWei(1000, "ether"), publisher_wallet)

    tx = bpool.join_pool(
        web3.toWei("0.01", "ether"),
        [
            web3.toWei("50", "ether"),
            web3.toWei("50", "ether"),
        ],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == erc20_token.address
    assert join_pool_event[1].args.tokenIn == dai_contract.address

    assert web3.toWei("0.01", "ether") == bpool.balanceOf(publisher_wallet.address)
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20_token.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # * Tests consumer adds more liquidity with joinswapExternAmountIn (only OCEAN)

    consumer_ocean_balance = dai_contract.balanceOf(consumer_wallet.address)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_join = side_staking.get_data_token_balance(erc20_token.address)

    dai_contract.approve(bpool_address, web3.toWei(1000, "ether"), consumer_wallet)

    tx = bpool.join_swap_extern_amount_in(
        dai_contract.address,
        web3.toWei(1, "ether"),
        web3.toWei(0.01, "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == dai_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address
    assert join_pool_event[0].args.tokenAmountIn == web3.toWei(1, "ether")
    side_staking_amount_in = ss_contract_dt_balance - erc20_token.balanceOf(
        side_staking.address
    )

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_join - side_staking_amount_in
    )

    assert join_pool_event[1].args.tokenAmountIn == side_staking_amount_in

    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert bpt_event[0].args.bptAmount + ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    # * Tests consumer adds more liquidity with joinswapPoolAmountOut (only DAI)

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    dt_balance_before_join = side_staking.get_data_token_balance(erc20_token.address)
    bpt_amount_out = web3.toWei(0.1, "ether")
    max_dai_in = web3.toWei(100, "ether")

    tx = bpool.join_swap_pool_amount_out(
        dai_contract.address, bpt_amount_out, max_dai_in, consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert join_pool_event[0].args.tokenIn == dai_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_join - join_pool_event[1].args.tokenAmountIn
    )
    assert consumer_dai_balance == join_pool_event[
        0
    ].args.tokenAmountIn + dai_contract.balanceOf(consumer_wallet.address)

    assert bpt_amount_out + consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    )
    assert ss_contract_bpt_balance + bpt_amount_out == bpool.balanceOf(
        side_staking.address
    )
    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)
    assert consumer_dt_balance == erc20_token.balanceOf(consumer_wallet.address)

    # * Tests consumer removes liquidity with ExitPool, receiving both tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)

    tx = bpool.exit_pool(
        web3.toWei("0.5", "ether"),
        [
            web3.toWei(0.001, "ether"),
            web3.toWei(0.001, "ether"),
        ],
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.tokenOut == erc20_token.address
    assert exit_event[1].args.tokenOut == dai_contract.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert exit_event[
        1
    ].args.tokenAmountOut + consumer_dai_balance == dai_contract.balanceOf(
        consumer_wallet.address
    )

    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert (
        bpool.balanceOf(consumer_wallet.address) + web3.toWei("0.5", "ether")
        == consumer_bpt_balance
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)

    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * Tests consumer removes liquidity with exitswapPoolAmountIn, receiving only DAI tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        dai_contract.address,
        web3.toWei("0.05", "ether"),
        web3.toWei("0.005", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == dai_contract.address
    assert exit_event[1].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dai_balance == dai_contract.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )

    assert consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    ) + web3.toWei("0.05", "ether")

    assert ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    ) + web3.toWei("0.05", "ether")

    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapPoolAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        erc20_token.address,
        web3.toWei("0.05", "ether"),
        web3.toWei("0.005", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert dai_contract.balanceOf(consumer_wallet.address) == consumer_dai_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert (
        bpool.balanceOf(consumer_wallet.address)
        == consumer_bpt_balance - bpt_event[0].args.bptAmount
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert consumer_bpt_balance == bpool.balanceOf(
        consumer_wallet.address
    ) + web3.toWei("0.05", "ether")

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)
    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapExternAmountOut, receiving only DAI tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_extern_amount_out(
        dai_contract.address,
        web3.toWei("0.001", "ether"),
        web3.toWei("0.005", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert consumer_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        consumer_wallet.address
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == dai_contract.address
    assert exit_event[1].args.tokenOut == erc20_token.address
    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dai_balance == dai_contract.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )
    assert ss_contract_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        side_staking.address
    )
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # * consumer removes liquidity with exitswapExternAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_data_token_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_extern_amount_out(
        erc20_token.address,
        web3.toWei("0.001", "ether"),
        web3.toWei("0.05", "ether"),
        consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert dai_contract.balanceOf(consumer_wallet.address) == consumer_dai_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert consumer_bpt_balance - bpt_event[0].args.bptAmount == bpool.balanceOf(
        consumer_wallet.address
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + consumer_dt_balance == erc20_token.balanceOf(
        consumer_wallet.address
    )
    assert (
        side_staking.get_data_token_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)
    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # * Tests Ocean and market fees were accounted for
    assert bpool.opf_fee() == web3.toWei("0.001", "ether")
    assert bpool.get_swap_fee() == swap_market_fee
    assert (bpool.community_fee(erc20_token.address) > 0) is True
    assert (bpool.community_fee(dai_contract.address) > 0) is True
    assert (bpool.market_fee(erc20_token.address) > 0) is True
    assert (bpool.market_fee(dai_contract.address) > 0) is True
