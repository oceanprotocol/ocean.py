#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.models.bpool import BPool
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721NFT
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.structures.abi_tuples import CreateErc20Data, PoolData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


def _deploy_erc721_token(config, web3, factory_deployer_wallet, manager_wallet):
    erc721_nft = deploy_erc721_erc20(web3, config, factory_deployer_wallet)

    erc721_nft.add_to_725_store_list(manager_wallet.address, factory_deployer_wallet)
    erc721_nft.add_to_create_erc20_list(manager_wallet.address, factory_deployer_wallet)
    erc721_nft.add_to_metadata_list(manager_wallet.address, factory_deployer_wallet)
    return erc721_nft


@pytest.mark.unit
def test_deploy_erc721_and_manage(
    web3, config, factory_deployer_wallet, consumer_wallet, another_consumer_wallet
):
    """
    Owner deploys a new ERC721 NFT
    """
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    tx = erc721_factory.deploy_erc721_contract(
        (
            "NFT",
            "SYMBOL",
            1,
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            "https://oceanprotocol.com/nft/",
        ),
        factory_deployer_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    event = erc721_factory.get_event_log(
        erc721_factory.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert event

    token_address = event[0].args.newTokenAddress
    erc721_nft = ERC721NFT(web3, token_address)

    assert erc721_nft.balance_of(factory_deployer_wallet.address) == 1

    erc721_nft.add_manager(another_consumer_wallet.address, factory_deployer_wallet)
    erc721_nft.add_to_725_store_list(consumer_wallet.address, factory_deployer_wallet)
    erc721_nft.add_to_create_erc20_list(
        consumer_wallet.address, factory_deployer_wallet
    )
    erc721_nft.add_to_metadata_list(consumer_wallet.address, factory_deployer_wallet)

    permissions = erc721_nft.get_permissions(consumer_wallet.address)

    assert permissions[1] is True
    assert permissions[2] is True
    assert permissions[3] is True


@pytest.mark.unit
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
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
    erc721_nft = _deploy_erc721_token(
        config, web3, factory_deployer_wallet, consumer_wallet
    )

    # Tests consumer deploys a new erc20DT, assigning himself as minter
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

    swap_fee = to_wei("0.001")
    swap_market_fee = to_wei("0.001")

    # Tests consumer calls deployPool(), we then check ocean and market fee"

    initial_ocean_liq = to_wei("10")
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(
        get_address_of_type(config, "Router"), to_wei("10"), consumer_wallet
    )

    pool_data = PoolData(
        [
            to_wei("1"),
            ocean_contract.decimals(),
            initial_ocean_liq,
            2500000,
            initial_ocean_liq,
        ],
        [to_wei("0.001"), to_wei("0.001")],
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
    assert bpool.get_swap_fee() == to_wei("0.001")
    assert bpool.community_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == to_wei("99990")

    assert bpool.calc_pool_in_single_out(
        erc20_address, to_wei("1")
    ) == bpool.calc_pool_in_single_out(
        get_address_of_type(config, "Ocean"), to_wei("1")
    )
    assert bpool.calc_pool_out_single_in(
        erc20_address, to_wei("1")
    ) == bpool.calc_pool_out_single_in(
        get_address_of_type(config, "Ocean"), to_wei("1")
    )
    assert bpool.calc_single_in_pool_out(
        erc20_address, to_wei("1")
    ) == bpool.calc_single_in_pool_out(
        get_address_of_type(config, "Ocean"), to_wei("1")
    )
    assert bpool.calc_single_out_pool_in(
        erc20_address, to_wei("1")
    ) == bpool.calc_single_out_pool_in(
        get_address_of_type(config, "Ocean"), to_wei("1")
    )
    # Tests publisher buys some DT - exactAmountIn

    assert ocean_contract.balanceOf(bpool.address) == to_wei("10")
    ocean_contract.approve(bpool_address, to_wei("10"), publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)

    tx = bpool.swap_exact_amount_in(
        [ocean_contract.address, erc20_address, another_consumer_wallet.address],
        [to_wei("0.1"), to_wei("0.0001"), to_wei("100"), 0],
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

    tx = bpool.swap_exact_amount_out(
        [ocean_contract.address, erc20_address, another_consumer_wallet.address],
        [to_wei("10"), to_wei("1"), to_wei("100"), 0],
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
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
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

    tx = bpool.swap_exact_amount_in(
        [erc20_address, ocean_contract.address, another_consumer_wallet.address],
        [to_wei("0.1"), to_wei("0.0001"), to_wei("100"), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert to_wei("0.0001") == swap_fees_event_args.marketFeeAmount
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
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
        swap_event_args.tokenAmountIn / (to_wei("1") / swap_market_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_fee))
        == swap_fees_event_args.LPFeeAmount
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
        [to_wei("0.1"), to_wei("0.0001"), to_wei("100"), 0],
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
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher adds more liquidity with joinPool() (adding both tokens)

    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    erc20_token.approve(bpool_address, to_wei("1000"), publisher_wallet)

    tx = bpool.join_pool(to_wei("0.01"), [to_wei("50"), to_wei("50")], publisher_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == erc20_token.address
    assert join_pool_event[1].args.tokenIn == ocean_contract.address

    assert to_wei("0.01") == bpool.balanceOf(publisher_wallet.address)
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20_token.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # Tests consumer adds more liquidity with joinswapExternAmountIn (only OCEAN)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_join = side_staking.get_datatoken_balance(erc20_token.address)

    ocean_contract.approve(bpool_address, to_wei("1000"), consumer_wallet)

    tx = bpool.join_swap_extern_amount_in(to_wei("1"), to_wei("0.01"), consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == ocean_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address
    assert join_pool_event[0].args.tokenAmountIn == to_wei("1")
    side_staking_amount_in = ss_contract_dt_balance - erc20_token.balanceOf(
        side_staking.address
    )

    assert (
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_join - side_staking_amount_in
    )

    assert join_pool_event[1].args.tokenAmountIn == side_staking_amount_in

    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert bpt_event[0].args.bptAmount + ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    # Tests consumer removes liquidity with ExitPool, receiving both tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_ocean_balance = ocean_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    tx = bpool.exit_pool(
        to_wei("0.5"), [to_wei("0.001"), to_wei("0.001")], consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert (
        bpool.balanceOf(consumer_wallet.address) + to_wei("0.5") == consumer_bpt_balance
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)

    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # Tests consumer removes liquidity with exitswapPoolAmountIn, receiving only OCEAN tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_ocean_balance = ocean_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        to_wei("0.05"), to_wei("0.005"), consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )

    assert consumer_bpt_balance == bpool.balanceOf(consumer_wallet.address) + to_wei(
        "0.05"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.05"
    )

    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # consumer removes liquidity with exitswapPoolAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_ocean_balance = ocean_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        to_wei("0.05"), to_wei("0.005"), consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert (
        bpool.balanceOf(consumer_wallet.address)
        == consumer_bpt_balance - bpt_event[0].args.bptAmount
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )
    assert consumer_bpt_balance == bpool.balanceOf(consumer_wallet.address) + to_wei(
        "0.05"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.05"
    )
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # Tests no ocean and market fees were accounted for
    assert bpool.opc_fee() == 0
    assert bpool.get_swap_fee() == swap_market_fee
    assert bpool.community_fee(ocean_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert (bpool.publish_market_fee(erc20_token.address) > 0) is True
    assert (bpool.publish_market_fee(ocean_contract.address) > 0) is True


@pytest.mark.unit
def test_pool_dai(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    another_consumer_wallet,
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
        consumer_wallet.address, to_wei("20"), factory_deployer_wallet
    )
    dai_contract.transfer(
        publisher_wallet.address, to_wei("20"), factory_deployer_wallet
    )

    erc721_nft = _deploy_erc721_token(
        config, web3, factory_deployer_wallet, consumer_wallet
    )
    swap_fee = to_wei("0.001")
    swap_market_fee = to_wei("0.001")

    # Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = to_wei("1000")
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

    # Tests consumer calls deployPool(), we then check dai and market fee"

    initial_dai_liq = to_wei("10")

    dai_contract.approve(
        get_address_of_type(config, "Router"), to_wei("10"), consumer_wallet
    )

    pool_data = PoolData(
        [
            to_wei("1"),
            dai_contract.decimals(),
            initial_dai_liq,
            2500000,
            initial_dai_liq,
        ],
        [to_wei("0.001"), to_wei("0.001")],
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
    assert bpool.is_finalized() is True
    assert bpool.opc_fee() == to_wei("0.001")
    assert bpool.get_swap_fee() == to_wei("0.001")
    assert bpool.community_fee(dai_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(dai_contract.address) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == to_wei("990")

    assert bpool.calc_pool_in_single_out(
        erc20_address, to_wei("1")
    ) == bpool.calc_pool_in_single_out(dai_contract.address, to_wei("1"))
    assert bpool.calc_pool_out_single_in(
        erc20_address, to_wei("1")
    ) == bpool.calc_pool_out_single_in(dai_contract.address, to_wei("1"))
    assert bpool.calc_single_in_pool_out(
        erc20_address, to_wei("1")
    ) == bpool.calc_single_in_pool_out(dai_contract.address, to_wei("1"))
    assert bpool.calc_single_out_pool_in(
        erc20_address, to_wei("1")
    ) == bpool.calc_single_out_pool_in(dai_contract.address, to_wei("1"))
    # Tests publisher buys some DT - exactAmountIn

    assert dai_contract.balanceOf(bpool.address) == to_wei("10")
    dai_contract.approve(bpool_address, to_wei("10"), publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)

    tx = bpool.swap_exact_amount_in(
        [dai_contract.address, erc20_address, another_consumer_wallet.address],
        [to_wei("0.1"), to_wei("0.0001"), to_wei("100"), 0],
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
        dai_contract.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dai_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    # Tests publisher buys some DT - exactAmountOut
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)
    dai_market_fee_balance = bpool.publish_market_fee(dai_contract.address)

    tx = bpool.swap_exact_amount_out(
        [dai_contract.address, erc20_address, another_consumer_wallet.address],
        [to_wei("10"), to_wei("1"), to_wei("100"), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
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
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert swap_fees_event_args.tokenFeeAddress == dai_contract.address
    assert (
        dai_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
    )
    assert dt_market_fee_balance == bpool.publish_market_fee(erc20_token.address)

    # Tests publisher swaps some DT back to DAI with swapExactAmountIn, check swap custom fees
    assert bpool.is_finalized() is True

    erc20_token.approve(bpool_address, to_wei("1000"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_in(
        [erc20_address, dai_contract.address, another_consumer_wallet.address],
        [to_wei("0.1"), to_wei("0.0001"), to_wei("100"), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert to_wei("0.0001") == swap_fees_event_args.marketFeeAmount
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
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
        swap_event_args.tokenAmountIn / (to_wei("1") / swap_market_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher swaps some DT back to dai with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, to_wei("1000"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        [erc20_token.address, dai_contract.address, another_consumer_wallet.address],
        [to_wei("0.1"), to_wei("0.0001"), to_wei("100"), 0],
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
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
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
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_market_fee))
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher adds more liquidity with joinPool() (adding both tokens)

    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    dai_contract.approve(bpool_address, to_wei(1000), publisher_wallet)
    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)

    tx = bpool.join_pool(to_wei("0.01"), [to_wei("50"), to_wei("50")], publisher_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == erc20_token.address
    assert join_pool_event[1].args.tokenIn == dai_contract.address

    assert to_wei("0.01") == bpool.balanceOf(publisher_wallet.address)
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20_token.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # Tests consumer adds more liquidity with joinswapExternAmountIn (only OCEAN)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_join = side_staking.get_datatoken_balance(erc20_token.address)

    dai_contract.approve(bpool_address, to_wei(1000), consumer_wallet)

    tx = bpool.join_swap_extern_amount_in(to_wei(1), to_wei("0.01"), consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == dai_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address
    assert join_pool_event[0].args.tokenAmountIn == to_wei(1)
    side_staking_amount_in = ss_contract_dt_balance - erc20_token.balanceOf(
        side_staking.address
    )

    assert (
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_join - side_staking_amount_in
    )

    assert join_pool_event[1].args.tokenAmountIn == side_staking_amount_in

    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert bpt_event[0].args.bptAmount + ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    # Tests consumer removes liquidity with ExitPool, receiving both tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    tx = bpool.exit_pool(
        to_wei("0.5"), [to_wei("0.001"), to_wei("0.001")], consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert (
        bpool.balanceOf(consumer_wallet.address) + to_wei("0.5") == consumer_bpt_balance
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)

    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # Tests consumer removes liquidity with exitswapPoolAmountIn, receiving only dai tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        to_wei("0.05"), to_wei("0.005"), consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )

    assert consumer_bpt_balance == bpool.balanceOf(consumer_wallet.address) + to_wei(
        "0.05"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.05"
    )

    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # consumer removes liquidity with exitswapPoolAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        to_wei("0.05"), to_wei("0.005"), consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert (
        bpool.balanceOf(consumer_wallet.address)
        == consumer_bpt_balance - bpt_event[0].args.bptAmount
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )
    assert consumer_bpt_balance == bpool.balanceOf(consumer_wallet.address) + to_wei(
        "0.05"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.05"
    )
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # Tests Ocean and market fees were accounted for
    assert bpool.opc_fee() == to_wei("0.001")
    assert bpool.get_swap_fee() == swap_market_fee
    assert (bpool.community_fee(erc20_token.address) > 0) is True
    assert (bpool.community_fee(dai_contract.address) > 0) is True
    assert (bpool.publish_market_fee(erc20_token.address) > 0) is True
    assert (bpool.publish_market_fee(dai_contract.address) > 0) is True


def test_pool_usdc(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    another_consumer_wallet,
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
        consumer_wallet.address, to_wei("20"), factory_deployer_wallet
    )
    usdc_contract.transfer(
        publisher_wallet.address, to_wei("20"), factory_deployer_wallet
    )

    erc721_nft = _deploy_erc721_token(
        config, web3, factory_deployer_wallet, consumer_wallet
    )
    swap_fee = to_wei("0.001")
    swap_market_fee = to_wei("0.001")

    # Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = to_wei("1000")
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

    # Tests consumer calls deployPool(), we then check USDC and market fee"

    initial_usdc_liq = int(1e6) * 880  # 880 USDC

    usdc_contract.approve(
        get_address_of_type(config, "Router"), to_wei(100), consumer_wallet
    )

    pool_data = PoolData(
        [
            to_wei(1),
            usdc_contract.decimals(),
            initial_usdc_liq,
            2500000,
            initial_usdc_liq,
        ],
        [to_wei("0.001"), to_wei("0.001")],
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
    assert bpool.is_finalized() is True
    assert bpool.opc_fee() == to_wei("0.001")
    assert bpool.get_swap_fee() == to_wei("0.001")
    assert bpool.community_fee(usdc_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(usdc_contract.address) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == to_wei(120)

    assert bpool.calc_pool_in_single_out(erc20_address, to_wei(1)) // int(
        1e12
    ) == bpool.calc_pool_in_single_out(usdc_contract.address, int(1e6)) // int(1e12)
    assert bpool.calc_pool_out_single_in(
        erc20_address, to_wei(1)
    ) == bpool.calc_pool_out_single_in(usdc_contract.address, int(1e6))
    assert bpool.calc_single_in_pool_out(erc20_address, to_wei(10)) // int(
        1e12
    ) == bpool.calc_single_in_pool_out(usdc_contract.address, to_wei(10))
    assert bpool.calc_single_out_pool_in(erc20_address, to_wei(10)) // int(
        1e12
    ) == bpool.calc_single_out_pool_in(usdc_contract.address, to_wei(10))
    # Tests publisher buys some DT - exactAmountIn

    assert usdc_contract.balanceOf(bpool.address) == initial_usdc_liq
    usdc_contract.approve(bpool_address, to_wei(10), publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)

    tx = bpool.swap_exact_amount_in(
        [usdc_contract.address, erc20_address, another_consumer_wallet.address],
        [int(1e7), to_wei(1), to_wei(5), 0],
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
        usdc_contract.balanceOf(publisher_wallet.address)
        + swap_event_args.tokenAmountIn
        == publisher_usdc_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    # Tests publisher buys some DT - exactAmountOut
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)
    usdc_market_fee_balance = bpool.publish_market_fee(usdc_contract.address)

    tx = bpool.swap_exact_amount_out(
        [usdc_contract.address, erc20_address, another_consumer_wallet.address],
        [to_wei(10), to_wei(1), to_wei(100), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
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
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert swap_fees_event_args.tokenFeeAddress == usdc_contract.address
    assert (
        usdc_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
    )
    assert dt_market_fee_balance == bpool.publish_market_fee(erc20_token.address)

    # Tests publisher swaps some DT back to USDC with swapExactAmountIn, check swap custom fees
    assert bpool.is_finalized() is True

    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_in(
        [erc20_address, usdc_contract.address, another_consumer_wallet.address],
        [to_wei("0.1"), int(1e4), int(2**256 - 1), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert to_wei("0.0001") == swap_fees_event_args.marketFeeAmount
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
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
        swap_event_args.tokenAmountIn / (to_wei(1) / swap_market_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher swaps some DT back to USDC with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        [erc20_token.address, usdc_contract.address, another_consumer_wallet.address],
        [to_wei(10), int(1e6), to_wei(1000000000000000), 0],
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
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
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
        round(swap_event_args.tokenAmountIn / (to_wei(1) / swap_market_fee))
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher adds more liquidity with joinPool() (adding both tokens)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    usdc_contract.approve(bpool_address, to_wei("1000"), publisher_wallet)
    erc20_token.approve(bpool_address, to_wei("1000"), publisher_wallet)

    tx = bpool.join_pool(to_wei("0.01"), [to_wei("50"), to_wei("50")], publisher_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == erc20_token.address
    assert join_pool_event[1].args.tokenIn == usdc_contract.address

    assert to_wei("0.01") == bpool.balanceOf(publisher_wallet.address)
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20_token.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # Tests consumer adds more liquidity with joinswapExternAmountIn (only OCEAN)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_join = side_staking.get_datatoken_balance(erc20_token.address)

    usdc_contract.approve(bpool_address, to_wei(1000), consumer_wallet)

    tx = bpool.join_swap_extern_amount_in(int(1e6), to_wei("0.01"), consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == usdc_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address
    assert join_pool_event[0].args.tokenAmountIn == int(1e6)
    side_staking_amount_in = ss_contract_dt_balance - erc20_token.balanceOf(
        side_staking.address
    )

    assert (
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_join - side_staking_amount_in
    )

    assert join_pool_event[1].args.tokenAmountIn == side_staking_amount_in

    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert bpt_event[0].args.bptAmount + ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    # Tests consumer removes liquidity with ExitPool, receiving both tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    tx = bpool.exit_pool(to_wei("0.1"), [to_wei("0.1"), int(1e5)], consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert (
        bpool.balanceOf(consumer_wallet.address) + to_wei("0.1") == consumer_bpt_balance
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)

    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # Tests consumer removes liquidity with exitswapPoolAmountIn, receiving only USDC tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(to_wei("0.1"), int(1e5), consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )

    assert consumer_bpt_balance == bpool.balanceOf(consumer_wallet.address) + to_wei(
        "0.1"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.1"
    )

    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # consumer removes liquidity with exitswapPoolAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(to_wei("0.1"), int(1e6), consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert (
        bpool.balanceOf(consumer_wallet.address)
        == consumer_bpt_balance - bpt_event[0].args.bptAmount
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )
    assert consumer_bpt_balance == bpool.balanceOf(consumer_wallet.address) + to_wei(
        "0.1"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.1"
    )
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # Tests Ocean and market fees were accounted for
    assert bpool.opc_fee() == to_wei("0.001")
    assert bpool.get_swap_fee() == swap_market_fee
    assert (bpool.community_fee(erc20_token.address) > 0) is True
    assert (bpool.community_fee(usdc_contract.address) > 0) is True
    assert (bpool.publish_market_fee(erc20_token.address) > 0) is True
    assert (bpool.publish_market_fee(usdc_contract.address) > 0) is True


@pytest.mark.unit
def test_pool_usdc_flexible(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    publisher_wallet,
    another_consumer_wallet,
    factory_router,
):
    """Tests pool with NO ocean token (USDC 6 decimals) and market fee 0.1% flexible opc fee"""
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
    usdc_contract = ERC20Token(
        address=get_address_of_type(config, "MockUSDC"), web3=web3
    )
    usdc_contract.transfer(
        consumer_wallet.address, to_wei("20"), factory_deployer_wallet
    )
    usdc_contract.transfer(
        publisher_wallet.address, to_wei("20"), factory_deployer_wallet
    )

    erc721_nft = _deploy_erc721_token(
        config, web3, factory_deployer_wallet, consumer_wallet
    )
    swap_fee = to_wei("0.001")
    swap_market_fee = to_wei("0.001")

    # Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = to_wei(1000)
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

    # Tests consumer calls deployPool(), we then check USDC and market fee"

    initial_usdc_liq = int(1e6) * 880  # 880 USDC  # 880 USDC

    usdc_contract.approve(
        get_address_of_type(config, "Router"), to_wei(10), consumer_wallet
    )

    pool_data = PoolData(
        [
            to_wei(1),
            usdc_contract.decimals(),
            initial_usdc_liq,
            2500000,
            initial_usdc_liq,
        ],
        [to_wei("0.001"), to_wei("0.001")],
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

    assert bpool.is_finalized() is True
    assert bpool.get_swap_fee() == to_wei("0.001")
    assert bpool.community_fee(usdc_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(usdc_contract.address) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == to_wei(120)
    assert bpool.calc_pool_in_single_out(erc20_address, to_wei(1)) // int(
        1e12
    ) == bpool.calc_pool_in_single_out(usdc_contract.address, int(1e6)) // int(1e12)
    assert bpool.calc_pool_out_single_in(
        erc20_address, to_wei(1)
    ) == bpool.calc_pool_out_single_in(usdc_contract.address, int(1e6))
    assert bpool.calc_single_in_pool_out(erc20_address, to_wei(10)) // int(
        1e12
    ) == bpool.calc_single_in_pool_out(usdc_contract.address, to_wei(10))
    assert bpool.calc_single_out_pool_in(erc20_address, to_wei(10)) // int(
        1e12
    ) == bpool.calc_single_out_pool_in(usdc_contract.address, to_wei(10))
    # Tests publisher buys some DT - exactAmountIn

    assert usdc_contract.balanceOf(bpool.address) == initial_usdc_liq
    usdc_contract.approve(bpool_address, to_wei(10), publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)

    tx = bpool.swap_exact_amount_in(
        [usdc_contract.address, erc20_address, another_consumer_wallet.address],
        [int(1e7), to_wei(1), to_wei(5), 0],
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
        usdc_contract.balanceOf(publisher_wallet.address)
        + swap_event_args.tokenAmountIn
        == publisher_usdc_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    # Tests publisher buys some DT - exactAmountOut
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)
    usdc_market_fee_balance = bpool.publish_market_fee(usdc_contract.address)

    tx = bpool.swap_exact_amount_out(
        [usdc_contract.address, erc20_address, another_consumer_wallet.address],
        [to_wei(10), to_wei(1), to_wei(100), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
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
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert swap_fees_event_args.tokenFeeAddress == usdc_contract.address
    assert (
        usdc_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
    )
    assert dt_market_fee_balance == bpool.publish_market_fee(erc20_token.address)

    # Tests publisher swaps some DT back to USDC with swapExactAmountIn, check swap custom fees
    assert bpool.is_finalized() is True

    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_in(
        [erc20_address, usdc_contract.address, another_consumer_wallet.address],
        [to_wei("0.1"), int(1e4), int(2**256 - 1), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert to_wei("0.0001") == swap_fees_event_args.marketFeeAmount
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
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
        swap_event_args.tokenAmountIn / (to_wei(1) / swap_market_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher swaps some DT back to USDC with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        [erc20_token.address, usdc_contract.address, another_consumer_wallet.address],
        [to_wei(10), int(1e6), to_wei(1000000000000000), 0],
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
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
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
        round(swap_event_args.tokenAmountIn / (to_wei(1) / swap_market_fee))
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher adds more liquidity with joinPool() (adding both tokens)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    usdc_contract.approve(bpool_address, to_wei(1000), publisher_wallet)
    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)

    tx = bpool.join_pool(to_wei("0.01"), [to_wei("50"), to_wei("50")], publisher_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == erc20_token.address
    assert join_pool_event[1].args.tokenIn == usdc_contract.address

    assert to_wei("0.01") == bpool.balanceOf(publisher_wallet.address)
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20_token.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # Tests consumer adds more liquidity with joinswapExternAmountIn (only OCEAN)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_join = side_staking.get_datatoken_balance(erc20_token.address)

    usdc_contract.approve(bpool_address, to_wei(1000), consumer_wallet)

    tx = bpool.join_swap_extern_amount_in(int(1e6), to_wei("0.01"), consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == usdc_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address
    assert join_pool_event[0].args.tokenAmountIn == int(1e6)
    side_staking_amount_in = ss_contract_dt_balance - erc20_token.balanceOf(
        side_staking.address
    )

    assert (
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_join - side_staking_amount_in
    )

    assert join_pool_event[1].args.tokenAmountIn == side_staking_amount_in

    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert bpt_event[0].args.bptAmount + ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    # Tests consumer removes liquidity with ExitPool, receiving both tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    tx = bpool.exit_pool(to_wei("0.1"), [to_wei("0.1"), int(1e5)], consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert (
        bpool.balanceOf(consumer_wallet.address) + to_wei("0.1") == consumer_bpt_balance
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)

    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # Tests consumer removes liquidity with exitswapPoolAmountIn, receiving only USDC tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(to_wei("0.1"), int(1e5), consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )

    assert consumer_bpt_balance == bpool.balanceOf(consumer_wallet.address) + to_wei(
        "0.1"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.1"
    )

    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # consumer removes liquidity with exitswapPoolAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_usdc_balance = usdc_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(to_wei("0.1"), int(1e6), consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert (
        bpool.balanceOf(consumer_wallet.address)
        == consumer_bpt_balance - bpt_event[0].args.bptAmount
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )
    assert consumer_bpt_balance == bpool.balanceOf(consumer_wallet.address) + to_wei(
        "0.1"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.1"
    )
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # Tests Ocean and market fees were accounted for
    assert bpool.opc_fee() == to_wei("0.001")
    assert bpool.get_swap_fee() == swap_market_fee
    assert (bpool.community_fee(erc20_token.address) > 0) is True
    assert (bpool.community_fee(usdc_contract.address) > 0) is True
    assert (bpool.publish_market_fee(erc20_token.address) > 0) is True
    assert (bpool.publish_market_fee(usdc_contract.address) > 0) is True


@pytest.mark.unit
def test_pool_dai_flexible(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    publisher_wallet,
    another_consumer_wallet,
    factory_router,
):
    """Tests pool with NO ocean token (DAI 18 decimals) and market fee 0.1% and flexible opc fee"""
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
    dai_contract = ERC20Token(address=get_address_of_type(config, "MockDAI"), web3=web3)
    dai_contract.transfer(
        consumer_wallet.address, to_wei("20"), factory_deployer_wallet
    )
    dai_contract.transfer(
        publisher_wallet.address, to_wei("20"), factory_deployer_wallet
    )

    erc721_nft = _deploy_erc721_token(
        config, web3, factory_deployer_wallet, consumer_wallet
    )
    swap_fee = to_wei("0.001")
    swap_market_fee = to_wei("0.001")

    # Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = to_wei(1000)
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

    # Tests consumer calls deployPool(), we then check DAI and market fee"

    initial_dai_liq = to_wei(10)

    dai_contract.approve(
        get_address_of_type(config, "Router"), to_wei(10), consumer_wallet
    )

    pool_data = PoolData(
        [to_wei(1), 18, initial_dai_liq, 2500000, initial_dai_liq],
        [to_wei("0.001"), to_wei("0.001")],
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

    assert bpool.is_finalized() is True
    assert bpool.get_swap_fee() == to_wei("0.001")
    assert bpool.community_fee(dai_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(dai_contract.address) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == to_wei(990)

    assert bpool.calc_pool_in_single_out(
        erc20_address, to_wei(1)
    ) == bpool.calc_pool_in_single_out(dai_contract.address, to_wei(1))
    assert bpool.calc_pool_out_single_in(
        erc20_address, to_wei(1)
    ) == bpool.calc_pool_out_single_in(dai_contract.address, to_wei(1))
    assert bpool.calc_single_in_pool_out(
        erc20_address, to_wei(1)
    ) == bpool.calc_single_in_pool_out(dai_contract.address, to_wei(1))
    assert bpool.calc_single_out_pool_in(
        erc20_address, to_wei(1)
    ) == bpool.calc_single_out_pool_in(dai_contract.address, to_wei(1))
    # Tests publisher buys some DT - exactAmountIn

    assert dai_contract.balanceOf(bpool.address) == to_wei(10)
    dai_contract.approve(bpool_address, to_wei(10), publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)

    tx = bpool.swap_exact_amount_in(
        [dai_contract.address, erc20_address, another_consumer_wallet.address],
        [to_wei("0.1"), to_wei("0.0001"), to_wei("100"), 0],
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
        dai_contract.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn
        == publisher_dai_balance
    )
    assert (
        erc20_token.balanceOf(publisher_wallet.address)
        == publisher_dt_balance + swap_event_args.tokenAmountOut
    )

    # Tests publisher buys some DT - exactAmountOut
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)
    dai_market_fee_balance = bpool.publish_market_fee(dai_contract.address)

    tx = bpool.swap_exact_amount_out(
        [dai_contract.address, erc20_address, another_consumer_wallet.address],
        [to_wei(10), to_wei(1), to_wei(100), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
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
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert swap_fees_event_args.tokenFeeAddress == dai_contract.address
    assert (
        dai_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
    )
    assert dt_market_fee_balance == bpool.publish_market_fee(erc20_token.address)

    # Tests publisher swaps some DT back to DAI with swapExactAmountIn, check swap custom fees
    assert bpool.is_finalized() is True

    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_in(
        [erc20_address, dai_contract.address, another_consumer_wallet.address],
        [to_wei("0.1"), to_wei("0.0001"), to_wei("100"), 0],
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert to_wei("0.0001") == swap_fees_event_args.marketFeeAmount
    assert (
        dt_market_fee_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
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
        swap_event_args.tokenAmountIn / (to_wei(1) / swap_market_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher swaps some DT back to DAI with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        [erc20_token.address, dai_contract.address, another_consumer_wallet.address],
        [to_wei("0.1"), to_wei("0.0001"), to_wei(100), 0],
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
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
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
        round(swap_event_args.tokenAmountIn / (to_wei(1) / swap_market_fee))
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher adds more liquidity with joinPool() (adding both tokens)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    dai_contract.approve(bpool_address, to_wei(1000), publisher_wallet)
    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)

    tx = bpool.join_pool(to_wei("0.01"), [to_wei("50"), to_wei("50")], publisher_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == erc20_token.address
    assert join_pool_event[1].args.tokenIn == dai_contract.address

    assert to_wei("0.01") == bpool.balanceOf(publisher_wallet.address)
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20_token.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # Tests consumer adds more liquidity with joinswapExternAmountIn (only OCEAN)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_join = side_staking.get_datatoken_balance(erc20_token.address)

    dai_contract.approve(bpool_address, to_wei("1000"), consumer_wallet)

    tx = bpool.join_swap_extern_amount_in(to_wei("1"), to_wei("0.01"), consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == dai_contract.address
    assert join_pool_event[1].args.tokenIn == erc20_token.address
    assert join_pool_event[0].args.tokenAmountIn == to_wei(1)
    side_staking_amount_in = ss_contract_dt_balance - erc20_token.balanceOf(
        side_staking.address
    )

    assert (
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_join - side_staking_amount_in
    )

    assert join_pool_event[1].args.tokenAmountIn == side_staking_amount_in

    assert ss_contract_dt_balance - join_pool_event[
        1
    ].args.tokenAmountIn == erc20_token.balanceOf(side_staking.address)

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert bpt_event[0].args.bptAmount + ss_contract_bpt_balance == bpool.balanceOf(
        side_staking.address
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    # Tests consumer removes liquidity with ExitPool, receiving both tokens
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    tx = bpool.exit_pool(
        to_wei("0.5"), [to_wei("0.001"), to_wei("0.001")], consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert (
        bpool.balanceOf(consumer_wallet.address) + to_wei("0.5") == consumer_bpt_balance
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)

    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # Tests consumer removes liquidity with exitswapPoolAmountIn, receiving only DAI tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        to_wei("0.05"), to_wei("0.005"), consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )

    assert consumer_bpt_balance == bpool.balanceOf(consumer_wallet.address) + to_wei(
        "0.05"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.05"
    )

    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # consumer removes liquidity with exitswapPoolAmountIn, receiving only DT tokens

    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_dai_balance = dai_contract.balanceOf(consumer_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)
    consumer_bpt_balance = bpool.balanceOf(consumer_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        to_wei("0.05"), to_wei("0.005"), consumer_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert erc20_token.balanceOf(consumer_wallet.address) == consumer_dt_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert (
        bpool.balanceOf(consumer_wallet.address)
        == consumer_bpt_balance - bpt_event[0].args.bptAmount
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
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
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )
    assert consumer_bpt_balance == bpool.balanceOf(consumer_wallet.address) + to_wei(
        "0.05"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.05"
    )
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # Tests Ocean and market fees were accounted for
    assert bpool.opc_fee() == to_wei("0.001")
    assert bpool.get_swap_fee() == swap_market_fee
    assert (bpool.community_fee(erc20_token.address) > 0) is True
    assert (bpool.community_fee(dai_contract.address) > 0) is True
    assert (bpool.publish_market_fee(erc20_token.address) > 0) is True
    assert (bpool.publish_market_fee(dai_contract.address) > 0) is True
