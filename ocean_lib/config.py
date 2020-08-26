#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import configparser
import logging
import os
import site
from pathlib import Path

from ocean_lib.web3_internal.constants import GAS_LIMIT_DEFAULT

DEFAULT_NETWORK_HOST = 'localhost'
DEFAULT_NETWORK_PORT = 8545
DEFAULT_NETWORK_URL = 'http://localhost:8545'
DEFAULT_ARTIFACTS_PATH = 'artifacts'
DEFAULT_ADDRESS_FILE = 'addresses.json'
DEFAULT_NAME_AQUARIUS_URL = 'http://localhost:5000'
DEFAULT_STORAGE_PATH = 'ocean_lib.db'

NAME_NETWORK_URL = 'network'
NAME_ARTIFACTS_PATH = 'artifacts.path'
NAME_ADDRESS_FILE = 'address.file'
NAME_GAS_LIMIT = 'gas_limit'
NAME_AQUARIUS_URL = 'aquarius.url'
NAME_STORAGE_PATH = 'storage.path'
NAME_AUTH_TOKEN_MESSAGE = 'auth_token_message'
NAME_AUTH_TOKEN_EXPIRATION = 'auth_token_expiration'

NAME_DATA_TOKEN_FACTORY_ADDRESS = 'dtfactory.address'
NAME_BFACTORY_ADDRESS = 'bfactory.address'
NAME_OCEAN_ADDRESS = 'OCEAN.address'

NAME_PARITY_URL = 'parity.url'
NAME_PROVIDER_ADDRESS = 'provider.address'


environ_names = {
    NAME_DATA_TOKEN_FACTORY_ADDRESS: ['DATA_TOKEN_FACTORY_ADDRESS', 'Data token factory address'],
    NAME_BFACTORY_ADDRESS: ['BFACTORY_ADDRESS', 'BPool factory address'],
    NAME_OCEAN_ADDRESS: ['OCEAN_ADDRESS', 'OCEAN address'],
    NAME_NETWORK_URL: ['NETWORK_URL', 'Network URL'],
    NAME_ARTIFACTS_PATH: ['ARTIFACTS_PATH', 'Path to the abi artifacts of the deployed smart contracts'],
    NAME_ADDRESS_FILE: ['ADDRESS_FILE', 'Path to json file of deployed contracts addresses'],
    NAME_GAS_LIMIT: ['GAS_LIMIT', 'Gas limit'],
    NAME_AQUARIUS_URL: ['AQUARIUS_URL', 'Aquarius URL'],
    NAME_STORAGE_PATH: ['STORAGE_PATH', 'Path to the local database file'],
    NAME_AUTH_TOKEN_MESSAGE: ['AUTH_TOKEN_MESSAGE',
                              'Message to use for generating user auth token'],
    NAME_AUTH_TOKEN_EXPIRATION: ['AUTH_TOKEN_EXPIRATION',
                                 'Auth token expiration time expressed in seconds'],
    NAME_PARITY_URL: ['PARITY_URL', 'Parity URL'],
    NAME_PROVIDER_ADDRESS: ['PROVIDER_ADDRESS', 'Provider (Brizo) ethereum address']
}

config_defaults = {
    'eth-network': {
        NAME_NETWORK_URL: DEFAULT_NETWORK_URL,
        NAME_ARTIFACTS_PATH: DEFAULT_ARTIFACTS_PATH,
        NAME_ADDRESS_FILE: DEFAULT_ADDRESS_FILE,
        NAME_GAS_LIMIT: GAS_LIMIT_DEFAULT,
        NAME_PARITY_URL: '',
        NAME_PROVIDER_ADDRESS: '',
    },
    'resources': {
        NAME_AQUARIUS_URL: DEFAULT_NAME_AQUARIUS_URL,
        NAME_STORAGE_PATH: DEFAULT_STORAGE_PATH,
        NAME_AUTH_TOKEN_MESSAGE: '',
        NAME_AUTH_TOKEN_EXPIRATION: ''
    }
}


