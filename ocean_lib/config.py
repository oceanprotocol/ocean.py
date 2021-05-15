#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import configparser
import logging
import os
from pathlib import Path

import ocean_abis
from ocean_lib.ocean.env_constants import ENV_CONFIG_FILE
from ocean_lib.web3_internal.constants import GAS_LIMIT_DEFAULT

DEFAULT_NETWORK_HOST = "localhost"
DEFAULT_NETWORK_PORT = 8545
DEFAULT_NETWORK_URL = "http://localhost:8545"
DEFAULT_ARTIFACTS_PATH = ""
DEFAULT_ADDRESS_FILE = ""
DEFAULT_METADATA_CACHE_URI = "http://localhost:5000"
DEFAULT_PROVIDER_URL = ""
DEFAULT_TYPECHECK = "true"

NAME_NETWORK_URL = "network"
NAME_ARTIFACTS_PATH = "artifacts.path"
NAME_ADDRESS_FILE = "address.file"
NAME_GAS_LIMIT = "gas_limit"
NAME_METADATA_CACHE_URI = "metadata_cache_uri"
NAME_AQUARIUS_URL = "aquarius.url"
NAME_PROVIDER_URL = "provider.url"

NAME_DATA_TOKEN_FACTORY_ADDRESS = "dtfactory.address"
NAME_BFACTORY_ADDRESS = "bfactory.address"
NAME_OCEAN_ADDRESS = "OCEAN.address"

NAME_PROVIDER_ADDRESS = "provider.address"

NAME_TYPECHECK = "typecheck"

SECTION_ETH_NETWORK = "eth-network"
SECTION_RESOURCES = "resources"
SECTION_UTIL = "util"

environ_names_and_sections = {
    NAME_DATA_TOKEN_FACTORY_ADDRESS: [
        "DATA_TOKEN_FACTORY_ADDRESS",
        "Data token factory address",
        SECTION_ETH_NETWORK,
    ],
    NAME_BFACTORY_ADDRESS: [
        "BFACTORY_ADDRESS",
        "BPool factory address",
        SECTION_ETH_NETWORK,
    ],
    NAME_OCEAN_ADDRESS: ["OCEAN_ADDRESS", "OCEAN address", SECTION_ETH_NETWORK],
    NAME_NETWORK_URL: ["NETWORK_URL", "Network URL", SECTION_ETH_NETWORK],
    NAME_ARTIFACTS_PATH: [
        "ARTIFACTS_PATH",
        "Path to the abi artifacts of the deployed smart contracts",
        SECTION_ETH_NETWORK,
    ],
    NAME_ADDRESS_FILE: [
        "ADDRESS_FILE",
        "Path to json file of deployed contracts addresses",
        SECTION_ETH_NETWORK,
    ],
    NAME_GAS_LIMIT: ["GAS_LIMIT", "Gas limit", SECTION_ETH_NETWORK],
    NAME_METADATA_CACHE_URI: [
        "METADATA_CACHE_URI",
        "Metadata Cache URI",
        SECTION_RESOURCES,
    ],
    NAME_PROVIDER_URL: [
        "PROVIDER_URL",
        "URL of data services provider",
        SECTION_RESOURCES,
    ],
    NAME_PROVIDER_ADDRESS: [
        "PROVIDER_ADDRESS",
        "Provider ethereum address",
        SECTION_RESOURCES,
    ],
    NAME_TYPECHECK: ["TYPECHECK", "Enforce type hints at runtime", SECTION_UTIL],
}

deprecated_environ_names = {
    NAME_AQUARIUS_URL: ["AQUARIUS_URL", "Aquarius URL", SECTION_RESOURCES]
}

config_defaults = {
    "eth-network": {
        NAME_NETWORK_URL: DEFAULT_NETWORK_URL,
        NAME_ARTIFACTS_PATH: DEFAULT_ARTIFACTS_PATH,
        NAME_ADDRESS_FILE: DEFAULT_ADDRESS_FILE,
        NAME_GAS_LIMIT: GAS_LIMIT_DEFAULT,
    },
    "resources": {
        NAME_METADATA_CACHE_URI: DEFAULT_METADATA_CACHE_URI,
        NAME_PROVIDER_URL: DEFAULT_PROVIDER_URL,
        NAME_PROVIDER_ADDRESS: "",
    },
    "util": {NAME_TYPECHECK: DEFAULT_TYPECHECK},
}


