#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from decimal import Decimal
from typing import Callable

import pytest
from web3 import Web3

from ocean_lib.config import Config
from ocean_lib.models.bpool import BPool
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.models.test.test_factory_router import (
    OPC_SWAP_FEE_APPROVED,
    OPC_SWAP_FEE_NOT_APPROVED,
)
from ocean_lib.web3_internal.currency import (
    MAX_WEI,
    format_units,
    from_wei,
    parse_units,
    to_wei,
)
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import get_opc_collector_address_from_pool
from tests.resources.helper_functions import (
    approx_format_units,
    approx_from_wei,
    base_token_to_datatoken,
    get_address_of_type,
    transfer_base_token_if_balance_lte,
)

logger = logging.getLogger(__name__)


@pytest.mark.unit
@pytest.mark.parametrize(
    "base_token_name, publish_market_swap_fee, consume_market_swap_fee, lp_swap_fee, dt_per_bt",
    [
        # Min fees
        ("Ocean", "0", "0", "0.0001", "1"),
        ("MockUSDC", "0", "0", "0.0001", "1"),
        # Happy path
        ("Ocean", "0.003", "0.005", "0.01", "1"),
        ("MockDAI", "0.003", "0.005", "0.01", "1"),
        ("MockUSDC", "0.003", "0.005", "0.01", "1"),
        # Max fees
        ("Ocean", "0.1", "0.1", "0.1", "1"),
        ("MockUSDC", "0.1", "0.1", "0.1", "1"),
        # Min rate. Rate must be > 1e12 wei (not equal)
        ("Ocean", "0.003", "0.005", "0.01", "0.000001000000000001"),
        ("MockUSDC", "0.003", "0.005", "0.01", "0.000001000000000001"),
        # High rate. There is no maximum
        ("Ocean", "0.003", "0.005", "0.01", "1000"),
        ("MockUSDC", "0.003", "0.005", "0.01", "1000"),
    ],
)
def test_pool_swap_fees(
    web3: Web3,
    config: Config,
    factory_deployer_wallet: Wallet,
    consumer_wallet: Wallet,
    another_consumer_wallet: Wallet,
    publisher_wallet: Wallet,
    base_token_name: str,
    datatoken: Datatoken,
    publish_market_swap_fee: str,
    consume_market_swap_fee: str,
    lp_swap_fee: str,
    dt_per_bt: str,
):
    """
    Tests pool swap fees with OCEAN, DAI, and USDC as base token

    OCEAN is an approved base token with 18 decimals (OPC Fee = 0.1%)
    DAI is a non-approved base token with 18 decimals (OPC Fee = 0.2%)
    USDC is a non-approved base token with 6 decimals (OPC Fee = 0.2%)
    """
    pool_swap_fees(
        web3=web3,
        config=config,
        base_token_deployer_wallet=factory_deployer_wallet,
        consumer_wallet=consumer_wallet,
        consume_market_swap_fee_collector=another_consumer_wallet,
        publisher_wallet=publisher_wallet,
        base_token_name=base_token_name,
        datatoken=datatoken,
        publish_market_swap_fee=publish_market_swap_fee,
        consume_market_swap_fee=consume_market_swap_fee,
        lp_swap_fee=lp_swap_fee,
        dt_per_bt=dt_per_bt,
    )


