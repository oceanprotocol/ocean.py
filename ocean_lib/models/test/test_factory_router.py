#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import Web3

from ocean_lib.config import Config
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import get_address_of_type

# Constants copied from FactoryRouter.sol, used for testing purposes
OPC_SWAP_FEE_APPROVED = to_wei("0.001")  # 0.1%
OPC_SWAP_FEE_NOT_APPROVED = to_wei("0.002")  # 0.2%
OPC_CONSUME_FEE = to_wei("0.03")  # 0.03 DT
OPC_PROVIDER_FEE = to_wei("0")  # 0%


@pytest.mark.unit
def test_properties(factory_router: FactoryRouter):
    """Tests the events' properties."""
    # Factory Router Events
    assert factory_router.event_NewPool.abi["name"] == FactoryRouter.EVENT_NEW_POOL
    # BFactory Events
    assert (
        factory_router.event_BPoolCreated.abi["name"]
        == FactoryRouter.EVENT_BPOOL_CREATED
    )
    assert (
        factory_router.event_PoolTemplateAdded.abi["name"]
        == FactoryRouter.EVENT_POOL_TEMPLATE_ADDED
    )
    assert (
        factory_router.event_PoolTemplateRemoved.abi["name"]
        == FactoryRouter.EVENT_POOL_TEMPLATE_REMOVED
    )


# BFactory methods


@pytest.mark.unit
def test_is_pool_template(config: Config, factory_router: FactoryRouter):
    assert factory_router.is_pool_template(get_address_of_type(config, "poolTemplate"))


# FactoryRouter methods


@pytest.mark.unit
def test_router_owner(factory_router: FactoryRouter):
    assert Web3.isChecksumAddress(factory_router.router_owner())


@pytest.mark.unit
def test_factory(config: Config, factory_router: FactoryRouter):
    assert factory_router.factory() == get_address_of_type(config, "ERC721Factory")


@pytest.mark.unit
def test_swap_ocean_fee(factory_router: FactoryRouter):
    assert factory_router.swap_ocean_fee() == OPC_SWAP_FEE_APPROVED


@pytest.mark.unit
def test_swap_non_ocean_fee(factory_router: FactoryRouter):
    assert factory_router.swap_non_ocean_fee() == OPC_SWAP_FEE_NOT_APPROVED


@pytest.mark.unit
def test_is_approved_token(
    config: Config, factory_router: FactoryRouter, ocean_address: str
):
    """Tests that Ocean token has been added to the mapping"""
    assert factory_router.is_approved_token(ocean_address)
    assert not (factory_router.is_approved_token(ZERO_ADDRESS))


@pytest.mark.unit
def test_is_ss_contract(config: Config, factory_router: FactoryRouter):
    """Tests if ssContract address has been added to the mapping"""
    assert factory_router.is_ss_contract(get_address_of_type(config, "Staking"))


@pytest.mark.unit
def test_is_fixed_rate_contract(config: Config, factory_router: FactoryRouter):
    """Tests that fixedRateExchange address is added to the mapping"""
    assert factory_router.is_fixed_rate_contract(
        get_address_of_type(config, "FixedPrice")
    )


@pytest.mark.unit
def test_is_dispenser_contract(config: Config, factory_router: FactoryRouter):
    assert factory_router.is_dispenser_contract(
        get_address_of_type(config, "Dispenser")
    )


@pytest.mark.unit
def test_get_opc_fee(config: Config, factory_router: FactoryRouter, ocean_address: str):
    assert factory_router.get_opc_fee(ocean_address) == OPC_SWAP_FEE_APPROVED
    assert factory_router.get_opc_fee(ZERO_ADDRESS) == OPC_SWAP_FEE_NOT_APPROVED


@pytest.mark.unit
def test_get_opc_fees(factory_router: FactoryRouter):
    assert factory_router.get_opc_fees() == [
        OPC_SWAP_FEE_APPROVED,
        OPC_SWAP_FEE_NOT_APPROVED,
    ]


@pytest.mark.unit
def test_get_opc_consume_fee(factory_router: FactoryRouter):
    assert factory_router.get_opc_consume_fee() == OPC_CONSUME_FEE


@pytest.mark.unit
def test_get_opc_provider_fee(factory_router: FactoryRouter):
    assert factory_router.get_opc_provider_fee() == OPC_PROVIDER_FEE


@pytest.mark.unit
def test_opc_collector(config: Config, factory_router: FactoryRouter):
    assert factory_router.get_opc_collector() == get_address_of_type(
        config, "OPFCommunityFeeCollector"
    )