class Config(configparser.ConfigParser):
    """Class to manage the ocean-lib configuration."""

    def __init__(self, filename=None, options_dict=None, **kwargs):
        """Initialize Config class.

        Options available:
        ```
        [eth-network]
        ; ethereum network url
        network = rinkeby
        ; Path of json abis, this defaults to the artifacts installed with `pip install ocean-contracts`
        artifacts.path = artifacts

        [resources]
        metadata_cache_uri = http://localhost:5000
        provider.url = http://localhost:8030

        [util]
        typecheck = true
        ```
        :param filename: Path of the config file, str.
        :param options_dict: Python dict with the config, dict.
        :param kwargs: Additional args. If you pass text, you have to pass the plain text configuration.
        """
        configparser.ConfigParser.__init__(self)

        self.read_dict(config_defaults)
        self._web3_provider = None
        self._logger = logging.getLogger("config")

        if filename:
            self._logger.debug(f"Config: loading config file {filename}")
            with open(filename) as fp:
                text = fp.read()
                self.read_string(text)
        elif "text" in kwargs:
            self._logger.debug("Config: loading config file {filename}.")
            self.read_string(kwargs["text"])
        elif options_dict:
            self._logger.debug(f"Config: loading from dict {options_dict}")
            self.read_dict(options_dict)
        else:
            filename = os.getenv(ENV_CONFIG_FILE)
            if filename is None:
                raise ValueError(f'Config file envvar "{ENV_CONFIG_FILE}" is empty')
            self._logger.debug(f"Config: loading config file {filename}")
            with open(filename) as fp:
                text = fp.read()
                self.read_string(text)
        self._handle_and_validate_metadata_cache_uri()
        self._load_environ()

    def _handle_and_validate_metadata_cache_uri(self):
        metadata_cache_uri = self.get(
            SECTION_RESOURCES, NAME_METADATA_CACHE_URI, fallback=None
        )
        aquarius_url = self.get(SECTION_RESOURCES, NAME_AQUARIUS_URL, fallback=None)

        if aquarius_url:
            self._logger.warning(
                f"Config: {SECTION_RESOURCES}.{NAME_AQUARIUS_URL} option is deprecated. "
                f"Use {SECTION_RESOURCES}.{NAME_METADATA_CACHE_URI} instead."
            )

        # Fallback to aquarius.url
        if aquarius_url and metadata_cache_uri == DEFAULT_METADATA_CACHE_URI:
            self.set(SECTION_RESOURCES, NAME_METADATA_CACHE_URI, aquarius_url)
            self.remove_option(SECTION_RESOURCES, NAME_AQUARIUS_URL)
            aquarius_url = None

        if aquarius_url and metadata_cache_uri:
            raise ValueError(
                (
                    f"Both {SECTION_RESOURCES}.{NAME_METADATA_CACHE_URI} and "
                    f"{SECTION_RESOURCES}.{NAME_AQUARIUS_URL} options are set. "
                    f"Use only {SECTION_RESOURCES}.{NAME_METADATA_CACHE_URI} because "
                    f"{SECTION_RESOURCES}.{NAME_AQUARIUS_URL} is deprecated."
                )
            )

    def _load_environ(self):
        for option_name, environ_item in environ_names_and_sections.items():
            if option_name == NAME_METADATA_CACHE_URI:
                metadata_cache_uri = os.environ.get(environ_item[0])
                aquarius_url = os.environ.get(
                    deprecated_environ_names[NAME_AQUARIUS_URL][0]
                )

                if metadata_cache_uri and aquarius_url:
                    raise ValueError(
                        (
                            "Both METADATA_CACHE_URI and AQUARIUS_URL envvars are set. "
                            "Use only METADATA_CACHE_URI because AQUARIUS_URL is deprecated."
                        )
                    )

                if aquarius_url:
                    self._logger.warning(
                        "Config: AQUARIUS_URL envvar is deprecated. Use METADATA_CACHE_URI instead."
                    )

                # fallback to AQUARIUS_URL
                value = metadata_cache_uri if metadata_cache_uri else aquarius_url
            else:
                value = os.environ.get(environ_item[0])
            if value is not None:
                self._logger.debug(f"Config: setting environ {option_name} = {value}")
                self.set(environ_item[2], option_name, value)

    @property
    def artifacts_path(self):
        """Path where the contracts artifacts are allocated."""
        _path_string = self.get(SECTION_ETH_NETWORK, NAME_ARTIFACTS_PATH)
        path = Path(_path_string).expanduser().resolve() if _path_string else None

        if path and path.exists():
            return path

        return Path(ocean_abis.__file__).parent.expanduser().resolve()

    @property
    def address_file(self):
        file_path = self.get(SECTION_ETH_NETWORK, NAME_ADDRESS_FILE)
        if file_path:
            file_path = Path(file_path).expanduser().resolve()

        if not file_path or not os.path.exists(file_path):
            file_path = os.path.join(self.artifacts_path, "address.json")

        return file_path

    @property
    def network_url(self):
        """URL of the ethereum network. (e.g.): http://mynetwork:8545."""
        return self.get(SECTION_ETH_NETWORK, NAME_NETWORK_URL)

    @property
    def gas_limit(self):
        """Ethereum gas limit."""
        return int(self.get(SECTION_ETH_NETWORK, NAME_GAS_LIMIT))

    @property
    def metadata_cache_uri(self):
        """URL of metadata cache component. (e.g.): http://myaquarius:5000."""
        return self.get(SECTION_RESOURCES, NAME_METADATA_CACHE_URI)

    @property
    def provider_url(self):
        return self.get(SECTION_RESOURCES, NAME_PROVIDER_URL)

    @property
    def provider_address(self):
        """Provider address (e.g.): 0x00bd138abd70e2f00903268f3db08f2d25677c9e.

        Ethereum address of service provider
        """
        return self.get(SECTION_RESOURCES, NAME_PROVIDER_ADDRESS)

    @property
    def downloads_path(self):
        """Path for the downloads of assets."""
        return self.get(SECTION_RESOURCES, "downloads.path")

    @property
    def typecheck(self):
        return self.get(SECTION_UTIL, NAME_TYPECHECK)
