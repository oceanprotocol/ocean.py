#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from web3.main import Web3
from tests.resources.helper_functions import (
    get_publisher_wallet,
    get_consumer_wallet,
    get_another_consumer_wallet,
)

import pytest

from web3 import exceptions
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.factory_router import FactoryRouter
from ocean_lib.web3_internal.contract_utils import get_contracts_addresses
from ocean_lib.models.v4.erc20_token import ERC20Token
from tests.resources.helper_functions import get_factory_deployer_wallet
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

_NETWORK = "ganache"


def create_new_token(web3, config):
    erc20_token = ERC20Token.deploy(web3=web3, deployer_wallet=get_publisher_wallet())
    return erc20_token


def test_ocean_tokens_mapping(web3, config):
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    ocean_tokens = factory_router.ocean_tokens(get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Ocean"
    ])
    assert ocean_tokens is True


def test_add_token(web3, config):
    new_token_address = ERC20Token.deploy(
        web3=web3, deployer_wallet=get_factory_deployer_wallet(network=_NETWORK)
    )
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])

    assert factory_router.ocean_tokens(new_token_address) == False
    factory_router.add_ocean_token(
        new_token_address, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.ocean_tokens(new_token_address) == True


def test_fail_add_token(web3, config):
    new_token_address = get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "ERC20Template"
    ]["1"]
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    with pytest.raises(exceptions.ContractLogicError):
        factory_router.add_ocean_token(new_token_address, get_another_consumer_wallet())


def test_remove_token(web3, config):
    new_token_address = create_new_token(web3, config)

    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    factory_router.add_ocean_token(
        new_token_address, get_factory_deployer_wallet(network=_NETWORK)
    )

    assert factory_router.ocean_tokens(new_token_address) == True
    factory_router.remove_ocean_token(
        new_token_address, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.ocean_tokens(new_token_address) == False


def test_fail_remove_token(web3, config):
    new_token_address = create_new_token(web3, config)

    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    factory_router.add_ocean_token(
        new_token_address, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.ocean_tokens(new_token_address) == True
    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.remove_ocean_token(new_token_address, get_consumer_wallet())
    assert err.value.args[0] == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"


def test_update_opf_fee(web3, config):
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    factory_router.update_opf_fee(
        web3.toWei(0.001, "ether"), get_factory_deployer_wallet(network=_NETWORK)
    )

    new_token_address = create_new_token(web3, config)
    factory_deployer = get_factory_deployer_wallet(network=_NETWORK)

    assert factory_router.ocean_tokens(new_token_address) == False
    assert factory_router.get_opf_fee(new_token_address) == web3.toWei(0.001, "ether")
    assert factory_router.swap_ocean_fee() == web3.toWei(0.001, "ether")

    factory_router.update_opf_fee(web3.toWei(0.01, "ether"), factory_deployer)
    assert factory_router.ocean_tokens(new_token_address) == False
    assert factory_router.get_opf_fee(new_token_address) == web3.toWei(0.01, "ether")
    assert factory_router.swap_ocean_fee() == web3.toWei(0.01, "ether")


def test_fail_update_opf_fee(web3, config):
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    factory_router.update_opf_fee(
        web3.toWei(0.001, "ether"), get_factory_deployer_wallet(network=_NETWORK)
    )

    new_token_address = create_new_token(web3, config)
    factory_deployer = get_factory_deployer_wallet(network=_NETWORK)

    assert factory_router.ocean_tokens(new_token_address) == False
    assert factory_router.get_opf_fee(new_token_address) == web3.toWei(0.001, "ether")
    assert factory_router.swap_ocean_fee() == web3.toWei(0.001, "ether")

    factory_router.update_opf_fee(web3.toWei(0.01, "ether"), factory_deployer)

    assert factory_router.ocean_tokens(new_token_address) == False
    assert factory_router.get_opf_fee(new_token_address) == web3.toWei(0.01, "ether")
    assert factory_router.swap_ocean_fee() == web3.toWei(0.01, "ether")


def test_ss_contracts(web3, config):
    userAddress = create_new_token(web3, config)

    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    assert factory_router.ss_contracts(userAddress) == False
    factory_router.add_ss_contract(
        userAddress, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.ss_contracts(userAddress) == True


def test_fail_ss_contracts(web3, config):
    userAddress = create_new_token(web3, config)

    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    assert factory_router.ss_contracts(userAddress) == False
    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.add_ss_contract(userAddress, get_another_consumer_wallet())
    assert err.value.args[0] == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"


def test_fail_add_factory_owner(web3, config):
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.add_factory(
            get_another_consumer_wallet().address,
            get_factory_deployer_wallet(network=_NETWORK),
        )
    assert (
        factory_router.factory()
        == get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
            "ERC721Factory"
        ]
    )
    assert err.value.args[0] == "execution reverted: VM Exception while processing transaction: revert FACTORY ALREADY SET"


def test_fail_add_factory_not_owner(web3, config):
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.add_factory(
            get_another_consumer_wallet().address, get_consumer_wallet()
        )
    assert err.value.args[0] == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"
    assert (
        factory_router.factory()
        == get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
            "ERC721Factory"
        ]
    )


def test_fixed_rate(web3, config):
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    fixed_rate_exchange_address = get_contracts_addresses(
        address_file=config.address_file, network=_NETWORK
    )["FixedPrice"]
    factory_router.add_fixed_rate_contract(
        fixed_rate_exchange_address, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.fixed_price(fixed_rate_exchange_address) == True


def test_fail_add_fixed_rate_contract(web3, config):
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])

    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.add_fixed_rate_contract(
            get_another_consumer_wallet().address, get_consumer_wallet()
        )
    assert err.value.args[0] == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"
    assert factory_router.fixed_price(get_another_consumer_wallet().address) == False


