#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging
import os
import sys

from ocean_lib.config import Config
from ocean_lib.ocean.util import get_infura_url, WEB3_INFURA_PROJECT_ID

logging.basicConfig(level=logging.INFO)


def get_variable_value(variable):
    if os.getenv(variable) is None:
        logging.error(f'you should provide a {variable}')
        sys.exit(1)
    else:
        return os.getenv(variable)


class ExampleConfig:

    @staticmethod
    def get_config_net():
        return os.environ.get('TEST_NET', 'ganache')

    @staticmethod
    def get_base_config():
        return {
            "eth-network": {
                "network": "http://localhost:8545",
                "artifacts.path": "artifacts",
                "address.file": "artifacts/addresses.json"
            },
            "resources": {
                "aquarius.url": "http://aquarius:5000",
                "provider.url": "http://localhost:8030",
                "provider.address": '0x068Ed00cF0441e4829D9784fCBe7b9e26D4BD8d0',
                "storage.path": "ocean_lib.db",
                "downloads.path": "consume-downloads"
            }
        }

    @staticmethod
    def get_rinkeby_config():
        return {
            "eth-network": {
                "network": get_infura_url(WEB3_INFURA_PROJECT_ID, 'rinkeby'),
                "artifacts.path": "artifacts",
                "dtfactory.address": "0xB9d406D24B310A7D821D0b782a36909e8c925471"

            },
            "resources": {
                "aquarius.url": "http://aquarius:5000",
                # "aquarius.url": "https://aquarius.marketplace.dev-ocean.com",
                "provider.url": "http://localhost:8030",
                "provider.address": '0x068Ed00cF0441e4829D9784fCBe7b9e26D4BD8d0',
                "storage.path": "ocean_lib.db",
                "downloads.path": "consume-downloads"
            }
        }

    @staticmethod
    def _get_config(local_node=True, net_name=None):
        if local_node:
            return ExampleConfig.get_base_config()

        return ExampleConfig.get_rinkeby_config()

    @staticmethod
    def get_config_dict():
        test_net = ExampleConfig.get_config_net()
        local_node = not test_net or test_net in {'local', 'ganache'}
        config_dict = ExampleConfig._get_config(local_node, test_net)
        return config_dict

    @staticmethod
    def get_config(network=None):
        logging.debug("Configuration loaded for environment '{}'"
                      .format(network or ExampleConfig.get_config_net()))
        return Config(options_dict=ExampleConfig.get_config_dict())
