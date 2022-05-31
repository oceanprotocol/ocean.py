#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from decimal import Decimal

import pytest
from web3 import Web3
from web3.exceptions import ContractLogicError

from ocean_lib.config import Config
from ocean_lib.models.bpool import BPool
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import MAX_WEI, from_wei, parse_units, to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.flows.test_exchange_swap_fees import (
    buy_or_sell_dt_and_verify_balances_swap_fees,
)
from tests.resources.helper_functions import (
    base_token_to_datatoken,
    transfer_base_token_if_balance_lte,
)


def test_create_pool_and_exchange(
    web3: Web3,
    config: Config,
    ocean_token: Datatoken,
    factory_deployer_wallet: Wallet,
    publisher_wallet: Wallet,
    consumer_wallet: Wallet,
    another_consumer_wallet: Wallet,
    datatoken: Datatoken,
):
    """
    Test interactions between pools, exchange, and dispenser.
    """
    bt = ocean_token
    dt = datatoken

    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=factory_deployer_wallet,
        recipient=publisher_wallet.address,
        min_balance=parse_units("1500", bt.decimals()),
        amount_to_transfer=parse_units("1500", bt.decimals()),
    )

    transfer_base_token_if_balance_lte(
        web3=web3,
        base_token_address=bt.address,
        from_wallet=factory_deployer_wallet,
        recipient=consumer_wallet.address,
        min_balance=parse_units("1500", bt.decimals()),
        amount_to_transfer=parse_units("1500", bt.decimals()),
    )

    # Create Pool
    publish_market_swap_fee = to_wei("0.003")
    consume_market_swap_fee = to_wei("0.005")
    dt_per_bt_in_wei = to_wei("1")
    bt_per_dt_in_wei = to_wei(Decimal("1") / from_wei(dt_per_bt_in_wei))
    with_mint = 1

    fixed_price_address = get_address_of_type(config, "FixedPrice")
    exchange = FixedRateExchange(web3, fixed_price_address)

    lp_swap_fee = to_wei("0.001")
    initial_base_token_amount = parse_units("1000", bt.decimals())

    factory_router = FactoryRouter(web3, get_address_of_type(config, "Router"))
    bt.approve(factory_router.address, MAX_WEI, publisher_wallet)

    side_staking = SideStaking(web3, get_address_of_type(config, "Staking"))

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
    BPool(web3, bpool_address)

    # Create Fixed Rate Exchange
    tx = dt.create_fixed_rate(
        fixed_price_address=fixed_price_address,
        base_token_address=bt.address,
        owner=publisher_wallet.address,
        publish_market_swap_fee_collector=publisher_wallet.address,
        allowed_swapper=ZERO_ADDRESS,
        base_token_decimals=bt.decimals(),
        datatoken_decimals=dt.decimals(),
        fixed_rate=bt_per_dt_in_wei,
        publish_market_swap_fee_amount=publish_market_swap_fee,
        with_mint=with_mint,
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    exchange_event = dt.get_event_log(
        dt.EVENT_NEW_FIXED_RATE,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    exchange_id = exchange_event[0].args.exchangeId

    # Grant infinite approvals for exchange to spend consumer's BT and DT
    dt.approve(exchange.address, MAX_WEI, consumer_wallet)
    bt.approve(exchange.address, MAX_WEI, consumer_wallet)

    one_base_token = parse_units("1", bt.decimals())

    with pytest.raises(ContractLogicError):
        buy_or_sell_dt_and_verify_balances_swap_fees(
            "buy",
            base_token_to_datatoken(one_base_token, bt.decimals(), dt_per_bt_in_wei),
            web3,
            exchange,
            exchange_id,
            another_consumer_wallet.address,
            consume_market_swap_fee,
            consumer_wallet,
        )
