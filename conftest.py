#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import uuid

import pytest
from ocean_lib.common.aquarius.aquarius_provider import AquariusProvider
from enforce_typing import enforce_types
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models import btoken
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.ocean.util import get_contracts_addresses, get_ocean_token_address
from ocean_lib.web3_internal.currency import from_wei, to_wei
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.utils import get_ether_balance
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import get_metadata
from tests.resources.helper_functions import (
    get_consumer_ocean_instance,
    get_consumer_wallet,
    get_example_config,
    get_ganache_wallet,
    get_publisher_ocean_instance,
    get_publisher_wallet,
    get_web3,
    setup_logging,
    get_factory_deployer_wallet,
    get_another_consumer_wallet,
)
from web3.main import Web3

_NETWORK = "ganache"
HUGEINT = 2 ** 255
BobInfo = None
AliceInfo = None

setup_logging()


@pytest.fixture(autouse=True)
def setup_all(request, config, web3):
    # a test can skip setup_all() via decorator "@pytest.mark.nosetup_all"
    if "nosetup_all" in request.keywords:
        return

    wallet = get_ganache_wallet()

    if not wallet:
        return

    addresses_file = config.address_file
    if not os.path.exists(addresses_file):
        return

    with open(addresses_file) as f:
        network_addresses = json.load(f)

    print(f"sender: {wallet.key}, {wallet.address}, {wallet.keys_str()}")
    print(f"sender balance: {from_wei(get_ether_balance(web3, wallet.address))}")
    assert get_ether_balance(web3, wallet.address) >= to_wei(
        10
    ), "Ether balance less than 10."

    from ocean_lib.models.data_token import DataToken

    OCEAN_token = DataToken(web3, address=network_addresses["development"]["Ocean"])

    amt_distribute = to_wei(1000)

    for w in (get_publisher_wallet(), get_consumer_wallet()):
        if get_ether_balance(web3, w.address) < to_wei(2):
            send_ether(wallet, w.address, to_wei(4))

        if OCEAN_token.balanceOf(w.address) < to_wei(100):
            OCEAN_token.mint(wallet.address, amt_distribute, from_wallet=wallet)
            OCEAN_token.transfer(w.address, amt_distribute, from_wallet=wallet)


@pytest.fixture
def config():
    return get_example_config()


@pytest.fixture
def publisher_ocean_instance():
    return get_publisher_ocean_instance()


@pytest.fixture
def consumer_ocean_instance():
    return get_consumer_ocean_instance()


@pytest.fixture
def publisher_wallet():
    return get_publisher_wallet()


@pytest.fixture
def consumer_wallet():
    return get_consumer_wallet()


@pytest.fixture
def another_consumer_wallet():
    return get_another_consumer_wallet()


@pytest.fixture
def factory_deployer_wallet():
    return get_factory_deployer_wallet(_NETWORK)


@pytest.fixture
def web3():
    return get_web3()


@pytest.fixture
def aquarius_instance(config):
    return AquariusProvider.get_aquarius(config.metadata_cache_uri)


@pytest.fixture
def metadata():
    metadata = get_metadata()
    metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    return metadata


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
