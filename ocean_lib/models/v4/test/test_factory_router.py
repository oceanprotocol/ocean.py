#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.factory_router import FactoryRouter
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import (
    get_address_of_type,
    get_another_consumer_wallet,
    get_consumer_wallet,
    get_factory_deployer_wallet,
    get_publisher_wallet,
)

_NETWORK = "ganache"


def create_new_token(web3, config):
    erc20_token = ERC20Token.deploy(web3=web3, deployer_wallet=get_publisher_wallet())
    return erc20_token


def test_properties(web3, config, factory_router):
    """Tests the events' properties."""
    assert factory_router.event_NewPool.abi["name"] == FactoryRouter.EVENT_NEW_POOL


def test_ocean_tokens_mapping(web3, config, factory_router):
    """Tests that Ocean token has been added to the mapping"""
    ocean_tokens = factory_router.ocean_tokens(get_address_of_type(config, "Ocean"))
    assert ocean_tokens is True


def test_add_token(web3, config, factory_router):
    """Tests adding a new token address to the mapping if Router Owner"""
    new_token_address = ERC20Token.deploy(
        web3=web3, deployer_wallet=get_factory_deployer_wallet(network=_NETWORK)
    )

    assert factory_router.ocean_tokens(new_token_address) == False
    factory_router.add_ocean_token(
        new_token_address, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.ocean_tokens(new_token_address) == True


def test_fail_add_token(web3, config, factory_router):
    """Tests that if it fails to add a new token address to the mapping if NOT Router Owner"""
    new_token_address = get_address_of_type(config, ERC20Token.CONTRACT_NAME)
    with pytest.raises(exceptions.ContractLogicError):
        factory_router.add_ocean_token(new_token_address, get_another_consumer_wallet())


def test_remove_token(web3, config, factory_router):
    """should remove a token previously added if Router Owner, check OPF fee updates properly"""
    new_token_address = create_new_token(web3, config)
    assert factory_router.get_opf_fee(new_token_address) == web3.toWei(0.001, "ether")

    factory_router.add_ocean_token(
        new_token_address, get_factory_deployer_wallet(network=_NETWORK)
    )

    assert factory_router.get_opf_fee(new_token_address) == 0

    assert factory_router.ocean_tokens(new_token_address) == True
    factory_router.remove_ocean_token(
        new_token_address, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.ocean_tokens(new_token_address) == False
    assert factory_router.get_opf_fee(new_token_address) == web3.toWei(0.001, "ether")


def test_fail_remove_token(web3, config, factory_router):
    """Tests that if it fails to remove a token address to the mapping if NOT Router Owner"""
    new_token_address = create_new_token(web3, config)

    factory_router.add_ocean_token(
        new_token_address, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.ocean_tokens(new_token_address) == True
    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.remove_ocean_token(new_token_address, get_consumer_wallet())
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"
    )


def test_update_opf_fee(web3, config, factory_router, factory_deployer):
    """Tests if owner can update the opf fee"""

    factory_router.update_opf_fee(web3.toWei(0.001, "ether"), factory_deployer)

    new_token_address = create_new_token(web3, config)

    assert factory_router.ocean_tokens(new_token_address) == False
    assert factory_router.get_opf_fee(new_token_address) == web3.toWei(0.001, "ether")
    assert factory_router.swap_ocean_fee() == web3.toWei(0.001, "ether")

    factory_router.update_opf_fee(web3.toWei(0.01, "ether"), factory_deployer)

    assert factory_router.ocean_tokens(new_token_address) == False
    assert factory_router.get_opf_fee(new_token_address) == web3.toWei(0.01, "ether")
    assert factory_router.swap_ocean_fee() == web3.toWei(0.01, "ether")


def test_fail_update_opf_fee(
    web3, config, factory_router, consumer_wallet, factory_deployer
):
    """Tests that if it fails to update the opf fee if NOT Router Owner"""

    factory_router.update_opf_fee(web3.toWei(0.001, "ether"), factory_deployer)

    new_token_address = create_new_token(web3, config)

    assert factory_router.ocean_tokens(new_token_address) == False
    assert factory_router.get_opf_fee(new_token_address) == web3.toWei(0.001, "ether")
    assert factory_router.swap_ocean_fee() == web3.toWei(0.001, "ether")

    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.update_opf_fee(web3.toWei(0.01, "ether"), consumer_wallet)

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"
    )

    assert factory_router.ocean_tokens(new_token_address) == False
    assert factory_router.get_opf_fee(new_token_address) == web3.toWei(0.001, "ether")
    assert factory_router.swap_ocean_fee() == web3.toWei(0.001, "ether")


def test_mapping_ss_contracts(web3, config, factory_router):
    """Confirms if ssContract address has been added to the mapping"""
    assert factory_router.ss_contracts(get_address_of_type(config, "Staking")) == True


def test_add_ss_contracts(web3, config, factory_router):
    """Tests adding a new ssContract address to the mapping if Router owner"""
    user_address = create_new_token(web3, config)

    assert factory_router.ss_contracts(user_address) == False
    factory_router.add_ss_contract(
        user_address, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.ss_contracts(user_address) == True


def test_fail_ss_contracts(web3, config, factory_router):
    """Tests that if it fails to add a new ssContract address to the mapping if NOT Router Owner"""
    user_address = create_new_token(web3, config)

    assert factory_router.ss_contracts(user_address) == False
    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.add_ss_contract(user_address, get_another_consumer_wallet())
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"
    )


def test_fail_add_factory_owner(
    web3, config, factory_router, another_consumer_wallet, factory_deployer
):
    """Tests that if it fails to add a new factory address to the mapping EVEN if Router Owner"""

    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.add_factory(
            another_consumer_wallet.address,
            factory_deployer,
        )
    assert factory_router.factory() == get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert FACTORY ALREADY SET"
    )