class Config(configparser.ConfigParser):
    """Class to manage the ocean-lib configuration."""

    def __init__(self, filename=None, options_dict=None, **kwargs):
        """
        Initialize Config class.

        Options available:

        [eth-network]
        network = http://localhost:8545                            # ethereum network url.
        artifacts.path = artifacts                                       # Path of json abis.
        parity.url = http://localhost:8545                            # Parity client url.
        [resources]
        aquarius.url = http://localhost:5000                          # Aquarius url.
        brizo.url = http://localhost:8030                             # Brizo url.
        storage.path = ocean_lib.db                                    # Path of sla back-up storage.

        :param filename: Path of the config file, str.
        :param options_dict: Python dict with the config, dict.
        :param kwargs: Additional args. If you pass text, you have to pass the plain text
        configuration.
        """
        configparser.ConfigParser.__init__(self)

        self.read_dict(config_defaults)
        self._web3_provider = None
        self._section_name = 'eth-network'
        self._logger = logging.getLogger('config')

        if filename:
            self._logger.debug(f'Config: loading config file {filename}')
            with open(filename) as fp:
                text = fp.read()
                self.read_string(text)
        else:
            if 'text' in kwargs:
                self.read_string(kwargs['text'])

        if options_dict:
            self._logger.debug(f'Config: loading from dict {options_dict}')
            self.read_dict(options_dict)

        self._load_environ()

    def _load_environ(self):
        for option_name, environ_item in environ_names.items():
            value = os.environ.get(environ_item[0])
            if value is not None:
                self._logger.debug(f'Config: setting environ {option_name} = {value}')
                self.set(self._section_name, option_name, value)

    @property
    def artifacts_path(self):
        """Path where the contracts artifacts are allocated."""
        path = None
        _path_string = self.get(self._section_name, NAME_ARTIFACTS_PATH)
        if _path_string:
            path = Path(_path_string).expanduser().resolve()

        # TODO: Handle the default case and make default empty string
        # assert path.exists(), "Can't find the keeper path: {} ({})"..format(_path_string,
        # path)
        if path and os.path.exists(path):
            return path

        if os.getenv('VIRTUAL_ENV'):
            path = os.path.join(os.getenv('VIRTUAL_ENV'), 'artifacts')
        else:
            path = os.path.join(site.PREFIXES[0], 'artifacts')

        return path

    @property
    def address_file(self):
        file_path = self.get(self._section_name, NAME_ADDRESS_FILE)
        if file_path:
            file_path = Path(file_path).expanduser().resolve()

        if not file_path or not os.path.exists(file_path):
            return None

        return file_path

    @property
    def storage_path(self):
        """Path to local storage (database file)."""
        return self.get('resources', NAME_STORAGE_PATH)

    @property
    def network_url(self):
        """URL of the ethereum network. (e.g.): http://mynetwork:8545."""
        return self.get(self._section_name, NAME_NETWORK_URL)

    @property
    def gas_limit(self):
        """Ethereum gas limit."""
        return int(self.get(self._section_name, NAME_GAS_LIMIT))

    @property
    def aquarius_url(self):
        """URL of aquarius component. (e.g.): http://myaquarius:5000."""
        return self.get('resources', NAME_AQUARIUS_URL)

    @property
    def metadata_store_url(self):
        return self.get('resources', NAME_AQUARIUS_URL)

    @property
    def parity_url(self):
        """URL of parity client. (e.g.): http://myparity:8545."""
        return self.get(self._section_name, NAME_PARITY_URL)

    @property
    def provider_address(self):
        """Provider address. (e.g.): 0x00bd138abd70e2f00903268f3db08f2d25677c9e.
        ethereum address of service provider (Brizo)
        """
        return self.get('resources', NAME_PROVIDER_ADDRESS)

    @property
    def dtfactory_address(self):
        return self.get('eth-network', NAME_DATA_TOKEN_FACTORY_ADDRESS,
                        fallback=None)

    @property
    def bfactory_address(self):
        return self.get('eth-network', NAME_BFACTORY_ADDRESS, fallback=None)

    @property
    def ocean_token_address(self):
        return self.get('eth-network', NAME_OCEAN_ADDRESS, fallback=None)

    @property
    def downloads_path(self):
        """Path for the downloads of assets."""
        return self.get('resources', 'downloads.path')

    @property
    def auth_token_message(self):
        return self.get('resources', NAME_AUTH_TOKEN_MESSAGE)

    @property
    def auth_token_expiration(self):
        return self.get('resources', NAME_AUTH_TOKEN_EXPIRATION)

    @property
    def web3_provider(self):
        """Web3 provider"""
        return self._web3_provider

    @web3_provider.setter
    def web3_provider(self, web3_provider):
        self._web3_provider = web3_provider