@pytest.mark.unit
def test_buy_dt_batch(
    web3: Web3,
    config: Config,
    ocean_token: Datatoken,
    factory_router: FactoryRouter,
    consumer_wallet: Wallet,
    factory_deployer_wallet: Wallet,
    another_consumer_wallet: Wallet,
):
    """Tests that a batch of tokens is successfully bought through the buy_dt_batch function"""

    nft_factory = DataNFTFactoryContract(
        web3=web3,
        address=get_address_of_type(config, DataNFTFactoryContract.CONTRACT_NAME),
    )

    ocean_token.approve(
        get_address_of_type(config, DataNFTFactoryContract.CONTRACT_NAME),
        2**256 - 1,
        factory_deployer_wallet,
    )
    ocean_token.approve(
        get_address_of_type(config, "Router"), 2**256 - 1, factory_deployer_wallet
    )

    tx = nft_factory.create_nft_erc20_with_pool(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        nft_token_uri="https://oceanprotocol.com/nft/",
        nft_transferable=True,
        nft_owner=factory_deployer_wallet.address,
        datatoken_template=1,
        datatoken_name="DTB1",
        datatoken_symbol="DT1Symbol",
        datatoken_minter=factory_deployer_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_order_fee_address=factory_deployer_wallet.address,
        datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
        datatoken_publish_market_order_fee_amount=0,
        datatoken_bytess=[b""],
        pool_rate=to_wei("2"),
        pool_base_token_decimals=ocean_token.decimals(),
        pool_base_token_amount=to_wei("2"),
        pool_lp_swap_fee_amount=to_wei("0.001"),
        pool_publish_market_swap_fee_amount=to_wei("0.001"),
        pool_side_staking=get_address_of_type(config, "Staking"),
        pool_base_token=ocean_token.address,
        pool_base_token_sender=get_address_of_type(
            config, DataNFTFactoryContract.CONTRACT_NAME
        ),
        pool_publisher=factory_deployer_wallet.address,
        pool_publish_market_swap_fee_collector=factory_deployer_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=factory_deployer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = nft_factory.get_event_log(
        "TokenCreated", tx_receipt.blockNumber, web3.eth.block_number, None
    )
    erc_token = registered_event[0]["args"]["newTokenAddress"]
    erc_token_contract = Datatoken(web3=web3, address=erc_token)
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
        nft_transferable=True,
        nft_owner=factory_deployer_wallet.address,
        datatoken_template=1,
        datatoken_name="DTB12",
        datatoken_symbol="DT1Symbol2",
        datatoken_minter=factory_deployer_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_order_fee_address=factory_deployer_wallet.address,
        datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
        datatoken_publish_market_order_fee_amount=0,
        datatoken_bytess=[b""],
        pool_rate=to_wei("1"),
        pool_base_token_decimals=ocean_token.decimals(),
        pool_base_token_amount=to_wei("2"),
        pool_lp_swap_fee_amount=to_wei("0.001"),
        pool_publish_market_swap_fee_amount=to_wei("0.001"),
        pool_side_staking=get_address_of_type(config, "Staking"),
        pool_base_token=ocean_token.address,
        pool_base_token_sender=get_address_of_type(
            config, DataNFTFactoryContract.CONTRACT_NAME
        ),
        pool_publisher=factory_deployer_wallet.address,
        pool_publish_market_swap_fee_collector=factory_deployer_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=factory_deployer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = nft_factory.get_event_log(
        "TokenCreated", tx_receipt.blockNumber, web3.eth.block_number, None
    )
    erc_token2 = registered_event[0]["args"]["newTokenAddress"]
    erc_token_contract2 = Datatoken(web3=web3, address=erc_token2)
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
        "tokenIn": ocean_token.address,
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
        "tokenIn": ocean_token.address,
        "amountsIn": to_wei("1"),
        "tokenOut": erc_token2,
        "amountsOut": to_wei("0.1"),
        "maxPrice": to_wei("10"),
        "swapMarketFee": 0,
        "marketFeeAddress": another_consumer_wallet.address,
    }

    balance_ocean_before = ocean_token.balanceOf(factory_deployer_wallet.address)
    factory_router.buy_dt_batch([op1, op2], factory_deployer_wallet)
    balance_ocean_after = ocean_token.balanceOf(factory_deployer_wallet.address)

    balance_dt1 = erc_token_contract.balanceOf(factory_deployer_wallet.address)
    balance_dt2 = erc_token_contract2.balanceOf(factory_deployer_wallet.address)

    assert balance_ocean_after < balance_ocean_before
    assert balance_dt1 > 0
    assert balance_dt2 > 0


