#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import hexbytes
from web3.main import Web3
from tests.resources.helper_functions import (
    get_publisher_wallet,
    get_consumer_wallet,
    get_another_consumer_wallet,
)

import pytest

from web3 import exceptions
from ocean_lib.web3_internal.wallet import Wallet

from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.factory_router import FactoryRouter
from ocean_lib.web3_internal.contract_utils import get_contracts_addresses
from ocean_lib.models.v4.bfactory import BFactory
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import get_factory_deployer_wallet
from ocean_lib.config import Config
from ocean_lib.web3_internal.constants import ZERO_ADDRESS


import os
_NETWORK = "ganache"
_NETWORK = "ganache"


def get_factory_router_address(config):
    """Helper function to retrieve a known factory router address."""
    return get_contracts_addresses(address_file=config.address_file, network=_NETWORK)["Router"]


def init(web3, config):
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    factory_router.update_opf_fee(web3.toWei(0.001, "ether"), get_factory_deployer_wallet(network=_NETWORK))


def create_new_token(web3, config):
    tkn = ERC20Token.deploy(web3=web3, deployer_wallet=get_publisher_wallet())
    return tkn


def get_erc_address(config):
    """Helper function to retrieve a known ERC address."""
    return get_contracts_addresses(address_file=config.address_file, network=_NETWORK)["ERC20Template"]["1"]


def get_ocean_address(config):
    """Helper function to retrieve a known Ocean address."""
    return get_contracts_addresses(address_file=config.address_file, network=_NETWORK)["Ocean"]


def test_ocean_tokens_mapping(web3, config):
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    ocean_tokens = factory_router.ocean_tokens(get_ocean_address(config))
    assert ocean_tokens is True


def test_add_token(web3, config):
    newTokenAddress = ERC20Token.deploy(web3=web3, deployer_wallet=get_factory_deployer_wallet(network=_NETWORK))
    factory_router = FactoryRouter(web3, get_factory_router_address(config))

    print(get_factory_deployer_wallet(network=_NETWORK).address)
    print(factory_router.router_owner())

    assert factory_router.ocean_tokens(newTokenAddress) == False
    factory_router.add_ocean_token(newTokenAddress, get_factory_deployer_wallet(network=_NETWORK))
    assert factory_router.ocean_tokens(newTokenAddress) == True


def test_fail_add_token(web3, config):
    newTokenAddress = get_erc_address(config)
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    with pytest.raises(Exception):
        factory_router.add_ocean_token(newTokenAddress, get_another_consumer_wallet(network=_NETWORK))


def test_remove_token(web3, config):
    newTokenAddress = create_new_token(web3, config)

    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    factory_router.add_ocean_token(newTokenAddress, get_factory_deployer_wallet(network=_NETWORK))

    assert factory_router.ocean_tokens(newTokenAddress) == True
    factory_router.remove_ocean_token(newTokenAddress, get_factory_deployer_wallet(network=_NETWORK))
    assert factory_router.ocean_tokens(newTokenAddress) == False


def test_fail_remove_token(web3, config):
    newTokenAddress = create_new_token(web3, config)

    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    factory_router.add_ocean_token(newTokenAddress, get_factory_deployer_wallet(network=_NETWORK))
    assert factory_router.ocean_tokens(newTokenAddress) == True
    with pytest.raises(Exception):
        factory_router.remove_ocean_token(newTokenAddress, get_consumer_wallet())


def test_update_opf_fee(web3, config):
    init(web3, config)
    newTokenAddress = create_new_token(web3, config)
    factory_deployer = get_factory_deployer_wallet(network=_NETWORK)

    factory_router = FactoryRouter(web3, get_factory_router_address(config))

    assert factory_router.ocean_tokens(newTokenAddress) == False
    assert factory_router.get_opf_fee(newTokenAddress) == 1e15
    assert factory_router.swap_ocean_fee() == 1e15

    factory_router.update_opf_fee(web3.toWei(0.01, "ether"), factory_deployer)
    assert factory_router.ocean_tokens(newTokenAddress) == False
    assert factory_router.get_opf_fee(newTokenAddress) == 1e16
    assert factory_router.swap_ocean_fee() == 1e16


def test_fail_update_opf_fee(web3, config):
    init(web3, config)
    newTokenAddress = create_new_token(web3, config)
    factory_deployer = get_factory_deployer_wallet(network=_NETWORK)

    factory_router = FactoryRouter(web3, get_factory_router_address(config))

    assert factory_router.ocean_tokens(newTokenAddress) == False
    assert factory_router.get_opf_fee(newTokenAddress) == 1e15
    assert factory_router.swap_ocean_fee() == 1e15

    factory_router.update_opf_fee(web3.toWei(0.01, "ether"), factory_deployer)

    assert factory_router.ocean_tokens(newTokenAddress) == False
    assert factory_router.get_opf_fee(newTokenAddress) == 1e16
    assert factory_router.swap_ocean_fee() == 1e16


def test_ss_contracts(web3, config):
    userAddress = create_new_token(web3, config)

    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    assert factory_router.ss_contracts(userAddress) == False
    factory_router.add_ss_contract(userAddress, get_factory_deployer_wallet(network=_NETWORK))
    assert factory_router.ss_contracts(userAddress) == True


def test_fail_ss_contracts(web3, config):
    userAddress = create_new_token(web3, config)

    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    assert factory_router.ss_contracts(userAddress) == False
    with pytest.raises(Exception):
        factory_router.add_ss_contract(userAddress, get_another_consumer_wallet(network=_NETWORK))