def test_fail_add_factory_not_owner(
    web3, config, factory_router, another_consumer_wallet, consumer_wallet
):
    """Tests that if it fails to add a new factory address to the mapping if NOT Router Owner"""

    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.add_factory(another_consumer_wallet.address, consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"
    )
    assert factory_router.factory() == get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )


def test_fixed_rate_mapping(web3, config, factory_router):
    """Confirm that fixedRateExchange address is added to the mapping"""
    assert factory_router.fixed_price(get_address_of_type(config, "FixedPrice")) == True


def test_fixed_rate(web3, config, factory_router, factory_deployer):
    """Tests that fixedRateExchange is added if Router owner"""

    fixed_rate_exchange_address = get_address_of_type(config, "FixedPrice")

    factory_router.add_fixed_rate_contract(
        fixed_rate_exchange_address, factory_deployer
    )
    assert factory_router.fixed_price(fixed_rate_exchange_address) == True


def test_fail_add_fixed_rate_contract(
    web3, config, factory_router, another_consumer_wallet, consumer_wallet
):
    """Tests that if it fails to add a new fixedRateExchange address if NOT Router Owner"""

    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.add_fixed_rate_contract(
            another_consumer_wallet.address, consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"
    )
    assert factory_router.fixed_price(another_consumer_wallet.address) == False


def test_fail_add_pool_template(
    web3, config, factory_router, another_consumer_wallet, consumer_wallet
):
    """Tests that if it fails to add a new poolTemplate if NOT Router Owner"""

    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.add_pool_template(
            another_consumer_wallet.address, consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"
    )
    assert factory_router.is_pool_template(another_consumer_wallet.address) == False


