#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest

from ocean_lib.aquarius.aquarius import Aquarius
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.datatoken_enterprise import DatatokenEnterprise
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import from_wei, to_wei
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.utils import get_ether_balance
from tests.resources.helper_functions import (
    get_address_of_type,
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
    get_web3,
    setup_logging,
)

_NETWORK = "ganache"

setup_logging()


@pytest.fixture(autouse=True)
def setup_all(request, config, web3, ocean_token):
    # a test can skip setup_all() via decorator "@pytest.mark.nosetup_all"
    if "nosetup_all" in request.keywords:
        return

    wallet = get_ganache_wallet()

    if not wallet:
        return

    addresses_file = config.address_file
    if not os.path.exists(addresses_file):
        return

    print(f"sender: {wallet.key}, {wallet.address}, {wallet.keys_str()}")
    print(f"sender balance: {from_wei(get_ether_balance(web3, wallet.address))}")
    assert get_ether_balance(web3, wallet.address) >= to_wei(
        "10"
    ), "Ether balance less than 10."

    amt_distribute = to_wei("1000")

    for w in (get_publisher_wallet(), get_consumer_wallet()):
        if get_ether_balance(web3, w.address) < to_wei("2"):
            send_ether(wallet, w.address, to_wei("4"))

        if ocean_token.balanceOf(w.address) < to_wei("100"):
            ocean_token.transfer(w.address, amt_distribute, from_wallet=wallet)


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
def web3():
    return get_web3()


@pytest.fixture
def aquarius_instance(config):
    return Aquarius.get_instance(config.metadata_cache_uri)


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
def factory_deployer_wallet():
    return get_factory_deployer_wallet(_NETWORK)


@pytest.fixture
def ocean_address(config) -> str:
    return get_address_of_type(config, "Ocean")


@pytest.fixture
def ocean_token(web3, ocean_address) -> Datatoken:
    return Datatoken(web3, ocean_address)


@pytest.fixture
def factory_router(web3, config):
    return FactoryRouter(web3, get_address_of_type(config, "Router"))


@pytest.fixture
def side_staking(web3, config):
    return SideStaking(web3=web3, address=get_address_of_type(config, "Staking"))


@pytest.fixture
def data_nft_factory(web3, config):
    return DataNFTFactoryContract(web3, get_address_of_type(config, "ERC721Factory"))


@pytest.fixture
def provider_wallet():
    return get_provider_wallet()


@pytest.fixture
def data_nft(web3, publisher_wallet, data_nft_factory):
    tx = data_nft_factory.deploy_erc721_contract(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_datatoken_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    token_address = data_nft_factory.get_token_address(tx)
    return DataNFT(web3, token_address)


@pytest.fixture
def datatoken(web3, data_nft, publisher_wallet, data_nft_factory):
    tx_result = data_nft.create_erc20(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_result)

    registered_event = data_nft_factory.get_event_log(
        DataNFTFactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    dt_address = registered_event[0].args.newTokenAddress

    return Datatoken(web3, dt_address)


@pytest.fixture
def datatoken_enterprise_token(web3, data_nft, publisher_wallet, data_nft_factory):
    tx_result = data_nft.create_erc20(
        template_index=2,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=publisher_wallet,
        datatoken_cap=to_wei(100),
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_result)

    registered_event = data_nft_factory.get_event_log(
        DataNFTFactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    dt_address = registered_event[0].args.newTokenAddress

    return DatatokenEnterprise(web3, dt_address)


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
