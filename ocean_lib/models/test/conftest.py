#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from enforce_typing import enforce_types
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models import btoken
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.ocean.util import get_ocean_token_address
from ocean_lib.web3_internal.contract_utils import get_contracts_addresses
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.utils import get_ether_balance
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import (
    get_factory_deployer_wallet,
    get_ganache_wallet,
    get_web3,
)
from web3.main import Web3

_NETWORK = "ganache"
HUGEINT = 2 ** 255
BobInfo = None
AliceInfo = None


@pytest.fixture
def network():
    return _NETWORK


@pytest.fixture
def dtfactory_address(config):
    return DTFactory.configured_address(_NETWORK, config.address_file)


@pytest.fixture
def bfactory_address(config):
    return BFactory.configured_address(_NETWORK, config.address_file)


@pytest.fixture
def contracts_addresses(config):
    return get_contracts_addresses(_NETWORK, config.address_file)


@pytest.fixture
def OCEAN_address(config):
    return get_ocean_token_address(config.address_file, _NETWORK)


@pytest.fixture
def alice_private_key():
    return alice_info().private_key


@pytest.fixture
def alice_address():
    return alice_info().address


@pytest.fixture
def alice_wallet():
    return alice_info().wallet


@pytest.fixture
def alice_ocean():
    return alice_info().ocean


@pytest.fixture
def bob_private_key():
    return bob_info().private_key


@pytest.fixture
def bob_address():
    return bob_info().address


@pytest.fixture
def bob_wallet():
    return bob_info().wallet


@pytest.fixture
def bob_ocean():
    return bob_info().ocean


@pytest.fixture
def T1():  # 'TOK1' with 1000.0 held by Alice
    return alice_info().T1


@pytest.fixture
def T2():  # 'TOK2' with 1000.0 held by Alice
    return alice_info().T2


def alice_info():
    global AliceInfo
    if AliceInfo is None:
        AliceInfo = make_info("Alice", "TEST_PRIVATE_KEY1")
    return AliceInfo


def bob_info():
    global BobInfo
    if BobInfo is None:
        BobInfo = make_info("Bob", "TEST_PRIVATE_KEY2")
    return BobInfo


def make_info(name, private_key_name):
    # assume that this account has ETH with gas.
    class _Info:
        pass

    info = _Info()
    web3 = get_web3()
    config = ExampleConfig.get_config()

    info.web3 = web3

    info.private_key = os.environ.get(private_key_name)
    info.wallet = Wallet(
        web3,
        private_key=info.private_key,
        block_confirmations=config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )
    info.address = info.wallet.address
    wallet = get_ganache_wallet()
    if wallet:
        assert get_ether_balance(web3, wallet.address) >= to_wei(
            4
        ), "Ether balance less than 4."
        if get_ether_balance(web3, info.address) < to_wei(2):
            send_ether(wallet, info.address, to_wei(4))

    from ocean_lib.ocean.ocean import Ocean

    info.ocean = Ocean(config)
    info.T1 = _deployAndMintToken(web3, "TOK1", info.address)
    info.T2 = _deployAndMintToken(web3, "TOK2", info.address)

    return info


@enforce_types
def _deployAndMintToken(web3: Web3, symbol: str, to_address: str) -> btoken.BToken:
    wallet = get_factory_deployer_wallet(_NETWORK)
    dt_address = DataToken.deploy(
        web3,
        wallet,
        "Template Contract",
        "TEMPLATE",
        wallet.address,
        to_wei(1000),
        DTFactory.FIRST_BLOB,
        to_address,
    )
    dt_factory = DTFactory(web3, DTFactory.deploy(web3, wallet, dt_address, to_address))
    token_address = dt_factory.get_token_address(
        dt_factory.createToken(symbol, symbol, symbol, DataToken.DEFAULT_CAP, wallet)
    )
    token = DataToken(web3, token_address)
    token.mint(to_address, to_wei(1000), wallet)

    return btoken.BToken(web3, token.address)
