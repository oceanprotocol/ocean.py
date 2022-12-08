#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from brownie.network import accounts
from web3.main import Web3

from conftest_ganache import *
from ocean_lib.example_config import get_config_dict
from ocean_lib.ocean.util import get_address_of_type, get_ocean_token_address
from tests.resources.helper_functions import get_ganache_wallet

_NETWORK = "ganache"
HUGEINT = 2**255
BobInfo = None
AliceInfo = None


@pytest.fixture
def network():
    return _NETWORK


@pytest.fixture
def nft_factory_address(config):
    return get_address_of_type(config, "ERC721Factory")


@pytest.fixture
def OCEAN_address(config):
    return get_ocean_token_address(config.address_file)


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
def alice(alice_wallet): # alias to alice_wallet
    return alice_wallet


@pytest.fixture
def alice_ocean():
    return alice_info().ocean


@pytest.fixture
def ocean(alice_ocean): #alias for alice_ocean
    return alice_ocean


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
def bob(bob_wallet): #alias to bob_wallet
    return bob_wallet


@pytest.fixture
def bob_ocean():
    return bob_info().ocean


@pytest.fixture
def carlos(another_consumer_wallet): #alias for another_consumer wallet
    return another_consumer_wallet


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
    config = get_config_dict()

    info.private_key = os.environ.get(private_key_name)
    info.wallet = accounts.add(info.private_key)
    info.address = info.wallet.address
    wallet = get_ganache_wallet()
    if wallet:
        assert accounts.at(wallet.address).balance() >= Web3.toWei(
            "4", "ether"
        ), "Ether balance less than 4."
        if accounts.at(info.address).balance() < Web3.toWei("2", "ether"):
            wallet.transfer(info.address, "4 ether")

    from ocean_lib.ocean.ocean import Ocean

    info.ocean = Ocean(config)

    return info
