#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from decimal import Decimal

import pytest
from web3 import Web3

from ocean_lib.config import Config
from ocean_lib.models.bpool import BPool
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from ocean_lib.web3_internal.currency import format_units, from_wei, parse_units, to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import (
    approx_format_units,
    approx_from_wei,
    deploy_erc721_erc20,
    get_address_of_type,
    transfer_base_token_if_balance_lte,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "base_token_name, publish_market_swap_fee, consume_market_swap_fee, lp_swap_fee",
    [
        ("Ocean", "0", "0", "0.0001"),
        ("Ocean", "0.003", "0.004", "0.005"),
        ("MockDAI", "0", "0", "0.0001"),
        ("MockDAI", "0.003", "0.004", "0.005"),
        ("MockUSDC", "0", "0", "0.0001"),
        ("MockUSDC", "0.003", "0.004", "0.005"),
    ],
)
def test_pool(
    web3: Web3,
    config: Config,
    factory_deployer_wallet: Wallet,
    consumer_wallet: Wallet,
    another_consumer_wallet: Wallet,
    publisher_wallet: Wallet,
    base_token_name: str,
    publish_market_swap_fee: str,
    consume_market_swap_fee: str,
    lp_swap_fee: str,
):
    """
    Tests pool swap fees with OCEAN, DAI, and USDC as base token
    OCEAN is an approved base token with 18 decimals (OPC Fee = 0.1%)
    DAI is a non-approved base token with 18 decimals (OPC Fee = 0.2%)
    USDC is a non-approved base token with 6 decimals (OPC Fee = 0.2%)
    """
    _test_pool(
        web3,
        config,
        factory_deployer_wallet,
        consumer_wallet,
        another_consumer_wallet,
        publisher_wallet,
        base_token_name,
        publish_market_swap_fee,
        consume_market_swap_fee,
        lp_swap_fee,
    )


def _test_pool(
    web3: Web3,
    config: Config,
    base_token_deployer_wallet: Wallet,
    consumer_wallet: Wallet,
    consume_market_swap_fee_collector: Wallet,
    publisher_wallet: Wallet,
    base_token_name: str,
    publish_market_swap_fee: str,
    consume_market_swap_fee: str,
    lp_swap_fee: str,
):
    bt = ERC20Token(web3, get_address_of_type(config, base_token_name))

    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=base_token_deployer_wallet,
        recipient=publisher_wallet.address,
        min_balance=parse_units("1500", bt.decimals()),
        amount_to_transfer=parse_units("1500", bt.decimals()),
    )

    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=base_token_deployer_wallet,
        recipient=consumer_wallet.address,
        min_balance=parse_units("500", bt.decimals()),
        amount_to_transfer=parse_units("500", bt.decimals()),
    )

    factory_router = FactoryRouter(web3, get_address_of_type(config, "Router"))
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))
    erc721_nft = deploy_erc721_erc20(web3, config, publisher_wallet)

    # Datatoken cap is hardcoded to MAX_WEI in contract regardles of what is passed.
    cap_doesnt_matter = to_wei("100000")

    # Tests publisher deploys a new erc20 datatoken
    tx = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
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
    dt = ERC20Token(web3, erc20_address)

    assert dt.get_permissions(publisher_wallet.address)[0] is True

    # Tests publisher calls deployPool(), we then check base token balance and fees

    publish_market_swap_fee = to_wei(publish_market_swap_fee)
    consume_market_swap_fee = to_wei(consume_market_swap_fee)
    lp_swap_fee = to_wei(lp_swap_fee)

    initial_base_token_amount = parse_units("1000", bt.decimals())

    bt.approve(factory_router.address, initial_base_token_amount, publisher_wallet)

    tx = dt.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=bt.decimals(),
        vesting_amount=initial_base_token_amount,
        vesting_blocks=2500000,
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
    if factory_router.is_approved_token(bt.address):
        assert bpool.opc_fee() == to_wei("0.001")
    else:
        assert bpool.opc_fee() == to_wei("0.002")
    assert bpool.opc_fee() == factory_router.get_opc_fee(bt.address)
    assert bpool.get_swap_fee() == lp_swap_fee
    assert bpool.get_market_fee() == publish_market_swap_fee

    # Verify 0 fees have been collected so far
    assert bpool.community_fee(bt.address) == 0
    assert bpool.community_fee(dt.address) == 0
    assert bpool.publish_market_fee(bt.address) == 0
    assert bpool.publish_market_fee(dt.address) == 0
    # TODO: Assert that consume market fee collector also has 0.

    initial_datatoken_amount = base_token_to_datatoken(
        initial_base_token_amount, bt.decimals()
    )
    assert dt.balanceOf(side_staking.address) == MAX_UINT256 - initial_datatoken_amount
    assert bt.balanceOf(bpool.address) == initial_base_token_amount
    assert dt.balanceOf(consumer_wallet.address) == 0

    check_calc_methods(web3, bpool)

    bt.approve(bpool.address, parse_units("1000", bt.decimals()), consumer_wallet)

    buy_dt_exact_amount_in(
        web3,
        bpool,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
        "1",
    )

    buy_dt_exact_amount_out(
        web3,
        bpool,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
        "2",
    )

    dt.approve(bpool_address, to_wei("1000"), consumer_wallet)

    buy_bt_exact_amount_in(
        web3,
        bpool,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
        "1",
    )

    buy_bt_exact_amount_out(
        web3,
        bpool,
        consume_market_swap_fee_collector.address,
        consume_market_swap_fee,
        consumer_wallet,
        "1",
    )