def pool_swap_fees(
    web3: Web3,
    config: Config,
    base_token_deployer_wallet: Wallet,
    consumer_wallet: Wallet,
    consume_market_swap_fee_collector: Wallet,
    publisher_wallet: Wallet,
    base_token_name: str,
    datatoken: Datatoken,
    publish_market_swap_fee: str,
    consume_market_swap_fee: str,
    lp_swap_fee: str,
    dt_per_bt: str,
):
    bt = Datatoken(web3, get_address_of_type(config, base_token_name))
    dt = datatoken

    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=base_token_deployer_wallet,
        recipient=publisher_wallet.address,
        min_balance=parse_units("15000", bt.decimals()),
        amount_to_transfer=parse_units("15000", bt.decimals()),
    )

    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=base_token_deployer_wallet,
        recipient=consumer_wallet.address,
        min_balance=parse_units("5000", bt.decimals()),
        amount_to_transfer=parse_units("5000", bt.decimals()),
    )

    # Tests publisher calls deployPool(), we then check base token balance and fees

    publish_market_swap_fee = to_wei(publish_market_swap_fee)
    consume_market_swap_fee = to_wei(consume_market_swap_fee)
    lp_swap_fee = to_wei(lp_swap_fee)

    initial_base_token_amount = parse_units("10000", bt.decimals())

    factory_router = FactoryRouter(web3, get_address_of_type(config, "Router"))
    bt.approve(factory_router.address, MAX_WEI, publisher_wallet)

    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
    dt_per_bt_in_wei = to_wei(dt_per_bt)
    tx = dt.deploy_pool(
        rate=dt_per_bt_in_wei,
        base_token_decimals=bt.decimals(),
        base_token_amount=initial_base_token_amount,
        lp_swap_fee_amount=lp_swap_fee,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        ss_contract=side_staking.address,
        base_token_address=bt.address,
        base_token_sender=publisher_wallet.address,
        publisher_address=publisher_wallet.address,
        publish_market_swap_fee_collector=publisher_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    pool_event = dt.get_event_log(
        dt.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)
    assert bpool.is_finalized()

    # Verify fee collectors are configured correctly
    get_opc_collector_address_from_pool(bpool) == get_address_of_type(
        config, "OPFCommunityFeeCollector"
    )
    assert bpool.get_publish_market_collector() == publisher_wallet.address

    # Verify fees are configured correctly
    if factory_router.is_approved_token(bt.address):
        assert bpool.get_opc_fee() == OPC_SWAP_FEE_APPROVED
    else:
        assert bpool.get_opc_fee() == OPC_SWAP_FEE_NOT_APPROVED
    assert bpool.get_opc_fee() == factory_router.get_opc_fee(bt.address)
    assert bpool.get_swap_fee() == lp_swap_fee
    assert bpool.get_market_fee() == publish_market_swap_fee

    # Verify 0 fees have been collected so far
    assert bpool.community_fee(bt.address) == 0
    assert bpool.community_fee(dt.address) == 0
    assert bpool.publish_market_fee(bt.address) == 0
    assert bpool.publish_market_fee(dt.address) == 0

    # Verify side staking bot holds all datatokens, minus the initial DT amount
    initial_datatoken_amount = base_token_to_datatoken(
        initial_base_token_amount, bt.decimals(), dt_per_bt_in_wei
    )
    assert dt.balanceOf(side_staking.address) == MAX_WEI - initial_datatoken_amount

    # Verify pool balances
    assert bt.balanceOf(bpool.address) == initial_base_token_amount
    assert dt.balanceOf(bpool.address) == initial_datatoken_amount

    # Verify consumer starts with 0 datatokens
    assert dt.balanceOf(consumer_wallet.address) == 0

    check_calc_methods(web3, bpool, dt_per_bt_in_wei)

    # Grant infinite approvals to pool
    bt.approve(bpool.address, MAX_WEI, consumer_wallet)
    dt.approve(bpool_address, MAX_WEI, consumer_wallet)

    one_hundred_base_tokens = parse_units("100", bt.decimals())

    buy_dt_exact_amount_in(
        web3,
        bpool,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
        one_hundred_base_tokens,
    )

    buy_dt_exact_amount_out(
        web3,
        bpool,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
        base_token_to_datatoken(
            one_hundred_base_tokens * 2, bt.decimals(), dt_per_bt_in_wei
        ),
    )

    buy_bt_exact_amount_in(
        web3,
        bpool,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
        base_token_to_datatoken(
            one_hundred_base_tokens, bt.decimals(), dt_per_bt_in_wei
        ),
    )

    buy_bt_exact_amount_out(
        web3,
        bpool,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
        one_hundred_base_tokens,
    )

    # Update LP swap fee
    new_lp_swap_fee = to_wei("0.06")
    side_staking.set_pool_swap_fee(
        dt.address, bpool.address, new_lp_swap_fee, publisher_wallet
    )
    assert bpool.get_swap_fee() == new_lp_swap_fee

    # Update publish market fee and fee collector
    new_publish_market_swap_fee_collector = consume_market_swap_fee_collector.address
    new_publish_market_swap_fee = to_wei("0.09")
    bpool.update_publish_market_fee(
        new_publish_market_swap_fee_collector,
        new_publish_market_swap_fee,
        publisher_wallet,
    )
    assert bpool.get_publish_market_collector() == new_publish_market_swap_fee_collector
    assert bpool.get_market_fee() == new_publish_market_swap_fee

    buy_dt_exact_amount_in(
        web3,
        bpool,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
        one_hundred_base_tokens,
    )

    # Collect publish market swap fees
    collect_fee_and_verify_balances(
        bpool.collect_market_fee, web3, bpool, publisher_wallet
    )

    # Collect OPC swap fees
    collect_fee_and_verify_balances(bpool.collect_opc, web3, bpool, publisher_wallet)


def buy_dt_exact_amount_in(
    web3: Web3,
    bpool: BPool,
    consume_market_swap_fee_address: str,
    consume_market_swap_fee: int,
    consumer_wallet: Wallet,
    bt_in: int,
):
    """Tests consumer buys some DT - exactAmountIn"""
    bt = Datatoken(web3, bpool.get_base_token_address())
    dt = Datatoken(web3, bpool.get_datatoken_address())

    consumer_bt_balance = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance = dt.balanceOf(consumer_wallet.address)
    bpool_bt_balance = bpool.get_balance(bt.address)
    bpool_dt_balance = bpool.get_balance(dt.address)
    publish_market_fee_bt_balance = bpool.publish_market_fee(bt.address)
    publish_market_fee_dt_balance = bpool.publish_market_fee(dt.address)
    opc_fee_bt_balance = bpool.community_fee(bt.address)
    opc_fee_dt_balance = bpool.community_fee(dt.address)
    consume_market_fee_bt_balance = bt.balanceOf(consume_market_swap_fee_address)
    consume_market_fee_dt_balance = dt.balanceOf(consume_market_swap_fee_address)

    (
        dt_out,
        lp_fee_amount,
        opc_fee_amount,
        publish_market_swap_fee_amount,
        consume_market_swap_fee_amount,
    ) = bpool.get_amount_out_exact_in(
        token_in=bt.address,
        token_out=dt.address,
        token_amount_in=bt_in,
        consume_market_swap_fee_amount=consume_market_swap_fee,
    )

    check_fee_amounts(
        bpool,
        bt_in,
        bt.decimals(),
        lp_fee_amount,
        opc_fee_amount,
        publish_market_swap_fee_amount,
        consume_market_swap_fee_amount,
        consume_market_swap_fee,
    )

    slippage = Decimal("0.01")  # 1%
    dt_out_unit = from_wei(dt_out)
    min_amount_out = to_wei(dt_out_unit - (dt_out_unit * slippage))
    max_price_impact = Decimal("0.01")  # 1%
    spot_price_before = bpool.get_spot_price(
        bt.address, dt.address, consume_market_swap_fee
    )
    max_price = to_wei(spot_price_before + (spot_price_before * max_price_impact))

    tx = bpool.swap_exact_amount_in(
        token_in=bt.address,
        token_out=dt.address,
        consume_market_swap_fee_address=consume_market_swap_fee_address,
        token_amount_in=bt_in,
        min_amount_out=min_amount_out,
        max_price=max_price,
        consume_market_swap_fee_amount=consume_market_swap_fee,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    bt_in_actual = check_balances_and_fees(
        web3,
        bpool,
        tx_receipt,
        consumer_bt_balance,
        consumer_dt_balance,
        consumer_wallet.address,
        bpool_bt_balance,
        bpool_dt_balance,
        publish_market_fee_bt_balance,
        publish_market_fee_dt_balance,
        opc_fee_bt_balance,
        opc_fee_dt_balance,
        consume_market_fee_bt_balance,
        consume_market_fee_dt_balance,
        consume_market_swap_fee_address,
        consume_market_swap_fee,
    )

    assert bt_in == bt_in_actual


def buy_dt_exact_amount_out(
    web3: Web3,
    bpool: BPool,
    consume_market_swap_fee_address: str,
    consume_market_swap_fee: int,
    consumer_wallet: Wallet,
    dt_out: int,
):
    """Tests consumer buys some DT - exactAmountOut"""
    bt = Datatoken(web3, bpool.get_base_token_address())
    dt = Datatoken(web3, bpool.get_datatoken_address())

    consumer_bt_balance = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance = dt.balanceOf(consumer_wallet.address)
    bpool_bt_balance = bpool.get_balance(bt.address)
    bpool_dt_balance = bpool.get_balance(dt.address)
    publish_market_fee_bt_balance = bpool.publish_market_fee(bt.address)
    publish_market_fee_dt_balance = bpool.publish_market_fee(dt.address)
    opc_fee_bt_balance = bpool.community_fee(bt.address)
    opc_fee_dt_balance = bpool.community_fee(dt.address)
    consume_market_fee_bt_balance = bt.balanceOf(consume_market_swap_fee_address)
    consume_market_fee_dt_balance = dt.balanceOf(consume_market_swap_fee_address)

    (
        bt_in,
        lp_fee_amount,
        opc_fee_amount,
        publish_market_swap_fee_amount,
        consume_market_swap_fee_amount,
    ) = bpool.get_amount_in_exact_out(
        token_in=bt.address,
        token_out=dt.address,
        token_amount_out=dt_out,
        consume_market_swap_fee_amount=consume_market_swap_fee,
    )

    check_fee_amounts(
        bpool,
        bt_in,
        bt.decimals(),
        lp_fee_amount,
        opc_fee_amount,
        publish_market_swap_fee_amount,
        consume_market_swap_fee_amount,
        consume_market_swap_fee,
    )

    slippage = Decimal("0.01")  # 1%
    bt_in_unit = format_units(bt_in, bt.decimals())
    max_amount_in = parse_units(bt_in_unit + (bt_in_unit * slippage), bt.decimals())
    max_price_impact = Decimal("0.01")  # 1%
    spot_price_before = bpool.get_spot_price(
        bt.address, dt.address, consume_market_swap_fee
    )
    max_price = to_wei(spot_price_before + (spot_price_before * max_price_impact))

    tx = bpool.swap_exact_amount_out(
        token_in=bt.address,
        token_out=dt.address,
        consume_market_swap_fee_address=consume_market_swap_fee_address,
        max_amount_in=max_amount_in,
        token_amount_out=dt_out,
        max_price=max_price,
        consume_market_swap_fee_amount=consume_market_swap_fee,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    bt_in_actual = check_balances_and_fees(
        web3,
        bpool,
        tx_receipt,
        consumer_bt_balance,
        consumer_dt_balance,
        consumer_wallet.address,
        bpool_bt_balance,
        bpool_dt_balance,
        publish_market_fee_bt_balance,
        publish_market_fee_dt_balance,
        opc_fee_bt_balance,
        opc_fee_dt_balance,
        consume_market_fee_bt_balance,
        consume_market_fee_dt_balance,
        consume_market_swap_fee_address,
        consume_market_swap_fee,
    )

    assert bt_in == bt_in_actual


def buy_bt_exact_amount_in(
    web3: Web3,
    bpool: BPool,
    consume_market_swap_fee_address: str,
    consume_market_swap_fee: int,
    consumer_wallet: Wallet,
    dt_in: int,
):
    """Tests consumer buys some BT - exactAmountIn"""
    bt = Datatoken(web3, bpool.get_base_token_address())
    dt = Datatoken(web3, bpool.get_datatoken_address())

    consumer_bt_balance = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance = dt.balanceOf(consumer_wallet.address)
    bpool_bt_balance = bpool.get_balance(bt.address)
    bpool_dt_balance = bpool.get_balance(dt.address)
    publish_market_fee_bt_balance = bpool.publish_market_fee(bt.address)
    publish_market_fee_dt_balance = bpool.publish_market_fee(dt.address)
    opc_fee_bt_balance = bpool.community_fee(bt.address)
    opc_fee_dt_balance = bpool.community_fee(dt.address)
    consume_market_fee_bt_balance = bt.balanceOf(consume_market_swap_fee_address)
    consume_market_fee_dt_balance = dt.balanceOf(consume_market_swap_fee_address)

    (
        bt_out,
        lp_fee_amount,
        opc_fee_amount,
        publish_market_swap_fee_amount,
        consume_market_swap_fee_amount,
    ) = bpool.get_amount_out_exact_in(
        token_in=dt.address,
        token_out=bt.address,
        token_amount_in=dt_in,
        consume_market_swap_fee_amount=consume_market_swap_fee,
    )

    check_fee_amounts(
        bpool,
        dt_in,
        dt.decimals(),
        lp_fee_amount,
        opc_fee_amount,
        publish_market_swap_fee_amount,
        consume_market_swap_fee_amount,
        consume_market_swap_fee,
    )

    slippage = Decimal("0.01")  # 1%
    bt_out_unit = format_units(bt_out)
    min_amount_out = parse_units(bt_out_unit - (bt_out_unit * slippage))
    max_price_impact = Decimal("0.01")  # 1%
    spot_price_before = bpool.get_spot_price(
        dt.address, bt.address, consume_market_swap_fee
    )
    max_price = parse_units(
        spot_price_before + (spot_price_before * max_price_impact), bt.decimals()
    )

    tx = bpool.swap_exact_amount_in(
        token_in=dt.address,
        token_out=bt.address,
        consume_market_swap_fee_address=consume_market_swap_fee_address,
        token_amount_in=dt_in,
        min_amount_out=min_amount_out,
        max_price=max_price,
        consume_market_swap_fee_amount=consume_market_swap_fee,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    dt_in_actual = check_balances_and_fees(
        web3,
        bpool,
        tx_receipt,
        consumer_bt_balance,
        consumer_dt_balance,
        consumer_wallet.address,
        bpool_bt_balance,
        bpool_dt_balance,
        publish_market_fee_bt_balance,
        publish_market_fee_dt_balance,
        opc_fee_bt_balance,
        opc_fee_dt_balance,
        consume_market_fee_bt_balance,
        consume_market_fee_dt_balance,
        consume_market_swap_fee_address,
        consume_market_swap_fee,
    )

    assert dt_in == dt_in_actual


def buy_bt_exact_amount_out(
    web3: Web3,
    bpool: BPool,
    consume_market_swap_fee_address: str,
    consume_market_swap_fee: int,
    consumer_wallet: Wallet,
    bt_out: int,
):
    """Tests consumer buys some DT - exactAmountOut"""
    bt = Datatoken(web3, bpool.get_base_token_address())
    dt = Datatoken(web3, bpool.get_datatoken_address())

    consumer_bt_balance = bt.balanceOf(consumer_wallet.address)
    consumer_dt_balance = dt.balanceOf(consumer_wallet.address)
    bpool_bt_balance = bpool.get_balance(bt.address)
    bpool_dt_balance = bpool.get_balance(dt.address)
    publish_market_fee_bt_balance = bpool.publish_market_fee(bt.address)
    publish_market_fee_dt_balance = bpool.publish_market_fee(dt.address)
    opc_fee_bt_balance = bpool.community_fee(bt.address)
    opc_fee_dt_balance = bpool.community_fee(dt.address)
    consume_market_fee_bt_balance = bt.balanceOf(consume_market_swap_fee_address)
    consume_market_fee_dt_balance = dt.balanceOf(consume_market_swap_fee_address)

    (
        dt_in,
        lp_fee_amount,
        opc_fee_amount,
        publish_market_swap_fee_amount,
        consume_market_swap_fee_amount,
    ) = bpool.get_amount_in_exact_out(
        token_in=dt.address,
        token_out=bt.address,
        token_amount_out=bt_out,
        consume_market_swap_fee_amount=consume_market_swap_fee,
    )

    check_fee_amounts(
        bpool,
        dt_in,
        dt.decimals(),
        lp_fee_amount,
        opc_fee_amount,
        publish_market_swap_fee_amount,
        consume_market_swap_fee_amount,
        consume_market_swap_fee,
    )

    slippage = Decimal("0.01")  # 1%
    dt_in_unit = from_wei(dt_in)
    max_amount_in = to_wei(dt_in_unit + (dt_in_unit * slippage))
    max_price_impact = Decimal("0.01")  # 1%
    spot_price_before = bpool.get_spot_price(
        dt.address, bt.address, consume_market_swap_fee
    )
    max_price = parse_units(
        spot_price_before + (spot_price_before * max_price_impact), bt.decimals()
    )

    tx = bpool.swap_exact_amount_out(
        token_in=dt.address,
        token_out=bt.address,
        consume_market_swap_fee_address=consume_market_swap_fee_address,
        max_amount_in=max_amount_in,
        token_amount_out=bt_out,
        max_price=max_price,
        consume_market_swap_fee_amount=consume_market_swap_fee,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    dt_in_actual = check_balances_and_fees(
        web3,
        bpool,
        tx_receipt,
        consumer_bt_balance,
        consumer_dt_balance,
        consumer_wallet.address,
        bpool_bt_balance,
        bpool_dt_balance,
        publish_market_fee_bt_balance,
        publish_market_fee_dt_balance,
        opc_fee_bt_balance,
        opc_fee_dt_balance,
        consume_market_fee_bt_balance,
        consume_market_fee_dt_balance,
        consume_market_swap_fee_address,
        consume_market_swap_fee,
    )

    assert dt_in == dt_in_actual


def check_calc_methods(web3: Web3, bpool: BPool, dt_per_bt_in_wei: int):
    bt = Datatoken(web3, bpool.get_base_token_address())
    dt = Datatoken(web3, bpool.get_datatoken_address())

    bt_amount = parse_units("100", bt.decimals())
    dt_amount = base_token_to_datatoken(bt_amount, bt.decimals(), dt_per_bt_in_wei)

    # "PT out" is equal when calculated using "DT in" or "BT in", regardless of BT decimals
    pool_out_dt_in = bpool.calc_pool_out_single_in(dt.address, dt_amount)
    pool_out_bt_in = bpool.calc_pool_out_single_in(bt.address, bt_amount)
    assert pool_out_dt_in == pool_out_bt_in

    # "PT in" is approx when calculated using "DT out" or "BT out", when BT decimals != 18
    pool_in_dt_out = bpool.calc_pool_in_single_out(dt.address, dt_amount)
    pool_in_bt_out = bpool.calc_pool_in_single_out(bt.address, bt_amount)
    assert approx_from_wei(pool_in_dt_out, pool_in_bt_out)

    pt_amount = to_wei("5")

    # "DT in" and "BT in" are approx when BT decimals != 18
    dt_in_pool_out = bpool.calc_single_in_pool_out(dt.address, pt_amount)
    bt_in_pool_out = bpool.calc_single_in_pool_out(bt.address, pt_amount)
    bt_in_pool_out_as_dt = base_token_to_datatoken(
        bt_in_pool_out, bt.decimals(), dt_per_bt_in_wei
    )
    assert approx_from_wei(
        dt_in_pool_out,
        bt_in_pool_out_as_dt,
    )

    # "DT out" and "BT out" are approx when BT decimals != 18
    dt_out_pool_in = bpool.calc_single_out_pool_in(dt.address, pt_amount)
    bt_out_pool_in = bpool.calc_single_out_pool_in(bt.address, pt_amount)
    bt_out_pool_in_as_dt = base_token_to_datatoken(
        bt_out_pool_in, bt.decimals(), dt_per_bt_in_wei
    )
    assert approx_from_wei(
        dt_out_pool_in,
        bt_out_pool_in_as_dt,
    )


def check_fee_amounts(
    bpool: BPool,
    amount_in: int,
    decimals: int,
    lp_fee_amount: int,
    opc_fee_amount: int,
    publish_market_swap_fee_amount: int,
    consume_market_swap_fee_amount: int,
    consume_market_swap_fee: int,
):
    amount_in_unit = format_units(amount_in, decimals)

    expected_lp_swap_fee_amount = parse_units(
        amount_in_unit * from_wei(bpool.get_swap_fee()), decimals
    )
    expected_opc_swap_fee_amount = parse_units(
        amount_in_unit * from_wei(bpool.get_opc_fee()), decimals
    )
    expected_publish_market_swap_fee_amount = parse_units(
        amount_in_unit * from_wei(bpool.get_market_fee()), decimals
    )
    expected_consume_market_swap_fee_amount = parse_units(
        amount_in_unit * from_wei(consume_market_swap_fee), decimals
    )

    assert approx_format_units(
        lp_fee_amount, decimals, expected_lp_swap_fee_amount, decimals, rel=1e5
    )
    assert approx_format_units(
        opc_fee_amount, decimals, expected_opc_swap_fee_amount, decimals, rel=1e5
    )
    assert approx_format_units(
        publish_market_swap_fee_amount,
        decimals,
        expected_publish_market_swap_fee_amount,
        decimals,
        rel=1e5,
    )
    assert approx_format_units(
        consume_market_swap_fee_amount,
        decimals,
        expected_consume_market_swap_fee_amount,
        decimals,
        rel=1e5,
    )


def check_balances_and_fees(
    web3: Web3,
    bpool: BPool,
    tx_receipt,
    consumer_bt_balance_before: int,
    consumer_dt_balance_before: int,
    consumer_address: str,
    bpool_bt_balance_before: int,
    bpool_dt_balance_before: int,
    publish_market_swap_fee_bt_balance_before: int,
    publish_market_swap_fee_dt_balance_before: int,
    opc_swap_fee_bt_balance_before: int,
    opc_swap_fee_dt_balance_before: int,
    consume_market_swap_fee_bt_balance_before: int,
    consume_market_swap_fee_dt_balance_before: int,
    consume_market_swap_fee_address: str,
    consume_market_swap_fee: int,
):
    # Get LOG_SWAP event
    log_swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
    )
    log_swap_event_args = log_swap_event[0].args

    bt = Datatoken(web3, bpool.get_base_token_address())
    dt = Datatoken(web3, bpool.get_datatoken_address())

    consumer_bt_balance = bt.balanceOf(consumer_address)
    consumer_dt_balance = dt.balanceOf(consumer_address)

    if log_swap_event_args.tokenIn == bt.address:
        consumer_in_token_balance_before = consumer_bt_balance_before
        consumer_in_token_balance = consumer_bt_balance
        consumer_out_token_balance_before = consumer_dt_balance_before
        consumer_out_token_balance = consumer_dt_balance
    else:
        consumer_in_token_balance_before = consumer_dt_balance_before
        consumer_in_token_balance = consumer_dt_balance
        consumer_out_token_balance_before = consumer_bt_balance_before
        consumer_out_token_balance = consumer_bt_balance

    # Check LOG_SWAP event
    assert (
        consumer_in_token_balance + log_swap_event_args.tokenAmountIn
        == consumer_in_token_balance_before
    )
    assert (
        consumer_out_token_balance_before + log_swap_event_args.tokenAmountOut
        == consumer_out_token_balance
    )

    # Get LOG_SWAP_FEES event
    swap_fees_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP_FEES, tx_receipt.blockNumber, web3.eth.block_number, None
    )
    swap_fees_event_args = swap_fees_event[0].args

    # Assign "fee" token and "not"-fee token.
    # Fees are denominated in the token coming into the pool
    if swap_fees_event_args.tokenFeeAddress == bt.address:
        fee_token = bt
        not_token = dt
        publish_fee_balance_before = publish_market_swap_fee_bt_balance_before
        publish_not_balance_before = publish_market_swap_fee_dt_balance_before
        opc_fee_balance_before = opc_swap_fee_bt_balance_before
        opc_not_balance_before = opc_swap_fee_dt_balance_before
        consume_fee_token_balance_before = consume_market_swap_fee_bt_balance_before
        consume_not_token_balance_before = consume_market_swap_fee_dt_balance_before
        bpool_fee_token_balance_before = bpool_bt_balance_before
        bpool_not_token_balance_before = bpool_dt_balance_before
    else:
        fee_token = dt
        not_token = bt
        publish_fee_balance_before = publish_market_swap_fee_dt_balance_before
        publish_not_balance_before = publish_market_swap_fee_bt_balance_before
        opc_fee_balance_before = opc_swap_fee_dt_balance_before
        opc_not_balance_before = opc_swap_fee_bt_balance_before
        consume_fee_token_balance_before = consume_market_swap_fee_dt_balance_before
        consume_not_token_balance_before = consume_market_swap_fee_bt_balance_before
        bpool_fee_token_balance_before = bpool_dt_balance_before
        bpool_not_token_balance_before = bpool_bt_balance_before

    # Get current fee balances
    publish_fee_balance = bpool.publish_market_fee(fee_token.address)
    publish_not_balance = bpool.publish_market_fee(not_token.address)
    opc_fee_balance = bpool.community_fee(fee_token.address)
    opc_not_balance = bpool.community_fee(not_token.address)
    consume_fee_balance = fee_token.balanceOf(consume_market_swap_fee_address)
    consume_not_balance = not_token.balanceOf(consume_market_swap_fee_address)
    bpool_fee_balance = bpool.get_balance(fee_token.address)
    bpool_not_balance = bpool.get_balance(not_token.address)

    # Check SWAP_FEES event
    assert (
        publish_fee_balance_before + swap_fees_event_args.marketFeeAmount
        == bpool.publish_market_fee(fee_token.address)
    )
    assert publish_not_balance_before == bpool.publish_market_fee(not_token.address)
    assert (
        opc_fee_balance_before + swap_fees_event_args.oceanFeeAmount
        == bpool.community_fee(fee_token.address)
    )
    assert opc_not_balance_before == bpool.community_fee(not_token.address)
    assert (
        consume_fee_token_balance_before + swap_fees_event_args.consumeMarketFeeAmount
        == fee_token.balanceOf(consume_market_swap_fee_address)
    )
    assert consume_not_token_balance_before == not_token.balanceOf(
        consume_market_swap_fee_address
    )

    # Check balances
    assert (
        publish_fee_balance
        == publish_fee_balance_before + swap_fees_event_args.marketFeeAmount
    )
    assert publish_not_balance == publish_not_balance_before
    assert (
        opc_fee_balance == opc_fee_balance_before + swap_fees_event_args.oceanFeeAmount
    )
    assert opc_not_balance == opc_not_balance_before
    assert (
        consume_fee_balance
        == consume_fee_token_balance_before
        + swap_fees_event_args.consumeMarketFeeAmount
    )
    assert consume_not_balance == consume_not_token_balance_before

    assert (
        bpool_fee_balance
        == bpool_fee_token_balance_before
        + log_swap_event_args.tokenAmountIn
        - swap_fees_event_args.marketFeeAmount
        - swap_fees_event_args.oceanFeeAmount
        - swap_fees_event_args.consumeMarketFeeAmount
    )

    assert (
        bpool_not_balance
        == bpool_not_token_balance_before - log_swap_event_args.tokenAmountOut
    )

    check_fee_amounts(
        bpool,
        log_swap_event_args.tokenAmountIn,
        fee_token.decimals(),
        swap_fees_event_args.LPFeeAmount,
        swap_fees_event_args.oceanFeeAmount,
        swap_fees_event_args.marketFeeAmount,
        swap_fees_event_args.consumeMarketFeeAmount,
        consume_market_swap_fee,
    )

    return log_swap_event_args.tokenAmountIn


def collect_fee_and_verify_balances(
    method: Callable,
    web3: Web3,
    bpool: BPool,
    wallet: Wallet,
):
    bt = Datatoken(web3, bpool.get_base_token_address())
    dt = Datatoken(web3, bpool.get_datatoken_address())

    if method == bpool.collect_market_fee:
        fee_collector = bpool.get_publish_market_collector()
        event_name = bpool.EVENT_PUBLISH_MARKET_FEE
        get_bpool_fee_balance = bpool.publish_market_fee
    else:
        fee_collector = get_opc_collector_address_from_pool(bpool)
        event_name = bpool.EVENT_OPC_FEE
        get_bpool_fee_balance = bpool.community_fee

    fee_collector_bt_balance_before = bt.balanceOf(fee_collector)
    fee_collector_dt_balance_before = dt.balanceOf(fee_collector)

    tx = method(wallet)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    fee_collector_bt_balance_after = bt.balanceOf(fee_collector)
    fee_collector_dt_balance_after = dt.balanceOf(fee_collector)

    events = bpool.get_event_log(
        event_name, tx_receipt.blockNumber, web3.eth.block_number, None
    )
    if events[0].args.token == bt.address:
        bt_args = events[0].args
        dt_args = events[1].args
    else:
        bt_args = events[1].args
        dt_args = events[0].args

    assert (
        fee_collector_bt_balance_before + bt_args.amount
        == fee_collector_bt_balance_after
    )
    assert (
        fee_collector_dt_balance_before + dt_args.amount
        == fee_collector_dt_balance_after
    )
    assert get_bpool_fee_balance(bt.address) == 0
    assert get_bpool_fee_balance(dt.address) == 0


@pytest.mark.parametrize("base_token_name", ["Ocean", "MockDAI", "MockUSDC"])
def test_swap_calculations(
    web3: Web3,
    config: Config,
    factory_deployer_wallet: Wallet,
    publisher_wallet: Wallet,
    datatoken: Datatoken,
    base_token_name: str,
):
    bt = Datatoken(web3, get_address_of_type(config, base_token_name))
    dt = datatoken

    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=factory_deployer_wallet,
        recipient=publisher_wallet.address,
        min_balance=parse_units("1500", bt.decimals()),
        amount_to_transfer=parse_units("1500", bt.decimals()),
    )

    publish_market_swap_fee = to_wei("0.003")
    consume_market_swap_fee = to_wei("0.005")
    lp_swap_fee = to_wei("0.01")

    initial_base_token_amount = parse_units("1000", bt.decimals())

    factory_router = FactoryRouter(web3, get_address_of_type(config, "Router"))
    bt.approve(factory_router.address, MAX_WEI, publisher_wallet)

    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
    dt_per_bt_in_wei = to_wei("1")
    tx = dt.deploy_pool(
        rate=dt_per_bt_in_wei,
        base_token_decimals=bt.decimals(),
        base_token_amount=initial_base_token_amount,
        lp_swap_fee_amount=lp_swap_fee,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        ss_contract=side_staking.address,
        base_token_address=bt.address,
        base_token_sender=publisher_wallet.address,
        publisher_address=publisher_wallet.address,
        publish_market_swap_fee_collector=publisher_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    pool_event = dt.get_event_log(
        dt.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)

    amount_in = parse_units(100, bt.decimals())

    (
        cogi_amount_out,
        cogi_amount_added_to_pool,
        (
            cogi_lp_fee_amount,
            cogi_opc_fee_amount,
            cogi_publish_market_fee_amount,
            cogi_consume_market_fee_amount,
        ),
    ) = bpool.calc_out_given_in(
        bt.address, dt.address, amount_in, consume_market_swap_fee
    )

    # `calc_in_given_out` using the "out" amount calculated by `calc_out_given_in`
    (
        cigo_amount_in,
        cigo_amount_added_to_pool,
        (
            cigo_lp_fee_amount,
            cigo_opc_fee_amount,
            cigo_publish_market_fee_amount,
            cigo_consume_market_fee_amount,
        ),
    ) = bpool.calc_in_given_out(
        bt.address, dt.address, cogi_amount_out, consume_market_swap_fee
    )

    logger.info(
        f"\n"
        f"amount_in = {format_units(amount_in, bt.decimals())}\n"
        f"cogi_amount_out = {format_units(cogi_amount_out, dt.decimals())}\n"
        f"cogi_amount_added_to_pool = {format_units(cogi_amount_added_to_pool, bt.decimals())}\n"
        f"cogi_lp_fee_amount = {format_units(cogi_lp_fee_amount, bt.decimals())}\n"
        f"cogi_opc_fee_amount = {format_units(cogi_opc_fee_amount, bt.decimals())}\n"
        f"cogi_publish_market_fee_amount = {format_units(cogi_publish_market_fee_amount, bt.decimals())}\n"
        f"cogi_consume_market_fee_amount = {format_units(cogi_consume_market_fee_amount, bt.decimals())}\n"
        f"cigo_amount_in = {format_units(cigo_amount_in, bt.decimals())}\n"
        f"cigo_amount_added_to_pool = {format_units(cigo_amount_added_to_pool, bt.decimals())}\n"
        f"cigo_lp_fee_amount = {format_units(cigo_lp_fee_amount, bt.decimals())}\n"
        f"cigo_opc_fee_amount = {format_units(cigo_opc_fee_amount, bt.decimals())}\n"
        f"cigo_publish_market_fee_amount = {format_units(cigo_publish_market_fee_amount, bt.decimals())}\n"
        f"cigo_consume_market_fee_amount = {format_units(cigo_consume_market_fee_amount, bt.decimals())}\n"
    )

    assert approx_format_units(cigo_amount_in, bt.decimals(), amount_in, bt.decimals())

    # Amount added to the pool should equal the amount_in minus the opc fee,
    # publish fee, and consume fee. LP fee is not subtracted because it's
    # absorbed into the pool, thus making the pool tokens more valuable.
    assert (
        cigo_amount_added_to_pool
        == cigo_amount_in
        - cigo_opc_fee_amount
        - cigo_publish_market_fee_amount
        - cigo_consume_market_fee_amount
    )
    assert (
        cogi_amount_added_to_pool
        == amount_in
        - cogi_opc_fee_amount
        - cogi_publish_market_fee_amount
        - cogi_consume_market_fee_amount
    )