def test_fail_add_factory_owner(web3, config):
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    with pytest.raises(exceptions.ContractLogicError):
        factory_router.add_factory(get_another_consumer_wallet().address, get_factory_deployer_wallet(network=_NETWORK))
    assert factory_router.factory() == get_contracts_addresses(address_file=config.address_file, network=_NETWORK)["ERC721Factory"]


def test_fail_add_factory_not_owner(web3, config):
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    with pytest.raises(exceptions.ContractLogicError):
        factory_router.add_factory(get_another_consumer_wallet().address, get_consumer_wallet())
    assert factory_router.factory() == get_contracts_addresses(address_file=config.address_file, network=_NETWORK)["ERC721Factory"]


def test_fixed_rate(web3, config):
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    fixedRateExchangeAddress = get_contracts_addresses(address_file=config.address_file, network=_NETWORK)["FixedPrice"]
    factory_router.add_fixed_rate_contract(fixedRateExchangeAddress, get_factory_deployer_wallet(network=_NETWORK))
    assert factory_router.fixed_price(fixedRateExchangeAddress) == True


def test_fail_add_fixed_rate_contract(web3, config):
    factory_router = FactoryRouter(web3, get_factory_router_address(config))

    with pytest.raises(exceptions.ContractLogicError):
        factory_router.add_fixed_rate_contract(get_another_consumer_wallet().address, get_consumer_wallet())
    assert factory_router.fixed_price(get_another_consumer_wallet().address) == False


def test_fail_add_pool_template(web3, config):
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    with pytest.raises(exceptions.ContractLogicError):
        factory_router.add_pool_template(get_another_consumer_wallet().address, get_consumer_wallet())
    assert factory_router.is_pool_template(get_another_consumer_wallet().address) == False


def test_add_pool_template(web3, config):
    user = get_consumer_wallet().address
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    factory_router.remove_pool_template(user, get_factory_deployer_wallet(network=_NETWORK))
    assert factory_router.is_pool_template(user) == False
    factory_router.add_pool_template(user, get_factory_deployer_wallet(network=_NETWORK))
    assert factory_router.is_pool_template(user) == True


def test_remove_pool_template(web3, config):
    user = get_consumer_wallet().address
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    assert factory_router.is_pool_template(user) == True
    factory_router.remove_pool_template(user, get_factory_deployer_wallet(network=_NETWORK))
    assert factory_router.is_pool_template(user) == False


def test_fail_remove_pool_template(web3, config):
    test_add_pool_template(web3, config)

    user = get_consumer_wallet().address
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    assert factory_router.is_pool_template(user) == True
    with pytest.raises(exceptions.ContractLogicError):
        factory_router.remove_pool_template(user, get_consumer_wallet())

    assert factory_router.is_pool_template(user) == True


def test_buy_dt_batch(web3: Web3, config):

    v4Addresses = get_contracts_addresses(address_file=config.address_file, network=_NETWORK)

    consumer_wallet = get_consumer_wallet()
    factory_deployer = get_factory_deployer_wallet(network=_NETWORK)

    daiAddress = v4Addresses["Ocean"]

    daiContract = ERC20Token(web3=web3, address=daiAddress)
    daiContract.allowance(factory_deployer.address, v4Addresses["ERC721Factory"])
    daiContract.approve(v4Addresses["ERC721Factory"], 2**256 - 1, factory_deployer)

    nftData = {
        "name": '72120Bundle',
        "symbol": '72Bundle',
        "templateIndex": 1,
        "baseURI": "https://oceanprotocol.com/nft/"
    }

    ercData = {
        "templateIndex": 1,
        "strings": ['ERC20B1', 'ERC20DT1Symbol'],
        "addresses": [
            factory_deployer.address,
            consumer_wallet.address,
            factory_deployer.address,
            ZERO_ADDRESS,
        ],
        "uints": [web3.toWei('1000000', "ether"), 0],
        "bytess": []
    }

    poolData = {
        "addresses": [
            v4Addresses["Staking"],
            v4Addresses["Ocean"],
            v4Addresses["ERC721Factory"],
            factory_deployer.address,
            factory_deployer.address,
            v4Addresses["poolTemplate"],
        ],
        "ssParams": [
            web3.toWei('1', "ether"),
            daiContract.decimals(),
            web3.toWei('10000', "ether"),
            2500000,
            web3.toWei('2', "ether")
        ],
        "swapFees": [
            web3.toWei('0.001', "ether"),
            web3.toWei('0.001', "ether")
        ]
    }

    nftFactory = ERC721FactoryContract(web3=web3, address=v4Addresses["ERC721Factory"])

    tx = nftFactory.create_nft_erc_with_pool(
        nftData,
        ercData,
        poolData,
        factory_deployer
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = nftFactory.get_event_log(
        'TokenCreated',
        tx_receipt.blockNumber, web3.eth.block_number, None
    )
    ercToken = registered_event[0]['args']['newTokenAddress']
    ercTokenContract = ERC20Token(web3=web3, address=ercToken)
    registered_event_pool = ercTokenContract.get_event_log(
        FactoryRouter.EVENT_NEW_POOL,
        tx_receipt.blockNumber, web3.eth.block_number, None
    )
    pool1 = registered_event_pool[0]['args']['poolAddress']

    print(pool1)
    print(ercToken)

    assert 0
