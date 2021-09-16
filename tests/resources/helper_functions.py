#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
import logging.config
import os
import time

import coloredlogs
import yaml
from enforce_typing import enforce_types
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.data_token import DataToken
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import get_web3_connection_provider
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.mocks.data_provider_mock import DataProviderMock
from web3.main import Web3


def get_web3():
    return Web3(provider=get_web3_connection_provider(get_example_config().network_url))


def get_example_config():
    return ExampleConfig.get_config()


@enforce_types
def get_publisher_wallet() -> Wallet:
    return Wallet(get_web3(), private_key=os.environ.get("TEST_PRIVATE_KEY1"))


@enforce_types
def get_consumer_wallet() -> Wallet:
    return Wallet(get_web3(), private_key=os.environ.get("TEST_PRIVATE_KEY2"))


@enforce_types
def get_another_consumer_wallet() -> Wallet:
    return Wallet(get_web3(), private_key=os.environ.get("TEST_PRIVATE_KEY3"))


def get_factory_deployer_wallet(network):
    if network == "ganache":
        return get_ganache_wallet()

    private_key = os.environ.get("FACTORY_DEPLOYER_PRIVATE_KEY")
    if not private_key:
        return None

    return Wallet(get_web3(), private_key=private_key)


def get_ganache_wallet():
    web3 = get_web3()
    if (
        web3.eth.accounts
        and web3.eth.accounts[0].lower()
        == "0xe2DD09d719Da89e5a3D0F2549c7E24566e947260".lower()
    ):
        return Wallet(
            web3,
            private_key="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58",
        )

    return None


@enforce_types
def get_publisher_ocean_instance(use_provider_mock=False) -> Ocean:
    config = ExampleConfig.get_config()
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(config, data_provider=data_provider)
    account = get_publisher_wallet()
    ocn.main_account = account
    return ocn


@enforce_types
def get_consumer_ocean_instance(use_provider_mock: bool = False) -> Ocean:
    config = ExampleConfig.get_config()
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(config, data_provider=data_provider)
    account = get_consumer_wallet()
    ocn.main_account = account
    return ocn


@enforce_types
def get_another_consumer_ocean_instance(use_provider_mock: bool = False) -> Ocean:
    config = ExampleConfig.get_config()
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(config, data_provider=data_provider)
    account = get_another_consumer_wallet()
    ocn.main_account = account
    return ocn


@enforce_types
def log_event(event_name: str):
    def _process_event(event):
        print(f"Received event {event_name}: {event}")

    return _process_event


@enforce_types
def setup_logging(
    default_path: str = "logging.yaml",
    default_level=logging.INFO,
    env_key: str = "LOG_CFG",
):
    """Logging setup."""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, "rt") as file:
            try:
                config = yaml.safe_load(file.read())
                logging.config.dictConfig(config)
                coloredlogs.install()
                logging.info(f"Logging configuration loaded from file: {path}")
            except Exception as ex:
                print(ex)
                print("Error in Logging Configuration. Using default configs")
                logging.basicConfig(level=default_level)
                coloredlogs.install(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        coloredlogs.install(level=default_level)


@enforce_types
def mint_tokens_and_wait(
    data_token_contract: DataToken,
    receiver_address: str,
    minter_wallet: Wallet,
    block_confirmations: int,
):
    dtc = data_token_contract
    tx_id = dtc.mint(receiver_address, to_wei(50), minter_wallet, block_confirmations)
    dtc.get_tx_receipt(dtc.web3, tx_id)
    time.sleep(2)

    def verify_supply(mint_amount=to_wei(50)):
        supply = dtc.contract.caller.totalSupply()
        if supply <= 0:
            _tx_id = dtc.mint(
                receiver_address, mint_amount, minter_wallet, block_confirmations
            )
            dtc.get_tx_receipt(dtc.web3, _tx_id)
            supply = dtc.contract.caller.totalSupply()
        return supply

    while True:
        try:
            s = verify_supply()
            if s > 0:
                break
        except (ValueError, Exception):
            pass
