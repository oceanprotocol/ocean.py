#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest

from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.ocean.util import get_ocean_token_address
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.utils import get_ether_balance
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import get_ganache_wallet, get_web3

_NETWORK = "ganache"
HUGEINT = 2**255
BobInfo = None
AliceInfo = None


@pytest.fixture
def network():
    return _NETWORK


@pytest.fixture
def nft_factory_address(config):
    return DataNFTFactoryContract.configured_address(_NETWORK, config.address_file)


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
            "4"
        ), "Ether balance less than 4."
        if get_ether_balance(web3, info.address) < to_wei("2"):
            send_ether(wallet, info.address, to_wei("4"))

    from ocean_lib.ocean.ocean import Ocean

    info.ocean = Ocean(config)

    return info