def test_fail_add_pool_template(web3, config):
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.add_pool_template(
            get_another_consumer_wallet().address, get_consumer_wallet()
        )
    assert err.value.args[0] == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"
    assert (
        factory_router.is_pool_template(get_another_consumer_wallet().address) == False
    )


def test_add_pool_template(web3, config):
    user = get_consumer_wallet().address
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    factory_router.remove_pool_template(
        user, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.is_pool_template(user) == False
    factory_router.add_pool_template(
        user, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.is_pool_template(user) == True


def test_remove_pool_template(web3, config):
    user = get_consumer_wallet().address
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    assert factory_router.is_pool_template(user) == True
    factory_router.remove_pool_template(
        user, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.is_pool_template(user) == False


def test_fail_remove_pool_template(web3, config):
    user = get_consumer_wallet().address
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])

    factory_router.add_pool_template(
        user, get_factory_deployer_wallet(network=_NETWORK)
    )
    assert factory_router.is_pool_template(user) == True

    with pytest.raises(exceptions.ContractLogicError) as err:
        factory_router.remove_pool_template(user, get_consumer_wallet())

    assert err.value.args[0] == "execution reverted: VM Exception while processing transaction: revert OceanRouter: NOT OWNER"
    assert factory_router.is_pool_template(user) == True


def test_buy_dt_batch(web3: Web3, config):
    factory_router = FactoryRouter(web3, get_contracts_addresses(address_file=config.address_file, network=_NETWORK)[
        "Router"
    ])
    v4_addresses = get_contracts_addresses(
        address_file=config.address_file, network=_NETWORK
    )
    nft_factory = ERC721FactoryContract(web3=web3, address=v4_addresses["ERC721Factory"])

    consumer_wallet = get_consumer_wallet()
    factory_deployer = get_factory_deployer_wallet(network=_NETWORK)

    ocean_contract = ERC20Token(web3=web3, address=v4_addresses["Ocean"])
    ocean_contract.approve(v4_addresses["ERC721Factory"], 2 ** 256 - 1, factory_deployer)
    ocean_contract.approve(v4_addresses["Router"], 2 ** 256 - 1, factory_deployer)

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
            v4_addresses["Staking"],
            v4_addresses["Ocean"],
            v4_addresses["ERC721Factory"],
            factory_deployer.address,
            factory_deployer.address,
            v4_addresses["poolTemplate"],
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
            v4_addresses["Staking"],
            v4_addresses["Ocean"],
            v4_addresses["ERC721Factory"],
            factory_deployer.address,
            factory_deployer.address,
            v4_addresses["poolTemplate"],
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
        "exchangeIds": Web3.keccak(0x00),
        "source": pool1,
        "operation": 0,
        "tokenIn": v4_addresses["Ocean"],
        "amountsIn": web3.toWei("1", "ether"),
        "tokenOut": erc_token,
        "amountsOut": web3.toWei("0.1", "ether"),
        "maxPrice": web3.toWei("10", "ether"),
    }

    op2 = {
        "exchangeIds": Web3.keccak(0x00),
        "source": pool2,
        "operation": 0,
        "tokenIn": v4_addresses["Ocean"],
        "amountsIn": web3.toWei("1", "ether"),
        "tokenOut": erc_token2,
        "amountsOut": web3.toWei("0.1", "ether"),
        "maxPrice": web3.toWei("10", "ether"),
    }
    erc_token_contract.approve(
        v4_addresses["ERC721Factory"], 2 ** 256 - 1, factory_deployer
    )
    erc_token_contract2.approve(
        v4_addresses["ERC721Factory"], 2 ** 256 - 1, factory_deployer
    )

    balance_ocean_before = ocean_contract.balanceOf(factory_deployer.address)
    factory_router.buy_dt_batch([op1, op2], factory_deployer)
    balance_ocean_after = ocean_contract.balanceOf(factory_deployer.address)

    balance_dt1 = erc_token_contract.balanceOf(factory_deployer.address)
    balance_dt2 = erc_token_contract2.balanceOf(factory_deployer.address)

    assert balance_ocean_after < balance_ocean_before
    assert balance_dt1 > 0
    assert balance_dt2 > 0
