"""Ocean module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging
import os

import eth_account
from squid_py.web3_stuff.contract_handler import ContractHandler
from squid_py.web3_stuff.utils import get_account
from squid_py.web3_stuff.web3_provider import Web3Provider
from squid_py import Config

from squid_py.data_provider.data_service_provider import DataServiceProvider
from squid_py.config_provider import ConfigProvider
from squid_py.models.datatoken import DataToken
from squid_py.models.factory import FactoryContract
from squid_py.ocean.ocean_assets import OceanAssets
from squid_py.ocean.ocean_auth import OceanAuth
from squid_py.ocean.ocean_compute import OceanCompute
from squid_py.ocean.ocean_services import OceanServices
from squid_py.ocean.util import GANACHE_URL, get_infura_url, WEB3_INFURA_PROJECT_ID, get_web3_provider

CONFIG_FILE_ENVIRONMENT_NAME = 'CONFIG_FILE'

logger = logging.getLogger('ocean')


class Ocean:
    """The Ocean class is the entry point into Ocean Protocol."""

    def __init__(self, config=None, data_provider=None):
        """
        Initialize Ocean class.
           >> # Make a new Ocean instance
           >> ocean = Ocean({...})

        This class provides the main top-level functions in ocean protocol:
         * Publish assets metadata and associated services
            * Each asset is assigned a unique DID and a DID Document (DDO)
            * The DDO contains the asset's services including the metadata
            * The DID is registered on-chain with a URL of the metadata store
              to retrieve the DDO from

            >> ddo = ocean.assets.create(metadata, publisher_account)

         * Discover/Search assets via the current configured metadata store (Aquarius)
            >> assets_list = ocean.assets.search('search text')

         * Purchase asset services by choosing a service agreement from the
           asset's DDO. Purchase goes through the service agreements interface
           and starts by signing a service agreement then sending the signature
           to the publisher's Brizo server via the `purchaseEndpoint` in the service
           definition:

           >> service_def_id = ddo.get_service(ServiceTypes.ASSET_ACCESS).service_definition_id
           >> service_agreement_id = ocean.assets.order(did, service_def_id, consumer_account)

        An instance of Ocean is parameterized by a `Config` instance.

        :param config: Config instance
        """
        # Configuration information for the market is stored in the Config class
        # config = Config(filename=config_file, options_dict=config_dict)
        if not config:
            config = ConfigProvider.get_config()

        if isinstance(config, dict):

            private_key = config.get('privateKey', None)
            if private_key:
                account = eth_account.Account.privateKeyToAccount(private_key)
                os.environ['PARITY_KEY'] = private_key
                os.environ['PARITY_ADDRESS'] = account.address

            network = config['network']
            if network == 'ganache':
                network_url = GANACHE_URL
            elif not network.startswith('http'):
                network_url = get_infura_url(WEB3_INFURA_PROJECT_ID, network)
            else:
                network_url = network

            rinkeby_url = get_infura_url(WEB3_INFURA_PROJECT_ID, 'rinkeby')
            print(f'rinkeby url: {rinkeby_url}')

            config_dict = {
                'eth-network': {
                    'network': network_url,
                    'factory.address': config.get('factory.address')
                },
                'resources': {
                    'aquarius.url': config.get('aquarius.url')
                }
            }
            config = Config(options_dict=config_dict)
            ConfigProvider.set_config(config)

        self._config = config
        self._web3 = Web3Provider.get_web3(provider=get_web3_provider(self._config.network_url))
        ContractHandler.set_artifacts_path(self._config.artifacts_path)

        if not data_provider:
            data_provider = DataServiceProvider
        self.assets = OceanAssets(
            self._config,
            data_provider
        )
        self.services = OceanServices()
        self.auth = OceanAuth(self._config.storage_path)
        self.compute = OceanCompute(
            self.auth,
            self._config,
            data_provider
        )

        logger.debug('Squid Ocean instance initialized: ')

    @property
    def config(self):
        return self._config

    def create_data_token(self, blob, account):
        return FactoryContract(self._config.factory_address).create_data_token(account, blob)

    @staticmethod
    def get_data_token(token_address):
        return DataToken(token_address)
