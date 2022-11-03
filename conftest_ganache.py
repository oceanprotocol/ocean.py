#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from brownie.network import accounts

from ocean_lib.aquarius.aquarius import Aquarius
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.datatoken_enterprise import DatatokenEnterprise
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.contract_utils import get_addresses_with_fallback
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.utils import connect_to_network
from tests.resources.helper_functions import (
    get_another_consumer_wallet,
    get_consumer_ocean_instance,
    get_consumer_wallet,
    get_example_config,
    get_factory_deployer_wallet,
    get_file1,
    get_file2,
    get_file3,
    get_ganache_wallet,
    get_provider_wallet,
    get_publisher_ocean_instance,
    get_publisher_wallet,
    get_wallet,
    setup_logging,
)

_NETWORK = "ganache"

setup_logging()


@pytest.fixture(autouse=True)
def setup_all(request, config, ocean_token):
    connect_to_network("development")
    accounts.clear()

    # a test can skip setup_all() via decorator "@pytest.mark.nosetup_all"
    if "nosetup_all" in request.keywords:
        return

    wallet = get_ganache_wallet()

    if not wallet:
        return

    if not get_addresses_with_fallback(config):
        print("Can not find adddresses.")
        return

    assert accounts.at(wallet.address).balance() >= to_wei(
        "10"
    ), "Ether balance less than 10."

    amt_distribute = to_wei("1000")
    ocean_token.mint(wallet.address, to_wei("20000"), {"from": wallet})

    for w in (get_publisher_wallet(), get_consumer_wallet()):
        if accounts.at(w.address).balance() < to_wei("2"):
            send_ether(config, wallet, w.address, "4 ether")

        if ocean_token.balanceOf(w.address) < to_wei("100"):
            ocean_token.mint(w.address, amt_distribute, {"from": wallet})


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
def aquarius_instance(config):
    return Aquarius.get_instance(config.get("METADATA_CACHE_URI"))


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
def publish_market_wallet():
    return get_wallet(4)


@pytest.fixture
def consume_market_wallet():
    return get_wallet(5)


@pytest.fixture
def factory_deployer_wallet(config):
    return get_factory_deployer_wallet(config)


@pytest.fixture
def ocean_address(config) -> str:
    return get_address_of_type(config, "Ocean")


@pytest.fixture
def ocean_token(config, ocean_address) -> Datatoken:
    connect_to_network("development")
    return Datatoken(config, ocean_address)


@pytest.fixture
def factory_router(config):
    return FactoryRouter(config, get_address_of_type(config, "Router"))


@pytest.fixture
def side_staking(config):
    return SideStaking(config=config, address=get_address_of_type(config, "Staking"))


@pytest.fixture
def data_nft_factory(config):
    return DataNFTFactoryContract(config, get_address_of_type(config, "ERC721Factory"))


@pytest.fixture
def provider_wallet():
    return get_provider_wallet()


@pytest.fixture
def data_nft(config, publisher_wallet, data_nft_factory):
    receipt = data_nft_factory.deployERC721Contract(
        "NFT",
        "NFTSYMBOL",
        1,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        True,
        publisher_wallet.address,
        {"from": publisher_wallet},
    )
    token_address = data_nft_factory.get_token_address(receipt)
    return DataNFT(config, token_address)


@pytest.fixture
def datatoken(config, data_nft, publisher_wallet, data_nft_factory):
    receipt = data_nft.create_erc20(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        transaction_parameters={"from": publisher_wallet},
    )

    dt_address = receipt.events["TokenCreated"]["newTokenAddress"]

    return Datatoken(config, dt_address)


@pytest.fixture
def datatoken_enterprise_token(config, data_nft, publisher_wallet, data_nft_factory):
    receipt = data_nft.create_erc20(
        template_index=2,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        transaction_parameters={"from": publisher_wallet},
        datatoken_cap=to_wei(100),
    )

    dt_address = receipt.events["TokenCreated"]["newTokenAddress"]

    return DatatokenEnterprise(config, dt_address)


@pytest.fixture
def publisher_addr():
    return get_publisher_wallet().address


@pytest.fixture
def consumer_addr():
    return get_consumer_wallet().address


@pytest.fixture
def another_consumer_addr():
    return get_another_consumer_wallet().address


@pytest.fixture
def file1():
    return get_file1()


@pytest.fixture
def file2():
    return get_file2()


@pytest.fixture
def file3():
    return get_file3()
