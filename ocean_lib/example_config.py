#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging

from ocean_lib.config import Config

logging.basicConfig(level=logging.INFO)


class ExampleConfig:
    @staticmethod
    def _get_config():
        """
        :return: dict
        """
        return {
            "eth-network": {"network": "http://localhost:8545", "address.file": ""},
            "resources": {
                "metadata_cache_uri": "http://aquarius:5000",
                "provider.url": "http://localhost:8030",
                "provider.address": "0x068Ed00cF0441e4829D9784fCBe7b9e26D4BD8d0",
                "downloads.path": "consume-downloads",
            },
        }

    @staticmethod
    def get_config_dict(network_name=None):
        """
        :return: dict
        """
        config_dict = ExampleConfig._get_config()
        logging.debug(
            f"Configuration loaded for environment `{network_name}`: {config_dict}"
        )
        return config_dict

    @staticmethod
    def get_config(network_url=None):
        """
        :return: `Config` instance
        """
        return Config(options_dict=ExampleConfig.get_config_dict(network_url))
