#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import get_address_of_type


def test_properties(factory_router):
    """Tests the events' properties."""
    assert factory_router.event_NewPool.abi["name"] == FactoryRouter.EVENT_NEW_POOL


def test_is_ocean_token_mapping(config, factory_router):
    """Tests that Ocean token has been added to the mapping"""
    is_ocean_token = factory_router.is_ocean_token(get_address_of_type(config, "Ocean"))
    assert is_ocean_token is True


def test_mapping_ss_contracts(config, factory_router):
    """Tests if ssContract address has been added to the mapping"""
    assert factory_router.is_ss_contract(get_address_of_type(config, "Staking")) is True


def test_fixed_rate_mapping(config, factory_router):
    """Tests that fixedRateExchange address is added to the mapping"""
    assert (
        factory_router.is_fixed_rate_contract(get_address_of_type(config, "FixedPrice"))
        is True
    )


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

    nft_data = {
        "name": "72120Bundle",
        "symbol": "72Bundle",
        "templateIndex": 1,
        "tokenURI": "https://oceanprotocol.com/nft/",
    }

    erc_data = {
        "templateIndex": 1,
        "strings": ["ERC20B1", "ERC20DT1Symbol"],
        "addresses": [
            factory_deployer_wallet.address,
            consumer_wallet.address,
            factory_deployer_wallet.address,
            ZERO_ADDRESS,
        ],
        "uints": [to_wei("1000000"), 0],
        "bytess": [],
    }

    pool_data = {
        "addresses": [
            get_address_of_type(config, "Staking"),
            get_address_of_type(config, "Ocean"),
            get_address_of_type(config, ERC721FactoryContract.CONTRACT_NAME),
            factory_deployer_wallet.address,
            factory_deployer_wallet.address,
            get_address_of_type(config, "poolTemplate"),
        ],
        "ssParams": [
            to_wei("2"),
            ocean_contract.decimals(),
            to_wei("10000"),
            2500000,
            to_wei("2"),
        ],
        "swapFees": [to_wei("0.001"), to_wei("0.001")],
    }

    tx = nft_factory.create_nft_erc_with_pool(
        nft_data, erc_data, pool_data, factory_deployer_wallet
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

    nft_data2 = {
        "name": "72120Bundle",
        "symbol": "72Bundle",
        "templateIndex": 1,
        "tokenURI": "https://oceanprotocol.com/nft2/",
    }

    erc_data2 = {
        "templateIndex": 1,
        "strings": ["ERC20B12", "ERC20DT1Symbol2"],
        "addresses": [
            factory_deployer_wallet.address,
            consumer_wallet.address,
            factory_deployer_wallet.address,
            ZERO_ADDRESS,
        ],
        "uints": [to_wei("1000000"), 0],
        "bytess": [],
    }

    pool_data2 = {
        "addresses": [
            get_address_of_type(config, "Staking"),
            get_address_of_type(config, "Ocean"),
            get_address_of_type(config, ERC721FactoryContract.CONTRACT_NAME),
            factory_deployer_wallet.address,
            factory_deployer_wallet.address,
            get_address_of_type(config, "poolTemplate"),
        ],
        "ssParams": [
            to_wei("1"),
            ocean_contract.decimals(),
            to_wei("10000"),
            2500000,
            to_wei("2"),
        ],
        "swapFees": [to_wei("0.001"), to_wei("0.001")],
    }

    tx = nft_factory.create_nft_erc_with_pool(
        nft_data2, erc_data2, pool_data2, factory_deployer_wallet
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