def test_add_pool_template(web3, config, factory_router):  # TODO CONTINUE
    """Tests that poolTemplate is added if Router owner"""
    consumer = get_consumer_wallet().address

    factory_router.remove_pool_template(
        consumer, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.is_pool_template(consumer) == False
    factory_router.add_pool_template(
        consumer, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.is_pool_template(consumer) == True


def test_remove_pool_template(web3, config, factory_router):
    """Tests that poolTemplate is removed if Router owner"""
    consumer = get_consumer_wallet().address

    assert factory_router.is_pool_template(consumer) == True
    factory_router.remove_pool_template(
        consumer, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.is_pool_template(consumer) == False


def test_fail_remove_pool_template(web3, config, factory_router):
    """Tests that if it fails to remove a poolTemplate if NOT Router Owner"""
    consumer = get_consumer_wallet().address

    factory_router.add_pool_template(
        consumer, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.is_pool_template(consumer) == True

    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.remove_pool_template(consumer, get_consumer_wallet())

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"
    )
    assert factory_router.is_pool_template(consumer) == True


def test_buy_dt_batch(web3, config, factory_router):
    """Tests that a batch of tokens is successfully bought through the buy_dt_batch function"""

    nft_factory = ERC721FactoryContract(
        web3=web3,
        address=get_address_of_type(config, ERC721FactoryContract.CONTRACT_NAME),
    )

    consumer_wallet = get_consumer_wallet()
    factory_deployer = get_factory_deployer_wallet(network=_NETWORK)

    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(
        get_address_of_type(config, ERC721FactoryContract.CONTRACT_NAME),
        2 ** 256 - 1,
        factory_deployer,
    )
    ocean_contract.approve(
        get_address_of_type(config, "Router"), 2 ** 256 - 1, factory_deployer
    )

    nft_data = {
        "name": "72120Bundle",
        "symbol": "72Bundle",
        "templateIndex": 1,
        "baseURI": "https://oceanprotocol.com/nft/",
    }

    erc_data = {
        "templateIndex": 1,
        "strings": ["ERC20B1", "ERC20DT1Symbol"],
        "addresses": [
            factory_deployer.address,
            consumer_wallet.address,
            factory_deployer.address,
            ZERO_ADDRESS,
        ],
        "uints": [web3.toWei("1000000", "ether"), 0],
        "bytess": [],
    }

    pool_data = {
        "addresses": [
            get_address_of_type(config, "Staking"),
            get_address_of_type(config, "Ocean"),
            get_address_of_type(config, ERC721FactoryContract.CONTRACT_NAME),
            factory_deployer.address,
            factory_deployer.address,
            get_address_of_type(config, "poolTemplate"),
        ],
        "ssParams": [
            web3.toWei("1", "ether"),
            ocean_contract.decimals(),
            web3.toWei("10000", "ether"),
            2500000,
            web3.toWei("2", "ether"),
        ],
        "swapFees": [web3.toWei("0.001", "ether"), web3.toWei("0.001", "ether")],
    }

    tx = nft_factory.create_nft_erc_with_pool(
        nft_data, erc_data, pool_data, factory_deployer
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
        "baseURI": "https://oceanprotocol.com/nft2/",
    }

    erc_data2 = {
        "templateIndex": 1,
        "strings": ["ERC20B12", "ERC20DT1Symbol2"],
        "addresses": [
            factory_deployer.address,
            consumer_wallet.address,
            factory_deployer.address,
            ZERO_ADDRESS,
        ],
        "uints": [web3.toWei("1000000", "ether"), 0],
        "bytess": [],
    }

    pool_data2 = {
        "addresses": [
            get_address_of_type(config, "Staking"),
            get_address_of_type(config, "Ocean"),
            get_address_of_type(config, ERC721FactoryContract.CONTRACT_NAME),
            factory_deployer.address,
            factory_deployer.address,
            get_address_of_type(config, "poolTemplate"),
        ],
        "ssParams": [
            web3.toWei("1", "ether"),
            ocean_contract.decimals(),
            web3.toWei("10000", "ether"),
            2500000,
            web3.toWei("2", "ether"),
        ],
        "swapFees": [web3.toWei("0.001", "ether"), web3.toWei("0.001", "ether")],
    }

    tx = nft_factory.create_nft_erc_with_pool(
        nft_data2, erc_data2, pool_data2, factory_deployer
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
        "amountsIn": web3.toWei("1", "ether"),
        "tokenOut": erc_token,
        "amountsOut": web3.toWei("0.1", "ether"),
        "maxPrice": web3.toWei("10", "ether"),
    }

    op2 = {
        "exchangeIds": web3.keccak(0x00),
        "source": pool2,
        "operation": 0,
        "tokenIn": get_address_of_type(config, "Ocean"),
        "amountsIn": web3.toWei("1", "ether"),
        "tokenOut": erc_token2,
        "amountsOut": web3.toWei("0.1", "ether"),
        "maxPrice": web3.toWei("10", "ether"),
    }

    balance_ocean_before = ocean_contract.balanceOf(factory_deployer.address)
    factory_router.buy_dt_batch([op1, op2], factory_deployer)
    balance_ocean_after = ocean_contract.balanceOf(factory_deployer.address)

    balance_dt1 = erc_token_contract.balanceOf(factory_deployer.address)
    balance_dt2 = erc_token_contract2.balanceOf(factory_deployer.address)

    assert balance_ocean_after < balance_ocean_before
    assert balance_dt1 > 0
    assert balance_dt2 > 0
