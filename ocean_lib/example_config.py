#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os
from typing import Dict, Optional

from enforce_typing import enforce_types
from ocean_lib.config import Config
from ocean_lib.ocean.util import get_infura_id, get_infura_url

logging.basicConfig(level=logging.INFO)


@enforce_types
class ExampleConfig:
    @staticmethod
    def get_config_net() -> str:
        """
        :return: value of environment variable `TEST_NET` or default `ganache`
        """
        return os.environ.get("TEST_NET", "ganache")

    @staticmethod
    def get_base_config() -> Dict[str, Dict[str, str]]:
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
    def get_network_config(network_name: str) -> Dict[str, Dict[str, str]]:
        """
        :return: dict
        """
        config = ExampleConfig.get_base_config()
        config["eth-network"]["network"] = get_infura_url(get_infura_id(), network_name)
        return config

    @staticmethod
    def _get_config(
        local_node: bool = True, net_name: Optional[str] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        :return: dict
        """
        if local_node:
            return ExampleConfig.get_base_config()

        return ExampleConfig.get_network_config(net_name)

    @staticmethod
    def get_config_dict(
        network_name: Optional[str] = None,
    ) -> Dict[str, Dict[str, str]]:
        """
        :return: dict
        """
        test_net = network_name or ExampleConfig.get_config_net()
        local_node = not test_net or test_net in {"local", "ganache"}
        config_dict = ExampleConfig._get_config(local_node, test_net)
        logging.debug(
            f"Configuration loaded for environment `{network_name}`: {config_dict}"
        )
        return config_dict

    @staticmethod
    def get_config(network_name: Optional[str] = None) -> Config:
        """
        :return: `Config` instance
        """
        return Config(options_dict=ExampleConfig.get_config_dict(network_name))
