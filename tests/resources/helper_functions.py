#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import brownie
import coloredlogs
import enforce
import json
import logging
import logging.config
import os
import pathlib
import uuid
import yaml

from ocean_lib.assets.asset import Asset
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.account import Account
from ocean_lib.web3_internal.utils import get_account
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.mocks.data_provider_mock import DataProviderMock

PUBLISHER_INDEX = 1
CONSUMER_INDEX = 0


@enforce.runtime_validation
def get_resource_path(dir_name, file_name):
    base = os.path.realpath(__file__).split(os.path.sep)[1:-1]
    if dir_name:
        return pathlib.Path(os.path.join(os.path.sep, *base, dir_name, file_name))
    else:
        return pathlib.Path(os.path.join(os.path.sep, *base, file_name))


@enforce.runtime_validation
def get_publisher_wallet() -> Wallet:
    web3 = get_web3()
    key = get_publisher_account().private_key
    wallet = Wallet(web3, key)
    return wallet

@enforce.runtime_validation
def get_consumer_wallet() -> Wallet:
    web3 = get_web3()
    key = get_consumer_account().private_key
    return Wallet(web3, key)

@enforce.runtime_validation
def get_publisher_account() -> Account:
    return get_account(0)

@enforce.runtime_validation
def get_consumer_account() -> Account:
    return get_account(1)

@enforce.runtime_validation
def get_web3():
    return get_publisher_ocean_instance().web3

@enforce.runtime_validation
def get_publisher_ocean_instance(use_provider_mock=False) -> Ocean:
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(data_provider=data_provider)
    account = get_publisher_account()
    ocn.main_account = account
    return ocn

@enforce.runtime_validation
def get_consumer_ocean_instance(use_provider_mock:bool=False) -> Ocean:
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(data_provider=data_provider)
    account = get_consumer_account()
    ocn.main_account = account
    return ocn

@enforce.runtime_validation
def get_ddo_sample() -> Asset:
    return Asset(json_filename=get_resource_path('ddo', 'ddo_sa_sample.json'))

@enforce.runtime_validation
def get_sample_ddo_with_compute_service() -> dict:
    path = get_resource_path('ddo', 'ddo_with_compute_service.json')  # 'ddo_sa_sample.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)

@enforce.runtime_validation
def get_algorithm_ddo() -> dict:
    path = get_resource_path('ddo', 'ddo_algorithm.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)

@enforce.runtime_validation
def get_computing_metadata() -> dict:
    path = get_resource_path('ddo', 'computing_metadata.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)

@enforce.runtime_validation
def get_registered_ddo(ocean_instance, wallet: Wallet):
    metadata = get_metadata()
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    asset = ocean_instance.assets.create(metadata, wallet)
    return asset

@enforce.runtime_validation
def log_event(event_name: str):
    def _process_event(event):
        print(f'Received event {event_name}: {event}')
    return _process_event

@enforce.runtime_validation
def get_metadata() -> dict:
    path = get_resource_path('ddo', 'valid_metadata.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)

@enforce.runtime_validation
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

@enforce.runtime_validation
def brownieAccount(private_key: str):
    assert brownie.network.is_connected()
    return brownie.network.accounts.add(private_key=private_key)
