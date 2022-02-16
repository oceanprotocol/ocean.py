#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.bpool import BPool
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721NFT
from ocean_lib.models.models_structures import CreateErc20Data, PoolData
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei, from_wei
from tests.resources.helper_functions import (
    approx_from_wei,
    deploy_erc721_erc20,
    get_address_of_type,
)
import random
import math
import pytest
from time import time


def _deploy_erc721_token(config, web3, factory_deployer_wallet, manager_wallet):
    erc721_nft = deploy_erc721_erc20(web3, config, factory_deployer_wallet)

    erc721_nft.add_to_725_store_list(manager_wallet.address, factory_deployer_wallet)
    erc721_nft.add_to_create_erc20_list(manager_wallet.address, factory_deployer_wallet)
    erc721_nft.add_to_metadata_list(manager_wallet.address, factory_deployer_wallet)
    return erc721_nft


def test_pool_ocean(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    another_consumer_wallet,
    publisher_wallet,
    factory_router,
):
    """Tests pool with ocean token and market fee 0.1%"""

    mint_fake_OCEAN(config)

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
    # cap = web3.toWei(randint(1,1000000),"ether")
    cap = to_wei("100000")
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
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    consumer_balance = ocean_contract.balanceOf(consumer_wallet.address)
    initial_ocean_liq_int = random.uniform(0.1, float(from_wei(consumer_balance)))
    ss_OCEAN_init_liquidity = web3.toWei(initial_ocean_liq_int, "ether")
    ocean_contract.approve(
        get_address_of_type(config, "Router"), ss_OCEAN_init_liquidity, consumer_wallet
    )

    ss_DT_vest_amt = web3.toWei(
        random.uniform(0.001, 0.1) * initial_ocean_liq_int, "ether"
    )
    min_vesting_period = factory_router.get_min_vesting_period()
    ss_DT_vested_blocks = random.randint(min_vesting_period, min_vesting_period * 1000)
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
        ocean_contract.balanceOf(consumer_wallet.address) + ss_OCEAN_init_liquidity
        == consumer_balance
    )

    assert approx_from_wei(
        cap - ss_OCEAN_init_liquidity * from_wei(ss_rate),
        erc20_token.balanceOf(side_staking.address),
    )

    assert ocean_contract.balanceOf(bpool.address) == ss_OCEAN_init_liquidity
    ocean_contract.approve(bpool_address, ss_OCEAN_init_liquidity, publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0

    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)

    token_amount_in = web3.toWei(random.uniform(0.01, 1), "ether")

    tx = bpool.swap_exact_amount_in(
        [ocean_contract.address, erc20_address, another_consumer_wallet.address],
        [token_amount_in, to_wei("0.0001"), to_wei("1000000"), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert (erc20_token.balanceOf(publisher_wallet.address) > 0) is True

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
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

    pool_dt_balance = bpool.get_balance(erc20_address)

    max_out_ratio = bpool.get_max_out_ratio()
    # token_amount_out = to_wei("1") if to_wei("1") < pool_dt_balance else pool_dt_balance - 1
    max_out_ratio_limit = to_wei(from_wei(max_out_ratio) * from_wei(pool_dt_balance))

    token_amount_out = (
        to_wei("1") if to_wei("1") < max_out_ratio_limit else max_out_ratio_limit - 1
    )
    # token_amount_out = max_out_ratio_limit

    tx = bpool.swap_exact_amount_out(
        [ocean_contract.address, erc20_address, another_consumer_wallet.address],
        [
            to_wei("1000000"),
            token_amount_out,
            to_wei("1000000"),
            0,
        ],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
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
        == bpool.publish_market_fee(swap_fees_event_args.tokenFees)
    )
    assert dt_market_fee_balance == bpool.publish_market_fee(erc20_token.address)

    # Tests publisher swaps some DT back to Ocean with swapExactAmountIn, check swap custom fees
    assert bpool.is_finalized() is True

    erc20_token.approve(bpool_address, to_wei("1000"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    assert bpool.community_fee(ocean_contract.address) == 0
    assert bpool.community_fee(erc20_address) == 0
    assert bpool.publish_market_fee(erc20_address) == 0

    token_amount_in = to_wei("0.1")

    tx = bpool.swap_exact_amount_in(
        [erc20_address, ocean_contract.address, another_consumer_wallet.address],
        [token_amount_in, to_wei("0.0001"), to_wei("100000"), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert approx_from_wei(
        swap_market_fee * token_amount_in / to_wei(1),
        swap_fees_event_args.marketFeeAmount,
    )

    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dt_balance
    )

    assert approx_from_wei(
        swap_event_args.tokenAmountIn / (to_wei(1) / swap_market_fee),
        swap_fees_event_args.marketFeeAmount,
    )

    assert approx_from_wei(
        swap_event_args.tokenAmountIn / (to_wei(1) / swap_fee),
        swap_fees_event_args.swapFeeAmount,
    )

    # Tests publisher swaps some DT back to Ocean with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, to_wei("1000"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    assert bpool.community_fee(ocean_contract.address) == 0
    assert bpool.community_fee(erc20_address) == 0

    tx = bpool.swap_exact_amount_out(
        [erc20_token.address, ocean_contract.address, another_consumer_wallet.address],
        [to_wei("1000000"), to_wei("0.0001"), to_wei("10000000"), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFees)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
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
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_market_fee))
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_fee))
        == swap_fees_event_args.swapFeeAmount
    )
