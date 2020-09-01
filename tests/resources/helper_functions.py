#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import coloredlogs

import json
import logging
import logging.config
import os
import pathlib
import time
import uuid
import yaml
from ocean_utils.agreements.service_factory import ServiceDescriptor

from ocean_lib.assets.asset import Asset
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.data_token import DataToken
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.web3_provider import Web3Provider

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.mocks.data_provider_mock import DataProviderMock


def get_resource_path(dir_name, file_name):
    base = os.path.realpath(__file__).split(os.path.sep)[1:-1]
    if dir_name:
        return pathlib.Path(os.path.join(os.path.sep, *base, dir_name, file_name))
    else:
        return pathlib.Path(os.path.join(os.path.sep, *base, file_name))


def get_web3():
    return Web3Provider.get_web3()


def get_publisher_wallet() -> Wallet:
    return Wallet(get_web3(), private_key=os.environ.get('TEST_PRIVATE_KEY1'))


def get_consumer_wallet() -> Wallet:
    return Wallet(get_web3(), private_key=os.environ.get('TEST_PRIVATE_KEY2'))


def get_factory_deployer_wallet(network):
    if network == 'ganache':
        return get_ganache_wallet()

    private_key = os.environ.get('FACTORY_DEPLOYER_PRIVATE_KEY')
    if not private_key:
        return None

    return Wallet(get_web3(), private_key=private_key)


def get_ganache_wallet():
    web3 = get_web3()
    if web3.eth.accounts and web3.eth.accounts[0].lower() == '0xe2DD09d719Da89e5a3D0F2549c7E24566e947260'.lower():
        return Wallet(web3, private_key='0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58')

    return None


def get_publisher_ocean_instance(use_provider_mock=False) -> Ocean:
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(data_provider=data_provider)
    account = get_publisher_wallet()
    ocn.main_account = account
    return ocn


def get_consumer_ocean_instance(use_provider_mock:bool=False) -> Ocean:
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(data_provider=data_provider)
    account = get_consumer_wallet()
    ocn.main_account = account
    return ocn


def get_ddo_sample() -> Asset:
    return Asset(json_filename=get_resource_path('ddo', 'ddo_sa_sample.json'))


def get_sample_ddo_with_compute_service() -> dict:
    path = get_resource_path('ddo', 'ddo_with_compute_service.json')  # 'ddo_sa_sample.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


def get_algorithm_ddo() -> dict:
    path = get_resource_path('ddo', 'ddo_algorithm.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


def get_computing_metadata() -> dict:
    path = get_resource_path('ddo', 'computing_metadata.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


def get_registered_ddo(ocean_instance, wallet: Wallet):
    metadata = get_metadata()
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    ServiceDescriptor.access_service_descriptor(
        ocean_instance.assets._build_access_service(
            metadata,
            to_base_18(1),
            wallet
        ),
        DataServiceProvider.get_download_endpoint(ocean_instance.config)
    )

    asset = ocean_instance.assets.create(metadata, wallet)
    return asset


def log_event(event_name: str):
    def _process_event(event):
        print(f'Received event {event_name}: {event}')
    return _process_event


def get_metadata() -> dict:
    path = get_resource_path('ddo', 'valid_metadata.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


def setup_logging(default_path:str='logging.yaml', default_level=logging.INFO, env_key:str='LOG_CFG'):
    """Logging setup."""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as file:
            try:
                config = yaml.safe_load(file.read())
                logging.config.dictConfig(config)
                coloredlogs.install()
                logging.info(f'Logging configuration loaded from file: {path}')
            except Exception as ex:
                print(ex)
                print('Error in Logging Configuration. Using default configs')
                logging.basicConfig(level=default_level)
                coloredlogs.install(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        coloredlogs.install(level=default_level)


def mint_tokens_and_wait(data_token_contract: DataToken, receiver_address: str, minter_wallet: Wallet):
    dtc = data_token_contract
    tx_id = dtc.mint_tokens(receiver_address, 50, minter_wallet)
    dtc.get_tx_receipt(tx_id)
    time.sleep(2)

    def verify_supply(mint_amount=50):
        supply = dtc.contract_concise.totalSupply()
        if supply <= 0:
            _tx_id = dtc.mint_tokens(receiver_address, mint_amount, minter_wallet)
            dtc.get_tx_receipt(_tx_id)
            supply = dtc.contract_concise.totalSupply()
        return supply

    while True:
        try:
            s = verify_supply()
            if s > 0:
                break
        except (ValueError, Exception):
            pass
