#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List

import pytest

from ocean_lib.models.bpool import BPool
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721NFT
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet
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
        name="NFT",
        symbol="SYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=factory_deployer_wallet.address,
        from_wallet=factory_deployer_wallet,
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


def distribute_base_token(
    base_token: ERC20Token,
    recipients: List[str],
    from_wallet: Wallet,
    amount_in_ether: int = 20,
) -> ERC20Token:
    for recipient in recipients:
        base_token.transfer(
            recipient,
            to_wei(amount_in_ether, base_token.decimals()),
            from_wallet,
        )


@pytest.mark.unit
@pytest.mark.parametrize("base_token_name", ["Ocean", "MockDAI"])
def test_pool(
    web3,
    config,
    factory_deployer_wallet,
    consumer_wallet,
    another_consumer_wallet,
    publisher_wallet,
    base_token_name: str,
):
    """
    Tests pool with OCEAN, DAI, and USDC as base token and market fee 0.1%
    OCEAN is an approved base token with 18 decimals (OPC Fee = 0.1%)
    DAI is a non-approved base token with 18 decimals (OPC Fee = 0.2%)
    USDC is a non-approved base token with 6 decimals (OPC Fee = 0.2%)
    """
    base_token = ERC20Token(web3, get_address_of_type(config, base_token_name))
    distribute_base_token(
        base_token=base_token,
        recipients=[publisher_wallet.address, consumer_wallet.address],
        from_wallet=factory_deployer_wallet,
    )

    factory_router = FactoryRouter(web3, get_address_of_type(config, "Router"))
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
    erc721_nft = _deploy_erc721_token(
        config, web3, factory_deployer_wallet, publisher_wallet
    )

    # Datatoken cap is hardcoded to MAX_WEI in contract regardles of what is passed.
    cap_doesnt_matter = to_wei("100000")

    # Tests publisher deploys a new erc20 datatoken
    tx = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=factory_deployer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=cap_doesnt_matter,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=publisher_wallet,
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

    assert erc20_token.get_permissions(publisher_wallet.address)[0] is True

    # TODO: Consider checking order fee amounts are correct

    # Tests publisher calls deployPool(), we then check base token balance and fees

    lp_swap_fee = to_wei("0.001")
    publish_market_swap_fee = to_wei("0.001")
    consume_market_swap_fee = to_wei(
        0
    )  # TODO: Increase consume market swap fee to non-zero amount

    initial_base_token_amount = to_wei("10")
    base_token.approve(factory_router.address, to_wei("10"), publisher_wallet)

    tx = erc20_token.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=base_token.decimals(),
        vesting_amount=initial_base_token_amount,
        vesting_blocks=2500000,
        base_token_amount=initial_base_token_amount,
        lp_swap_fee_amount=lp_swap_fee,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        ss_contract=side_staking.address,
        base_token_address=base_token.address,
        base_token_sender=publisher_wallet.address,
        publisher_address=publisher_wallet.address,
        publish_market_swap_fee_collector=publisher_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=publisher_wallet,
    )
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

    # Verify fee collectors are configured correctly
    assert bpool.get_opc_collector() == factory_router.opc_collector()
    assert bpool.get_opc_collector() == get_address_of_type(
        config, "OPFCommunityFeeCollector"
    )
    assert bpool.get_publish_market_collector() == publisher_wallet.address

    # Verify fees are configured correctly
    if factory_router.is_approved_token(base_token.address):
        assert bpool.opc_fee() == to_wei("0.001")
    else:
        assert bpool.opc_fee() == to_wei("0.002")
    assert bpool.opc_fee() == factory_router.get_opc_fee(base_token.address)
    assert bpool.get_swap_fee() == lp_swap_fee
    assert bpool.get_market_fee() == publish_market_swap_fee

    # Verify 0 fees have been collected so far
    assert bpool.community_fee(base_token.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(base_token.address) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0
    # TODO: Assert that consume market fee collector also has 0.

    assert (
        erc20_token.balanceOf(side_staking.address)
        == MAX_UINT256 - initial_base_token_amount
    )

    assert bpool.calc_pool_in_single_out(
        erc20_address, to_wei("1")
    ) == bpool.calc_pool_in_single_out(base_token.address, to_wei("1"))
    assert bpool.calc_pool_out_single_in(
        erc20_address, to_wei("1")
    ) == bpool.calc_pool_out_single_in(base_token.address, to_wei("1"))
    assert bpool.calc_single_in_pool_out(
        erc20_address, to_wei("1")
    ) == bpool.calc_single_in_pool_out(base_token.address, to_wei("1"))
    assert bpool.calc_single_out_pool_in(
        erc20_address, to_wei("1")
    ) == bpool.calc_single_out_pool_in(base_token.address, to_wei("1"))

    # Tests consumer buys some DT - exactAmountIn

    assert base_token.balanceOf(bpool.address) == to_wei("10")
    base_token.approve(bpool_address, to_wei("10"), consumer_wallet)

    assert erc20_token.balanceOf(consumer_wallet.address) == 0
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_bt_balance = base_token.balanceOf(consumer_wallet.address)

    tx = bpool.swap_exact_amount_in(
        token_in=base_token.address,
        token_out=erc20_address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        token_amount_in=to_wei("0.1"),
        min_amount_out=to_wei("0.0001"),
        max_price=to_wei("100"),
        consume_market_swap_fee_amount=consume_market_swap_fee,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert (erc20_token.balanceOf(consumer_wallet.address) > 0) is True

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_event_args = swap_fee_event[0].args

    # Check swap balances
    assert (
        base_token.balanceOf(consumer_wallet.address) + swap_event_args.tokenAmountIn
        == consumer_bt_balance
    )
    assert (
        erc20_token.balanceOf(consumer_wallet.address)
        == consumer_dt_balance + swap_event_args.tokenAmountOut
    )

    # TODO: Assert that appropraiate amount of fees were sent to LPs, Publish market, community and consume market.

    # Tests consumer buys some DT - exactAmountOut
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_bt_balance = base_token.balanceOf(consumer_wallet.address)
    publish_market_fee_dt_balance = bpool.publish_market_fee(erc20_token.address)
    publish_market_fee_bt_balance = bpool.publish_market_fee(base_token.address)
    opc_fee_dt_balance = bpool.community_fee(erc20_token.address)
    opc_fee_bt_balance = bpool.community_fee(base_token.address)

    tx = bpool.swap_exact_amount_out(
        token_in=base_token.address,
        token_out=erc20_address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        max_amount_in=to_wei(10),
        token_amount_out=to_wei(1),
        max_price=to_wei(100),
        consume_market_swap_fee_amount=consume_market_swap_fee,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fee_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_event_args = swap_fee_event[0].args

    assert (
        base_token.balanceOf(consumer_wallet.address) + swap_event_args.tokenAmountIn
        == consumer_bt_balance
    )
    assert (
        erc20_token.balanceOf(consumer_wallet.address)
        == consumer_dt_balance + swap_event_args.tokenAmountOut
    )

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert swap_fees_event_args.tokenFeeAddress == base_token.address
    assert (
        publish_market_fee_bt_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
    )
    assert publish_market_fee_dt_balance == bpool.publish_market_fee(
        erc20_token.address
    )

    # Tests consumer swaps datatokens back to base tokens with swapExactAmountIn, check swap fees
    assert bpool.is_finalized() is True

    erc20_token.approve(bpool_address, to_wei("1000"), consumer_wallet)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    publish_market_fee_dt_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_in(
        token_in=erc20_address,
        token_out=base_token.address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        token_amount_in=to_wei("0.1"),
        min_amount_out=to_wei("0.0001"),
        max_price=to_wei("100"),
        consume_market_swap_fee_amount=consume_market_swap_fee,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

    assert to_wei("0.0001") == swap_fees_event_args.marketFeeAmount
    assert (
        publish_market_fee_dt_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(consumer_wallet.address) + swap_event_args.tokenAmountIn
        == consumer_dt_balance
    )
    assert (
        swap_event_args.tokenAmountIn / (to_wei("1") / publish_market_swap_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / lp_swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests consumer swaps datatokens back to base tokens with swapExactAmountOut, check swap fees

    erc20_token.approve(bpool_address, to_wei("1000"), consumer_wallet)
    consumer_dt_balance = erc20_token.balanceOf(consumer_wallet.address)
    consumer_bt_balance = base_token.balanceOf(consumer_wallet.address)
    publish_market_fee_dt_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        token_in=erc20_address,
        token_out=base_token.address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        max_amount_in=to_wei("0.1"),
        token_amount_out=to_wei("0.0001"),
        max_price=to_wei(100),
        consume_market_swap_fee_amount=consume_market_swap_fee,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    swap_fees_event = bpool.get_event_log(
        "SWAP_FEES", tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args
    assert (
        publish_market_fee_dt_balance + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(swap_fees_event_args.tokenFeeAddress)
    )

    swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_event_args = swap_event[0].args

    assert (
        erc20_token.balanceOf(consumer_wallet.address) + swap_event_args.tokenAmountIn
        == consumer_dt_balance
    )
    assert consumer_bt_balance + swap_event_args.tokenAmountOut == base_token.balanceOf(
        consumer_wallet.address
    )

    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / publish_market_swap_fee))
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / lp_swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests consumer adds more liquidity with joinPool(), depositing both tokens

    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    erc20_token.approve(bpool_address, to_wei("1000"), consumer_wallet)

    tx = bpool.join_pool(to_wei("0.01"), [to_wei("50"), to_wei("50")], consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == erc20_token.address
    assert join_pool_event[1].args.tokenIn == base_token.address

    assert to_wei("0.01") == bpool.balanceOf(consumer_wallet.address)
    assert ss_contract_bpt_balance == bpool.balanceOf(
        get_address_of_type(config, "Staking")
    )
    assert ss_contract_dt_balance == erc20_token.balanceOf(
        get_address_of_type(config, "Staking")
    )

    # Tests publisher adds more liquidity with joinswapExternAmountIn, depositing only base tokens
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_join = side_staking.get_datatoken_balance(erc20_token.address)

    base_token.approve(bpool_address, to_wei("1000"), publisher_wallet)

    tx = bpool.join_swap_extern_amount_in(to_wei("1"), to_wei("0.01"), publisher_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_pool_event = bpool.get_event_log(
        bpool.EVENT_LOG_JOIN, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert join_pool_event[0].args.tokenIn == base_token.address
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
    assert erc20_token.balanceOf(publisher_wallet.address) == publisher_dt_balance

    # Tests publisher removes liquidity with ExitPool, receiving both tokens
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_bt_balance = base_token.balanceOf(publisher_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)

    publisher_bpt_balance = bpool.balanceOf(publisher_wallet.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    tx = bpool.exit_pool(
        to_wei("0.5"), [to_wei("0.001"), to_wei("0.001")], publisher_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert exit_event[0].args.tokenOut == erc20_token.address
    assert exit_event[1].args.tokenOut == base_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + publisher_dt_balance == erc20_token.balanceOf(
        publisher_wallet.address
    )
    assert exit_event[
        1
    ].args.tokenAmountOut + publisher_bt_balance == base_token.balanceOf(
        publisher_wallet.address
    )

    assert (
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit
    )
    assert (
        bpool.balanceOf(publisher_wallet.address) + to_wei("0.5")
        == publisher_bpt_balance
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address)

    assert ss_contract_dt_balance == erc20_token.balanceOf(side_staking.address)

    # Tests publisher removes liquidity with exitswapPoolAmountIn, receiving only base tokens

    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_bt_balance = base_token.balanceOf(publisher_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)

    publisher_bpt_balance = bpool.balanceOf(publisher_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        to_wei("0.05"), to_wei("0.005"), publisher_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    assert erc20_token.balanceOf(publisher_wallet.address) == publisher_dt_balance

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert exit_event[0].args.caller == publisher_wallet.address
    assert exit_event[0].args.tokenOut == base_token.address
    assert exit_event[1].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + publisher_bt_balance == base_token.balanceOf(
        publisher_wallet.address
    )
    assert (
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )

    assert publisher_bpt_balance == bpool.balanceOf(publisher_wallet.address) + to_wei(
        "0.05"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.05"
    )

    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # publisher removes liquidity with exitswapPoolAmountIn, receiving only datatokens

    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_bt_balance = base_token.balanceOf(publisher_wallet.address)
    ss_contract_dt_balance = erc20_token.balanceOf(side_staking.address)
    ss_contract_bpt_balance = bpool.balanceOf(side_staking.address)
    dt_balance_before_exit = side_staking.get_datatoken_balance(erc20_token.address)
    publisher_bpt_balance = bpool.balanceOf(publisher_wallet.address)

    tx = bpool.exit_swap_pool_amount_in(
        to_wei("0.05"), to_wei("0.005"), publisher_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert erc20_token.balanceOf(publisher_wallet.address) == publisher_dt_balance

    bpt_event = bpool.get_event_log(
        bpool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    assert (
        bpool.balanceOf(publisher_wallet.address)
        == publisher_bpt_balance - bpt_event[0].args.bptAmount
    )

    exit_event = bpool.get_event_log(
        bpool.EVENT_LOG_EXIT, tx_receipt.blockNumber, web3.eth.block_number, None
    )
    assert exit_event[0].args.caller == publisher_wallet.address
    assert exit_event[0].args.tokenOut == base_token.address
    assert exit_event[1].args.tokenOut == erc20_token.address

    assert exit_event[
        0
    ].args.tokenAmountOut + publisher_bt_balance == base_token.balanceOf(
        publisher_wallet.address
    )
    assert (
        side_staking.get_datatoken_balance(erc20_token.address)
        == dt_balance_before_exit + exit_event[1].args.tokenAmountOut
    )
    assert publisher_bpt_balance == bpool.balanceOf(publisher_wallet.address) + to_wei(
        "0.05"
    )

    assert ss_contract_bpt_balance == bpool.balanceOf(side_staking.address) + to_wei(
        "0.05"
    )
    assert ss_contract_dt_balance + exit_event[
        1
    ].args.tokenAmountOut == erc20_token.balanceOf(side_staking.address)

    # Tests no ocean and market fees were accounted for
    assert bpool.community_fee(base_token.address) > 0
    assert bpool.community_fee(erc20_token.address) > 0
    assert (bpool.publish_market_fee(erc20_token.address) > 0) is True
    assert (bpool.publish_market_fee(base_token.address) > 0) is True


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
    lp_swap_fee = to_wei("0.001")
    publish_market_swap_fee = to_wei("0.001")

    # Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = to_wei("1000")
    tx = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=consumer_wallet.address,
        fee_manager=factory_deployer_wallet.address,
        publish_market_order_fee_address=consumer_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=cap,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
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

    tx = erc20_token.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=dai_contract.decimals(),
        vesting_amount=initial_dai_liq,
        vesting_blocks=2500000,
        base_token_amount=initial_dai_liq,
        lp_swap_fee_amount=lp_swap_fee,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        ss_contract=side_staking.address,
        base_token_address=dai_contract.address,
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

    assert pool_event[0].event == "NewPool"
    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)
    assert bpool.is_finalized() is True
    assert bpool.opc_fee() == to_wei("0.002")
    assert bpool.get_swap_fee() == to_wei("0.001")
    assert bpool.community_fee(dai_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(dai_contract.address) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == MAX_UINT256 - initial_dai_liq

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
        token_in=dai_contract.address,
        token_out=erc20_address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        token_amount_in=to_wei("0.1"),
        min_amount_out=to_wei("0.0001"),
        max_price=to_wei("100"),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        token_in=dai_contract.address,
        token_out=erc20_address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        max_amount_in=to_wei(10),
        token_amount_out=to_wei(1),
        max_price=to_wei(100),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        token_in=erc20_address,
        token_out=dai_contract.address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        token_amount_in=to_wei("0.1"),
        min_amount_out=to_wei("0.0001"),
        max_price=to_wei("100"),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        swap_event_args.tokenAmountIn / (to_wei("1") / publish_market_swap_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / lp_swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher swaps some DT back to dai with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, to_wei("1000"), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        token_in=erc20_address,
        token_out=dai_contract.address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        max_amount_in=to_wei("0.1"),
        token_amount_out=to_wei("0.0001"),
        max_price=to_wei(100),
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
        round(swap_event_args.tokenAmountIn / (to_wei("1") / publish_market_swap_fee))
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / lp_swap_fee))
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
    assert bpool.opc_fee() == to_wei("0.002")
    assert bpool.get_swap_fee() == publish_market_swap_fee
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
    lp_swap_fee = to_wei("0.001")
    publish_market_swap_fee = to_wei("0.001")

    # Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = to_wei("1000")
    tx = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=consumer_wallet.address,
        fee_manager=factory_deployer_wallet.address,
        publish_market_order_fee_address=consumer_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=cap,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
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

    tx = erc20_token.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=usdc_contract.decimals(),
        vesting_amount=initial_usdc_liq,
        vesting_blocks=2500000,
        base_token_amount=initial_usdc_liq,
        lp_swap_fee_amount=lp_swap_fee,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        ss_contract=side_staking.address,
        base_token_address=usdc_contract.address,
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

    assert pool_event[0].event == "NewPool"
    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)
    assert bpool.is_finalized() is True
    assert bpool.opc_fee() == to_wei("0.002")
    assert bpool.get_swap_fee() == to_wei("0.001")
    assert bpool.community_fee(usdc_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(usdc_contract.address) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == MAX_UINT256 - to_wei(880)

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
        token_in=usdc_contract.address,
        token_out=erc20_address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        token_amount_in=int(1e7),
        min_amount_out=to_wei(1),
        max_price=to_wei(5),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        token_in=usdc_contract.address,
        token_out=erc20_address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        max_amount_in=to_wei(10),
        token_amount_out=to_wei(1),
        max_price=to_wei(100),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        token_in=erc20_address,
        token_out=usdc_contract.address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        token_amount_in=to_wei("0.1"),
        min_amount_out=int(1e4),
        max_price=int(2**256 - 1),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        swap_event_args.tokenAmountIn / (to_wei(1) / publish_market_swap_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / lp_swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher swaps some DT back to USDC with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        token_in=erc20_address,
        token_out=usdc_contract.address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        max_amount_in=to_wei(10),
        token_amount_out=int(1e6),
        max_price=to_wei(1000000000000000),
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
        round(swap_event_args.tokenAmountIn / (to_wei(1) / publish_market_swap_fee))
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / lp_swap_fee))
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
    assert bpool.opc_fee() == to_wei("0.002")
    assert bpool.get_swap_fee() == publish_market_swap_fee
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
    lp_swap_fee = to_wei("0.001")
    publish_market_swap_fee = to_wei("0.001")

    # Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = to_wei(1000)
    tx = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=consumer_wallet.address,
        fee_manager=factory_deployer_wallet.address,
        publish_market_order_fee_address=consumer_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=cap,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
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

    tx = erc20_token.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=usdc_contract.decimals(),
        vesting_amount=initial_usdc_liq,
        vesting_blocks=2500000,
        base_token_amount=initial_usdc_liq,
        lp_swap_fee_amount=lp_swap_fee,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        ss_contract=side_staking.address,
        base_token_address=usdc_contract.address,
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

    assert pool_event[0].event == "NewPool"
    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)

    assert bpool.is_finalized() is True
    assert bpool.get_swap_fee() == to_wei("0.001")
    assert bpool.community_fee(usdc_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(usdc_contract.address) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == MAX_UINT256 - to_wei(880)
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
        token_in=usdc_contract.address,
        token_out=erc20_address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        token_amount_in=int(1e7),
        min_amount_out=to_wei(1),
        max_price=to_wei(5),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        token_in=usdc_contract.address,
        token_out=erc20_address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        max_amount_in=to_wei(10),
        token_amount_out=to_wei(1),
        max_price=to_wei(100),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        token_in=erc20_address,
        token_out=usdc_contract.address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        token_amount_in=to_wei("0.1"),
        min_amount_out=int(1e4),
        max_price=int(2**256 - 1),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        swap_event_args.tokenAmountIn / (to_wei(1) / publish_market_swap_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / lp_swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher swaps some DT back to USDC with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_usdc_balance = usdc_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        token_in=erc20_address,
        token_out=usdc_contract.address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        max_amount_in=to_wei(10),
        token_amount_out=int(1e6),
        max_price=to_wei(1000000000000000),
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
        round(swap_event_args.tokenAmountIn / (to_wei(1) / publish_market_swap_fee))
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / lp_swap_fee))
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
    assert bpool.opc_fee() == to_wei("0.002")
    assert bpool.get_swap_fee() == publish_market_swap_fee
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
    lp_swap_fee = to_wei("0.001")
    publish_market_swap_fee = to_wei("0.001")

    # Tests consumer deploys a new erc20DT, assigning himself as minter
    cap = to_wei(1000)
    tx = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=consumer_wallet.address,
        fee_manager=factory_deployer_wallet.address,
        publish_market_order_fee_address=consumer_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=cap,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
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

    tx = erc20_token.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=dai_contract.decimals(),
        vesting_amount=initial_dai_liq,
        vesting_blocks=2500000,
        base_token_amount=initial_dai_liq,
        lp_swap_fee_amount=lp_swap_fee,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        ss_contract=side_staking.address,
        base_token_address=dai_contract.address,
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

    assert pool_event[0].event == "NewPool"
    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)

    assert bpool.is_finalized() is True
    assert bpool.get_swap_fee() == to_wei("0.001")
    assert bpool.community_fee(dai_contract.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(dai_contract.address) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(side_staking.address) == MAX_UINT256 - initial_dai_liq

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
        token_in=dai_contract.address,
        token_out=erc20_address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        token_amount_in=to_wei("0.1"),
        min_amount_out=to_wei("0.0001"),
        max_price=to_wei("100"),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        token_in=dai_contract.address,
        token_out=erc20_address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        max_amount_in=to_wei(10),
        token_amount_out=to_wei(1),
        max_price=to_wei(100),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        token_in=erc20_address,
        token_out=dai_contract.address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        token_amount_in=to_wei("0.1"),
        min_amount_out=to_wei("0.0001"),
        max_price=to_wei("100"),
        consume_market_swap_fee_amount=0,
        from_wallet=publisher_wallet,
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
        swap_event_args.tokenAmountIn / (to_wei(1) / publish_market_swap_fee)
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / lp_swap_fee))
        == swap_fees_event_args.LPFeeAmount
    )

    # Tests publisher swaps some DT back to DAI with swapExactAmountOut, check swap custom fees

    erc20_token.approve(bpool_address, to_wei(1000), publisher_wallet)
    publisher_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    publisher_dai_balance = dai_contract.balanceOf(publisher_wallet.address)
    dt_market_fee_balance = bpool.publish_market_fee(erc20_token.address)

    tx = bpool.swap_exact_amount_out(
        token_in=erc20_address,
        token_out=dai_contract.address,
        consume_market_swap_fee_address=another_consumer_wallet.address,
        max_amount_in=to_wei("0.1"),
        token_amount_out=to_wei("0.0001"),
        max_price=to_wei(100),
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
        round(swap_event_args.tokenAmountIn / (to_wei(1) / publish_market_swap_fee))
        == swap_fees_event_args.marketFeeAmount
    )
    assert (
        round(swap_event_args.tokenAmountIn / (to_wei("1") / lp_swap_fee))
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
    assert bpool.opc_fee() == to_wei("0.002")
    assert bpool.get_swap_fee() == publish_market_swap_fee
    assert (bpool.community_fee(erc20_token.address) > 0) is True
    assert (bpool.community_fee(dai_contract.address) > 0) is True
    assert (bpool.publish_market_fee(erc20_token.address) > 0) is True
    assert (bpool.publish_market_fee(dai_contract.address) > 0) is True