def buy_dt_exact_amount_in(
    web3: Web3,
    bpool: BPool,
    consume_market_swap_fee_address: str,
    consume_market_swap_fee: int,
    consumer_wallet: Wallet,
    bt_in_unit: str,
):
    """Tests consumer buys some DT - exactAmountIn"""
    bt = ERC20Token(web3, bpool.get_base_token_address())
    dt = ERC20Token(web3, bpool.get_datatoken_address())

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

    bt_in = parse_units(bt_in_unit, bt.decimals())

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

    slippage = Decimal("0.01")
    dt_out_unit = from_wei(dt_out)
    min_amount_out = to_wei(dt_out_unit - (dt_out_unit * slippage))
    max_price_impact = Decimal("0.01")
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
    dt_out_unit: str,
):
    """Tests consumer buys some DT - exactAmountOut"""
    bt = ERC20Token(web3, bpool.get_base_token_address())
    dt = ERC20Token(web3, bpool.get_datatoken_address())

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

    dt_out = to_wei(dt_out_unit)

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

    slippage = Decimal("0.01")
    bt_in_unit = format_units(bt_in, bt.decimals())
    max_amount_in = parse_units(bt_in_unit + (bt_in_unit * slippage), bt.decimals())
    max_price_impact = Decimal("0.01")
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
    dt_in_unit: str,
):
    """Tests consumer buys some BT - exactAmountIn"""
    bt = ERC20Token(web3, bpool.get_base_token_address())
    dt = ERC20Token(web3, bpool.get_datatoken_address())

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

    dt_in = to_wei(dt_in_unit)

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

    slippage = Decimal("0.01")
    bt_out_unit = format_units(bt_out)
    min_amount_out = parse_units(bt_out_unit - (bt_out_unit * slippage))
    max_price_impact = Decimal("0.01")
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
    bt_out_unit: str,
):
    """Tests consumer buys some DT - exactAmountOut"""
    bt = ERC20Token(web3, bpool.get_base_token_address())
    dt = ERC20Token(web3, bpool.get_datatoken_address())

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

    bt_out = parse_units(bt_out_unit, bt.decimals())

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

    slippage = Decimal("0.01")
    dt_in_unit = from_wei(dt_in)
    max_amount_in = to_wei(dt_in_unit + (dt_in_unit * slippage))
    max_price_impact = Decimal("0.01")
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


def base_token_to_datatoken(
    base_token_amount: int,
    base_token_decimals: int,
) -> int:
    """Datatokens have 18 decimals, even when base token decimals is different
    Given rate == 1, this converts from base tokens to equivalent datatokens
    """
    return to_wei(format_units(base_token_amount, base_token_decimals))


def check_calc_methods(web3: Web3, bpool: BPool):
    bt = ERC20Token(web3, bpool.get_base_token_address())
    dt = ERC20Token(web3, bpool.get_datatoken_address())

    bt_amount = parse_units("100", bt.decimals())
    dt_amount = base_token_to_datatoken(bt_amount, bt.decimals())

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
    assert approx_format_units(
        dt_in_pool_out,
        dt.decimals(),
        bt_in_pool_out,
        bt.decimals(),
    )

    # "DT out" and "BT out" are approx when BT decimals != 18
    dt_out_pool_in = bpool.calc_single_out_pool_in(dt.address, pt_amount)
    bt_out_pool_in = bpool.calc_single_out_pool_in(bt.address, pt_amount)
    assert approx_format_units(
        dt_out_pool_in,
        dt.decimals(),
        bt_out_pool_in,
        bt.decimals(),
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
        amount_in_unit * from_wei(bpool.opc_fee()), decimals
    )
    expected_publish_market_swap_fee_amount = parse_units(
        amount_in_unit * from_wei(bpool.get_market_fee()), decimals
    )
    expected_consume_market_swap_fee_amount = parse_units(
        amount_in_unit * from_wei(consume_market_swap_fee), decimals
    )

    assert approx_format_units(
        lp_fee_amount, decimals, expected_lp_swap_fee_amount, decimals
    )
    assert approx_format_units(
        opc_fee_amount, decimals, expected_opc_swap_fee_amount, decimals, rel=1e5
    )
    assert approx_format_units(
        publish_market_swap_fee_amount,
        decimals,
        expected_publish_market_swap_fee_amount,
        decimals,
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
    log_swap_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    log_swap_event_args = log_swap_event[0].args

    bt = ERC20Token(web3, bpool.get_base_token_address())
    dt = ERC20Token(web3, bpool.get_datatoken_address())

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

    swap_fees_event = bpool.get_event_log(
        bpool.EVENT_LOG_SWAP_FEES, tx_receipt.blockNumber, web3.eth.block_number, None
    )

    swap_fees_event_args = swap_fees_event[0].args

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

    assert approx_format_units(
        bpool_fee_balance,
        fee_token.decimals(),
        bpool_fee_token_balance_before
        + log_swap_event_args.tokenAmountIn
        - swap_fees_event_args.marketFeeAmount
        - swap_fees_event_args.oceanFeeAmount,
        fee_token.decimals(),
        rel=1e-4,
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
