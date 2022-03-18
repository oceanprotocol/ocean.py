#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import get_address_of_type


@pytest.mark.unit
def test_properties(factory_router):
    """Tests the events' properties."""
    assert factory_router.event_NewPool.abi["name"] == FactoryRouter.EVENT_NEW_POOL


@pytest.mark.unit
def test_is_approved_token_mapping(config, factory_router):
    """Tests that Ocean token has been added to the mapping"""
    is_approved_token = factory_router.is_approved_token(
        get_address_of_type(config, "Ocean")
    )
    assert is_approved_token is True


@pytest.mark.unit
def test_mapping_ss_contracts(config, factory_router):
    """Tests if ssContract address has been added to the mapping"""
    assert factory_router.is_ss_contract(get_address_of_type(config, "Staking")) is True


@pytest.mark.unit
def test_fixed_rate_mapping(config, factory_router):
    """Tests that fixedRateExchange address is added to the mapping"""
    assert (
        factory_router.is_fixed_rate_contract(get_address_of_type(config, "FixedPrice"))
        is True
    )


@pytest.mark.unit
def test_buy_dt_batch(
    web3,
    config,
    factory_router,
    consumer_wallet,
    factory_deployer_wallet,
    another_consumer_wallet,
):
    """Tests that a batch of tokens is successfully bought through the buy_dt_batch function"""

    nft_factory = ERC721FactoryContract(
        web3=web3,
        address=get_address_of_type(config, ERC721FactoryContract.CONTRACT_NAME),
    )

    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(
        get_address_of_type(config, ERC721FactoryContract.CONTRACT_NAME),
        2**256 - 1,
        factory_deployer_wallet,
    )
    ocean_contract.approve(
        get_address_of_type(config, "Router"), 2**256 - 1, factory_deployer_wallet
    )

    tx = nft_factory.create_nft_erc20_with_pool(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        nft_token_uri="https://oceanprotocol.com/nft/",
        datatoken_template=1,
        datatoken_name="ERC20B1",
        datatoken_symbol="ERC20DT1Symbol",
        datatoken_minter=factory_deployer_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_address=factory_deployer_wallet.address,
        datatoken_publish_market_fee_token=ZERO_ADDRESS,
        datatoken_cap=to_wei("1000000"),
        datatoken_publish_market_fee_amount=0,
        datatoken_bytess=[b""],
        pool_rate=to_wei("2"),
        pool_base_token_decimals=ocean_contract.decimals(),
        pool_vesting_amount=to_wei("10000"),
        pool_vesting_blocks=2500000,
        pool_base_token_amount=to_wei("2"),
        pool_lp_swap_fee=to_wei("0.001"),
        pool_publish_market_swap_fee=to_wei("0.001"),
        pool_side_staking=get_address_of_type(config, "Staking"),
        pool_base_token=get_address_of_type(config, "Ocean"),
        pool_base_token_sender=get_address_of_type(
            config, ERC721FactoryContract.CONTRACT_NAME
        ),
        pool_publisher=factory_deployer_wallet.address,
        pool_publish_market_fee_collector=factory_deployer_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=factory_deployer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = nft_factory.get_event_log(
        "TokenCreated", tx_receipt.blockNumber, web3.eth.block_number, None
    )
    erc_token = registered_event[0]["args"]["newTokenAddress"]
    erc_token_contract = ERC20Token(web3=web3, address=erc_token)
    registered_event_pool = erc_token_contract.get_event_log(
        FactoryRouter.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    pool1 = registered_event_pool[0]["args"]["poolAddress"]

    tx = nft_factory.create_nft_erc20_with_pool(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        nft_token_uri="https://oceanprotocol.com/nft/",
        datatoken_template=1,
        datatoken_name="ERC20B12",
        datatoken_symbol="ERC20DT1Symbol2",
        datatoken_minter=factory_deployer_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_address=factory_deployer_wallet.address,
        datatoken_publish_market_fee_token=ZERO_ADDRESS,
        datatoken_cap=to_wei("1000000"),
        datatoken_publish_market_fee_amount=0,
        datatoken_bytess=[b""],
        pool_rate=to_wei("1"),
        pool_base_token_decimals=ocean_contract.decimals(),
        pool_vesting_amount=to_wei("10000"),
        pool_vesting_blocks=2500000,
        pool_base_token_amount=to_wei("2"),
        pool_lp_swap_fee=to_wei("0.001"),
        pool_publish_market_swap_fee=to_wei("0.001"),
        pool_side_staking=get_address_of_type(config, "Staking"),
        pool_base_token=get_address_of_type(config, "Ocean"),
        pool_base_token_sender=get_address_of_type(
            config, ERC721FactoryContract.CONTRACT_NAME
        ),
        pool_publisher=factory_deployer_wallet.address,
        pool_publish_market_fee_collector=factory_deployer_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=factory_deployer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = nft_factory.get_event_log(
        "TokenCreated", tx_receipt.blockNumber, web3.eth.block_number, None
    )
    erc_token2 = registered_event[0]["args"]["newTokenAddress"]
    erc_token_contract2 = ERC20Token(web3=web3, address=erc_token2)
    registered_event_pool = erc_token_contract2.get_event_log(
        FactoryRouter.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    pool2 = registered_event_pool[0]["args"]["poolAddress"]

    op1 = {
        "exchangeIds": web3.keccak(0x00),
        "source": pool1,
        "operation": 0,
        "tokenIn": get_address_of_type(config, "Ocean"),
        "amountsIn": to_wei("1"),
        "tokenOut": erc_token,
        "amountsOut": to_wei("0.1"),
        "maxPrice": to_wei("10"),
        "swapMarketFee": 0,
        "marketFeeAddress": another_consumer_wallet.address,
    }

    op2 = {
        "exchangeIds": web3.keccak(0x00),
        "source": pool2,
        "operation": 0,
        "tokenIn": get_address_of_type(config, "Ocean"),
        "amountsIn": to_wei("1"),
        "tokenOut": erc_token2,
        "amountsOut": to_wei("0.1"),
        "maxPrice": to_wei("10"),
        "swapMarketFee": 0,
        "marketFeeAddress": another_consumer_wallet.address,
    }

    balance_ocean_before = ocean_contract.balanceOf(factory_deployer_wallet.address)
    factory_router.buy_dt_batch([op1, op2], factory_deployer_wallet)
    balance_ocean_after = ocean_contract.balanceOf(factory_deployer_wallet.address)

    balance_dt1 = erc_token_contract.balanceOf(factory_deployer_wallet.address)
    balance_dt2 = erc_token_contract2.balanceOf(factory_deployer_wallet.address)

    assert balance_ocean_after < balance_ocean_before
    assert balance_dt1 > 0
    assert balance_dt2 > 0


@pytest.mark.unit
def test_stake_batch(
    web3,
    config,
    factory_router,
    consumer_wallet,
    factory_deployer_wallet,
    another_consumer_wallet,
):
    nft_factory = ERC721FactoryContract(
        web3=web3,
        address=get_address_of_type(config, ERC721FactoryContract.CONTRACT_NAME),
    )

    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(
        get_address_of_type(config, ERC721FactoryContract.CONTRACT_NAME),
        2**256 - 1,
        factory_deployer_wallet,
    )
    ocean_contract.approve(
        get_address_of_type(config, "Router"), 2**256 - 1, factory_deployer_wallet
    )

    tx = nft_factory.create_nft_erc20_with_pool(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        nft_token_uri="https://oceanprotocol.com/nft/",
        datatoken_template=1,
        datatoken_name="ERC20B1",
        datatoken_symbol="ERC20DT1Symbol",
        datatoken_minter=factory_deployer_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_address=factory_deployer_wallet.address,
        datatoken_publish_market_fee_token=ZERO_ADDRESS,
        datatoken_cap=to_wei("1000000"),
        datatoken_publish_market_fee_amount=0,
        datatoken_bytess=[b""],
        pool_rate=to_wei("2"),
        pool_base_token_decimals=ocean_contract.decimals(),
        pool_vesting_amount=to_wei("10000"),
        pool_vesting_blocks=2500000,
        pool_base_token_amount=to_wei("2"),
        pool_lp_swap_fee=to_wei("0.001"),
        pool_publish_market_swap_fee=to_wei("0.001"),
        pool_side_staking=get_address_of_type(config, "Staking"),
        pool_base_token=get_address_of_type(config, "Ocean"),
        pool_base_token_sender=get_address_of_type(
            config, ERC721FactoryContract.CONTRACT_NAME
        ),
        pool_publisher=factory_deployer_wallet.address,
        pool_publish_market_fee_collector=factory_deployer_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=factory_deployer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = nft_factory.get_event_log(
        "TokenCreated", tx_receipt.blockNumber, web3.eth.block_number, None
    )
    erc_token = registered_event[0]["args"]["newTokenAddress"]
    erc_token_contract = ERC20Token(web3=web3, address=erc_token)
    registered_event_pool = erc_token_contract.get_event_log(
        FactoryRouter.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    pool1 = registered_event_pool[0]["args"]["poolAddress"]

    tx = nft_factory.create_nft_erc20_with_pool(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        nft_token_uri="https://oceanprotocol.com/nft/",
        datatoken_template=1,
        datatoken_name="ERC20B12",
        datatoken_symbol="ERC20DT1Symbol2",
        datatoken_minter=factory_deployer_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_address=factory_deployer_wallet.address,
        datatoken_publish_market_fee_token=ZERO_ADDRESS,
        datatoken_cap=to_wei("1000000"),
        datatoken_publish_market_fee_amount=0,
        datatoken_bytess=[b""],
        pool_rate=to_wei("1"),
        pool_base_token_decimals=ocean_contract.decimals(),
        pool_vesting_amount=to_wei("10000"),
        pool_vesting_blocks=2500000,
        pool_base_token_amount=to_wei("2"),
        pool_lp_swap_fee=to_wei("0.001"),
        pool_publish_market_swap_fee=to_wei("0.001"),
        pool_side_staking=get_address_of_type(config, "Staking"),
        pool_base_token=get_address_of_type(config, "Ocean"),
        pool_base_token_sender=get_address_of_type(
            config, ERC721FactoryContract.CONTRACT_NAME
        ),
        pool_publisher=factory_deployer_wallet.address,
        pool_publish_market_fee_collector=factory_deployer_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=factory_deployer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = nft_factory.get_event_log(
        "TokenCreated", tx_receipt.blockNumber, web3.eth.block_number, None
    )
    erc_token2 = registered_event[0]["args"]["newTokenAddress"]
    erc_token_contract2 = ERC20Token(web3=web3, address=erc_token2)
    registered_event_pool = erc_token_contract2.get_event_log(
        FactoryRouter.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    pool2 = registered_event_pool[0]["args"]["poolAddress"]

    stake1 = {"poolAddress": pool1, "tokenAmountIn": to_wei("1"), "minPoolAmountOut": 0}

    stake2 = {"poolAddress": pool2, "tokenAmountIn": to_wei("1"), "minPoolAmountOut": 0}
    bpool_token1 = ERC20Token(web3, pool1)
    bpool_token2 = ERC20Token(web3, pool2)

    assert bpool_token1.balanceOf(consumer_wallet.address) == 0
    assert bpool_token2.balanceOf(consumer_wallet.address) == 0

    ocean_contract.approve(
        get_address_of_type(config, ERC721FactoryContract.CONTRACT_NAME),
        2**256 - 1,
        consumer_wallet,
    )
    ocean_contract.approve(
        get_address_of_type(config, "Router"), 2**256 - 1, consumer_wallet
    )

    balance_ocean_before = ocean_contract.balanceOf(consumer_wallet.address)
    factory_router.stake_batch([stake1, stake2], consumer_wallet)
    balance_ocean_after = ocean_contract.balanceOf(consumer_wallet.address)

    balance_dt1 = bpool_token1.balanceOf(consumer_wallet.address)
    balance_dt2 = bpool_token2.balanceOf(consumer_wallet.address)

    assert balance_ocean_after < balance_ocean_before
    assert balance_dt1 > 0
    assert balance_dt2 > 0