@pytest.mark.unit
def test_stake_batch(
    web3: Web3,
    config: Config,
    ocean_token: Datatoken,
    factory_router: FactoryRouter,
    consumer_wallet: Wallet,
    factory_deployer_wallet: Wallet,
):
    nft_factory = DataNFTFactoryContract(
        web3=web3,
        address=get_address_of_type(config, DataNFTFactoryContract.CONTRACT_NAME),
    )

    ocean_token.approve(
        get_address_of_type(config, DataNFTFactoryContract.CONTRACT_NAME),
        2**256 - 1,
        factory_deployer_wallet,
    )
    ocean_token.approve(
        get_address_of_type(config, "Router"), 2**256 - 1, factory_deployer_wallet
    )

    tx = nft_factory.create_nft_erc20_with_pool(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        nft_token_uri="https://oceanprotocol.com/nft/",
        nft_transferable=True,
        nft_owner=factory_deployer_wallet.address,
        datatoken_template=1,
        datatoken_name="DTB1",
        datatoken_symbol="DT1Symbol",
        datatoken_minter=factory_deployer_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_order_fee_address=factory_deployer_wallet.address,
        datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
        datatoken_publish_market_order_fee_amount=0,
        datatoken_bytess=[b""],
        pool_rate=to_wei("2"),
        pool_base_token_decimals=ocean_token.decimals(),
        pool_base_token_amount=to_wei("2"),
        pool_lp_swap_fee_amount=to_wei("0.001"),
        pool_publish_market_swap_fee_amount=to_wei("0.001"),
        pool_side_staking=get_address_of_type(config, "Staking"),
        pool_base_token=ocean_token.address,
        pool_base_token_sender=get_address_of_type(
            config, DataNFTFactoryContract.CONTRACT_NAME
        ),
        pool_publisher=factory_deployer_wallet.address,
        pool_publish_market_swap_fee_collector=factory_deployer_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=factory_deployer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = nft_factory.get_event_log(
        "TokenCreated", tx_receipt.blockNumber, web3.eth.block_number, None
    )
    erc_token = registered_event[0]["args"]["newTokenAddress"]
    erc_token_contract = Datatoken(web3=web3, address=erc_token)
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
        nft_transferable=True,
        nft_owner=factory_deployer_wallet.address,
        datatoken_template=1,
        datatoken_name="DTB12",
        datatoken_symbol="DT1Symbol2",
        datatoken_minter=factory_deployer_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_order_fee_address=factory_deployer_wallet.address,
        datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
        datatoken_publish_market_order_fee_amount=0,
        datatoken_bytess=[b""],
        pool_rate=to_wei("1"),
        pool_base_token_decimals=ocean_token.decimals(),
        pool_base_token_amount=to_wei("2"),
        pool_lp_swap_fee_amount=to_wei("0.001"),
        pool_publish_market_swap_fee_amount=to_wei("0.001"),
        pool_side_staking=get_address_of_type(config, "Staking"),
        pool_base_token=ocean_token.address,
        pool_base_token_sender=get_address_of_type(
            config, DataNFTFactoryContract.CONTRACT_NAME
        ),
        pool_publisher=factory_deployer_wallet.address,
        pool_publish_market_swap_fee_collector=factory_deployer_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=factory_deployer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = nft_factory.get_event_log(
        "TokenCreated", tx_receipt.blockNumber, web3.eth.block_number, None
    )
    erc_token2 = registered_event[0]["args"]["newTokenAddress"]
    erc_token_contract2 = Datatoken(web3=web3, address=erc_token2)
    registered_event_pool = erc_token_contract2.get_event_log(
        FactoryRouter.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    pool2 = registered_event_pool[0]["args"]["poolAddress"]

    stake1 = {"poolAddress": pool1, "tokenAmountIn": to_wei("1"), "minPoolAmountOut": 0}

    stake2 = {"poolAddress": pool2, "tokenAmountIn": to_wei("1"), "minPoolAmountOut": 0}
    bpool_token1 = Datatoken(web3, pool1)
    bpool_token2 = Datatoken(web3, pool2)

    assert bpool_token1.balanceOf(consumer_wallet.address) == 0
    assert bpool_token2.balanceOf(consumer_wallet.address) == 0

    ocean_token.approve(
        get_address_of_type(config, DataNFTFactoryContract.CONTRACT_NAME),
        2**256 - 1,
        consumer_wallet,
    )
    ocean_token.approve(
        get_address_of_type(config, "Router"), 2**256 - 1, consumer_wallet
    )

    balance_ocean_before = ocean_token.balanceOf(consumer_wallet.address)
    factory_router.stake_batch([stake1, stake2], consumer_wallet)
    balance_ocean_after = ocean_token.balanceOf(consumer_wallet.address)

    balance_dt1 = bpool_token1.balanceOf(consumer_wallet.address)
    balance_dt2 = bpool_token2.balanceOf(consumer_wallet.address)

    assert balance_ocean_after < balance_ocean_before
    assert balance_dt1 > 0
    assert balance_dt2 > 0
